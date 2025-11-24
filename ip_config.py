#!/usr/bin/env python3

import yaml
import os
import sys
import subprocess
from pathlib import Path

class NetplanConfigurator:
    def __init__(self, config_path="/etc/netplan/"):
        self.config_path = Path(config_path)
        self.config_file = self.config_path / "01-netcfg.yaml"
    
    def check_root(self):
        """Ensure script is run with sudo"""
        if os.geteuid() != 0:
            print("❌ This script must be run with sudo privileges")
            sys.exit(1)
    
    def load_config(self):
        """Load existing netplan configuration"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f)
        return {'network': {'version': 2, 'ethernets': {}}}
    
    def save_config(self, config):
        """Save configuration to YAML file"""
        with open(self.config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        print(f"✓ Configuration saved to {self.config_file}")
    
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
        print("\n" + "="*50)
        print("📡 Netplan Static IP Configuration")
        print("="*50)
        
        # Get available interfaces
        interfaces = self.get_interfaces()
        if not interfaces:
            print("❌ No network interfaces found")
            sys.exit(1)
        
        print("\n📌 Available interfaces:")
        for i, iface in enumerate(interfaces, 1):
            print(f"  {i}. {iface}")
        
        # Select interface
        while True:
            try:
                choice = int(input("\nSelect interface number: ")) - 1
                if 0 <= choice < len(interfaces):
                    interface = interfaces[choice]
                    break
                print("❌ Invalid selection")
            except ValueError:
                print("❌ Please enter a number")
        
        # Get IP address
        while True:
            ip_input = input("\nEnter static IP address (e.g., 192.168.1.100): ").strip()
            if self.validate_ip(ip_input):
                break
            print("❌ Invalid IP address format")
        
        # Get subnet mask
        while True:
            try:
                prefix = int(input("Enter subnet prefix (e.g., 24 for /24 or 255.255.255.0): "))
                if 1 <= prefix <= 32:
                    break
                print("❌ Prefix must be between 1 and 32")
            except ValueError:
                print("❌ Please enter a valid number")
        
        # Get gateway
        while True:
            gateway = input("Enter gateway IP address (e.g., 192.168.1.1): ").strip()
            if self.validate_ip(gateway):
                break
            print("❌ Invalid gateway IP address")
        
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
    
    def configure(self, config_data):
        """Apply configuration to netplan YAML"""
        config = self.load_config()
        
        interface = config_data['interface']
        ip_with_prefix = config_data['ip']
        gateway = config_data['gateway']
        dns_servers = config_data['dns']
        
        # Build interface configuration
        interface_config = {
            'dhcp4': False,
            'addresses': [ip_with_prefix],
            'gateway4': gateway,
            'nameservers': {
                'addresses': dns_servers
            }
        }
        
        # Update or create interface configuration
        if 'ethernets' not in config['network']:
            config['network']['ethernets'] = {}
        
        config['network']['ethernets'][interface] = interface_config
        
        return config
    
    def apply_config(self):
        """Apply netplan configuration"""
        print("\n⏳ Applying netplan configuration...")
        try:
            result = subprocess.run(['netplan', 'apply'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print("✓ Configuration applied successfully!")
                return True
            else:
                print(f"❌ Error applying configuration: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            print("❌ Configuration application timed out")
            return False
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return False
    
    def display_config(self, config):
        """Display the configuration that will be applied"""
        print("\n" + "="*50)
        print("📋 Configuration Preview:")
        print("="*50)
        print(yaml.dump(config, default_flow_style=False))
    
    def run(self):
        """Main execution flow"""
        self.check_root()
        
        # Get user input
        config_data = self.get_user_input()
        
        # Build configuration
        config = self.configure(config_data)
        
        # Display preview
        self.display_config(config)
        
        # Confirm before applying
        confirm = input("\n⚠️  Apply this configuration? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("❌ Configuration cancelled")
            sys.exit(0)
        
        # Save configuration
        self.save_config(config)
        
        # Apply configuration
        if self.apply_config():
            print("\n✓ Static IP configuration completed!")
            print(f"✓ Your new IP: {config_data['ip'].split('/')[0]}")
            print(f"✓ Gateway: {config_data['gateway']}")
            print(f"✓ DNS: {', '.join(config_data['dns'])}")
        else:
            print("⚠️  Configuration saved but failed to apply")

#if __name__ == "__main__":
 #   configurator = NetplanConfigurator()
  #  configurator.run()
