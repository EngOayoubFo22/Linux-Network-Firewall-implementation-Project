#!/usr/bin/env python3

import json
import os
import sys
import subprocess
from pathlib import Path


class NetplanConfigurator:
    def __init__(self, config_path="/etc/network-tool"):
        # Path for OUR JSON storage (for persistence module)
        self.config_path = Path(config_path)
        self.config_file = self.config_path / "network_config.json"

        # JSON file added by Mohammad Maher, for persistence matters.
        # YAML file is still exist as Netplan only deals with YAML files.
        self.netplan_yaml_file = Path("/etc/netplan/01-netcfg.yaml")
        # WHY: netplan apply reads from /etc/netplan/*.yaml files
        # We need to write to THIS file, not just save JSON

    def check_root(self):
        """Ensure script is run with sudo"""
        if os.geteuid() != 0:
            print("⚠ This script must be run with sudo privileges")
            sys.exit(1)

    def load_config(self):
        """
        Load from REAL netplan YAML, not our JSON file
        This reads the actual netplan configuration that's currently active
        on the system, so we can see what's really configured.
        """
        import yaml

        if self.netplan_yaml_file.exists():
            try:
                with open(self.netplan_yaml_file, 'r') as f:
                    config = yaml.safe_load(f)

                    # Ensure proper structure
                    if config is None:
                        config = {}
                    if 'network' not in config:
                        config['network'] = {}
                    if 'version' not in config['network']:
                        config['network']['version'] = 2
                    if 'ethernets' not in config['network']:
                        config['network']['ethernets'] = {}

                    return config
            except Exception as e:
                print(f"⚠️ Warning: Could not load netplan YAML: {e}")
                return {'network': {'version': 2, 'ethernets': {}}}

        return {'network': {'version': 2, 'ethernets': {}}}

    def save_config(self, config):
        """
        Save to BOTH places:
        1. Our JSON file (for persistence tracking)
        2. Real netplan YAML file (so netplan apply actually works)
        """
        import yaml

        # Create our config directory if needed
        self.config_path.mkdir(parents=True, exist_ok=True)

        # 1. Save to our JSON file (for tracking)
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
            print(f"✓ Configuration saved to {self.config_file}")
        except Exception as e:
            print(f"⚠️ Warning: Could not save JSON: {e}")

        # 2. Save to REAL netplan YAML file
        try:
            with open(self.netplan_yaml_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            print(f"✓ Netplan YAML written to {self.netplan_yaml_file}")
        except Exception as e:
            print(f"⚠️ Error: Could not write netplan YAML: {e}")
            print(f"   Your configuration may not persist!")

    def get_interfaces(self):
        """Get available network interfaces"""
        result = subprocess.run(['ip', 'link', 'show'], capture_output=True, text=True)
        interfaces = []
        for line in result.stdout.split('\n'):
            if ':' in line and not line.startswith(' '):
                interface = line.split(':')[1].strip()
                if interface not in ['lo']:  # Exclude loopback
                    interfaces.append(interface)
        return interfaces

    def validate_ip(self, ip):
        """Validate IP address format"""
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        try:
            return all(0 <= int(part) <= 255 for part in parts)
        except ValueError:
            return False

    def get_user_input(self):
        """Interactive user input for network configuration"""
        print("\n" + "=" * 50)
        print("📡 Netplan Static IP Configuration")
        print("=" * 50)

        # Get available interfaces
        interfaces = self.get_interfaces()
        if not interfaces:
            print("⚠ No network interfaces found")
            sys.exit(1)

        print("\n🔌 Available interfaces:")
        for i, iface in enumerate(interfaces, 1):
            print(f"  {i}. {iface}")

        # Select interface
        while True:
            try:
                choice = int(input("\nSelect interface number: ")) - 1
                if 0 <= choice < len(interfaces):
                    interface = interfaces[choice]
                    break
                print("⚠ Invalid selection")
            except ValueError:
                print("⚠ Please enter a number")

        # Get IP address
        while True:
            ip_input = input("\nEnter static IP address (e.g., 192.168.1.100): ").strip()
            if self.validate_ip(ip_input):
                break
            print("⚠ Invalid IP address format")

        # Get subnet mask
        while True:
            try:
                prefix = int(input("Enter subnet prefix (e.g., 24 for /24 or 255.255.255.0): "))
                if 1 <= prefix <= 32:
                    break
                print("⚠ Prefix must be between 1 and 32")
            except ValueError:
                print("⚠ Please enter a valid number")

        # Get gateway
        while True:
            gateway = input("Enter gateway IP address (e.g., 192.168.1.1): ").strip()
            if self.validate_ip(gateway):
                break
            print("⚠ Invalid gateway IP address")

        # Get DNS servers
        dns_input = input("\nEnter DNS servers (comma-separated, e.g., 8.8.8.8,8.8.4.4): ").strip()
        dns_servers = [dns.strip() for dns in dns_input.split(',') if dns.strip()]

        if not dns_servers:
            dns_servers = ['8.8.8.8', '8.8.4.4']

        return {
            'interface': interface,
            'ip': f"{ip_input}/{prefix}",
            'gateway': gateway,
            'dns': dns_servers
        }

    def configure_dhcp(self, interface):
        """
        Build a netplan configuration that enables DHCP (dynamic IP)
        on the given interface, removing any static IPv4 settings.
        """
        config = self.load_config()

        # Ensure base structure
        if 'network' not in config:
            config['network'] = {'version': 2, 'ethernets': {}}
        if 'ethernets' not in config['network']:
            config['network']['ethernets'] = {}

        # Get existing interface config or start a new one
        iface_cfg = config['network']['ethernets'].get(interface, {})

        # Remove static IPv4 settings if present
        for key in ['addresses', 'gateway4', 'nameservers', 'routes']:
            iface_cfg.pop(key, None)

        # Enable DHCP for IPv4
        iface_cfg['dhcp4'] = True

        # Put it back into the config
        config['network']['ethernets'][interface] = iface_cfg

        return config

    def configure_static(self, config_data):
        config = self.load_config()
        interface = config_data['interface']
        ip_with_prefix = config_data['ip']
        gateway = config_data['gateway']
        dns_servers = config_data['dns']

        # Build interface configuration with NEW syntax
        interface_config = {
            'dhcp4': False,
            'addresses': [ip_with_prefix],
            'routes': [  # ✅ NEW: Use routes instead of gateway4
                {
                    'to': 'default',
                    'via': gateway
                }
            ],
            'nameservers': {
                'addresses': dns_servers
            }
        }

        # Ensure structure exists
        if 'network' not in config:
            config['network'] = {'version': 2, 'ethernets': {}}
        if 'ethernets' not in config['network']:
            config['network']['ethernets'] = {}

        # Update or create interface configuration
        config['network']['ethernets'][interface] = interface_config

        return config

    def apply_config(self):
        """Apply netplan configuration"""
        print("\n⏳ Applying netplan configuration...")
        try:
            result = subprocess.run(['netplan', 'apply'],
                                    capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print("✓ Configuration applied successfully!")
                return True
            else:
                print(f"⚠ Error applying configuration: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            print("⚠ Configuration application timed out")
            return False
        except Exception as e:
            print(f"⚠ Error: {str(e)}")
            return False

    def display_config(self, config):
        """Display the configuration that will be applied"""
        print("\n" + "=" * 50)
        print("📋 Configuration Preview:")
        print("=" * 50)
        print(json.dumps(config, indent=4))

    def run(self):
        """Main execution flow"""
        self.check_root()

        # Get user input
        config_data = self.get_user_input()

        # Build configuration
        config = self.configure_static(config_data)

        # Display preview
        self.display_config(config)

        # Confirm before applying
        confirm = input("\n⚠️  Apply this configuration? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("⚠ Configuration cancelled")
            sys.exit(0)

        # ✅ Save configuration (now saves to BOTH JSON and YAML)
        self.save_config(config)

        # Apply configuration
        if self.apply_config():
            print("\n✓ Static IP configuration completed!")
            print(f"✓ Your new IP: {config_data['ip'].split('/')[0]}")
            print(f"✓ Gateway: {config_data['gateway']}")
            print(f"✓ DNS: {', '.join(config_data['dns'])}")
        else:
            print("⚠️  Configuration saved but failed to apply")