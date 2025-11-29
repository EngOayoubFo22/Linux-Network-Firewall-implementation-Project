#!/usr/bin/env python3

# Network Configuration Persistence Manager
# This module handles saving and loading network configurations


import json
import os
import subprocess
from datetime import datetime
from pathlib import Path


class NetworkConfigManager:
    """
    Manages saving and loading network configurations.
    Stores data in JSON format for easy reading and writing.
    """

    def __init__(self, config_dir="/etc/network-tool"):
        """
        Initialize the configuration manager.

        Args:
            config_dir: Directory where configuration files are stored
                       (default: /etc/network-tool)
        """
        # Where we'll save our configuration files
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "network_config.json"
        self.backup_dir = self.config_dir / "backups"

        # Create directories if they don't exist
        self._ensure_directories()

    def _ensure_directories(self):
        """
        Create configuration and backup directories if they don't exist.
        This prevents errors when trying to save files.
        """
        try:
            # Create main config directory
            self.config_dir.mkdir(parents=True, exist_ok=True)
            # Create backup directory
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            print(f"✓ Configuration directory ready: {self.config_dir}")
        except PermissionError:
            print(f"✗ Error: Need root/sudo permission to create {self.config_dir}")
            raise

    def save_configuration(self, config_data):
        """
        Save network configuration to a JSON file.

        Args:
            config_data: Dictionary containing network settings
                        Example: {
                            'interfaces': {...},
                            'firewall_rules': [...],
                            'timestamp': '2025-01-15 10:30:00'
                        }

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Add timestamp to know when this config was saved
            config_data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            config_data['version'] = "1.0"

            # Create backup of existing config before overwriting
            if self.config_file.exists():
                self._create_backup()

            # Write configuration to file
            # indent=4 makes the JSON file human-readable
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=4)

            print(f"✓ Configuration saved successfully to {self.config_file}")
            return True

        except Exception as e:
            print(f"✗ Error saving configuration: {e}")
            return False

    def load_configuration(self):
        """
        Load network configuration from JSON file.

        Returns:
            dict: Configuration data, or None if file doesn't exist or error occurs
        """
        try:
            # Check if configuration file exists
            if not self.config_file.exists():
                print(f"ℹ No existing configuration found at {self.config_file}")
                return None

            # Read and parse JSON file
            with open(self.config_file, 'r') as f:
                config_data = json.load(f)

            print(f"✓ Configuration loaded successfully from {self.config_file}")
            print(f"  Last saved: {config_data.get('timestamp', 'Unknown')}")
            return config_data

        except json.JSONDecodeError as e:
            print(f"✗ Error: Configuration file is corrupted: {e}")
            return None
        except Exception as e:
            print(f"✗ Error loading configuration: {e}")
            return None

    def _create_backup(self):
        """
        Create a backup of the current configuration file.
        Backups are timestamped so you can restore from any point.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"network_config_{timestamp}.json"

        try:
            # Copy current config to backup location
            import shutil
            shutil.copy2(self.config_file, backup_file)
            print(f"✓ Backup created: {backup_file}")
        except Exception as e:
            print(f"⚠ Warning: Could not create backup: {e}")

    def apply_network_configuration(self, config_data):
        """
        Apply loaded configuration to the system.
        This restores network settings after a reboot.

        Args:
            config_data: Dictionary with network configuration

        Returns:
            bool: True if successful, False otherwise
        """
        if not config_data:
            print("✗ No configuration data to apply")
            return False

        success = True

        # Apply interface configurations
        if 'interfaces' in config_data:
            print("\n→ Applying network interface configurations...")
            for interface, settings in config_data['interfaces'].items():
                if not self._apply_interface_config(interface, settings):
                    success = False

        # Apply firewall rules
        if 'firewall_rules' in config_data:
            print("\n→ Applying firewall rules...")
            if not self._apply_firewall_rules(config_data['firewall_rules']):
                success = False

        return success

    def _apply_interface_config(self, interface, settings):
        """
        Apply configuration to a specific network interface.

        Args:
            interface: Interface name (e.g., 'eth0')
            settings: Dictionary with IP, netmask, gateway, etc.
        """
        try:
            # Check if interface should be enabled or disabled
            if settings.get('enabled', True):
                # Bring interface up
                subprocess.run(['ip', 'link', 'set', interface, 'up'],
                               check=True, capture_output=True)
                print(f"  ✓ Interface {interface} enabled")

                # Configure IP address if it's static
                if settings.get('type') == 'static' and 'address' in settings:
                    # Format: ip addr add 192.168.1.100/24 dev eth0
                    addr = f"{settings['address']}/{settings.get('netmask', '24')}"
                    subprocess.run(['ip', 'addr', 'add', addr, 'dev', interface],
                                   capture_output=True)  # Don't check=True, might already exist
                    print(f"  ✓ IP address {addr} configured on {interface}")

            else:
                # Bring interface down
                subprocess.run(['ip', 'link', 'set', interface, 'down'],
                               check=True, capture_output=True)
                print(f"  ✓ Interface {interface} disabled")

            return True

        except subprocess.CalledProcessError as e:
            print(f"  ✗ Error configuring {interface}: {e}")
            return False

    def _apply_firewall_rules(self, rules):
        """
        Apply firewall rules using iptables.

        Args:
            rules: List of firewall rule dictionaries
        """
        try:
            # First, flush existing rules (optional, be careful!)
            # subprocess.run(['iptables', '-F'], check=True)

            for rule in rules:
                # Build iptables command from rule dictionary
                cmd = ['iptables']

                # Add chain (INPUT, OUTPUT, FORWARD)
                cmd.extend(['-A', rule.get('chain', 'INPUT')])

                # Add protocol if specified
                if 'protocol' in rule:
                    cmd.extend(['-p', rule['protocol']])

                # Add port if specified
                if 'port' in rule:
                    cmd.extend(['--dport', str(rule['port'])])

                # Add source IP if specified
                if 'source' in rule:
                    cmd.extend(['-s', rule['source']])

                # Add action (ACCEPT, DROP, REJECT)
                cmd.extend(['-j', rule.get('action', 'ACCEPT')])

                # Execute the command
                subprocess.run(cmd, check=True, capture_output=True)
                print(f"  ✓ Applied rule: {' '.join(cmd[1:])}")

            return True

        except subprocess.CalledProcessError as e:
            print(f"  ✗ Error applying firewall rules: {e}")
            return False

    def get_current_configuration(self):
        """
        Read current system configuration (for saving).
        This captures the current state of network interfaces and firewall.

        Returns:
            dict: Current configuration
        """
        config = {
            'interfaces': {},
            'firewall_rules': []
        }

        # Get interface information
        try:
            # Run 'ip addr show' to get interface info
            result = subprocess.run(['ip', 'addr', 'show'],
                                    capture_output=True, text=True, check=True)
            # Parse the output (simplified for example)
            print("ℹ Current interfaces detected (parsing simplified)")
            # In real implementation, you'd parse result.stdout

        except subprocess.CalledProcessError as e:
            print(f"⚠ Warning: Could not retrieve interface info: {e}")

        # Get firewall rules
        try:
            # Run 'iptables -L' to list rules
            result = subprocess.run(['iptables', '-L', '-n'],
                                    capture_output=True, text=True)
            # Parse the output (simplified for example)
            print("ℹ Current firewall rules detected (parsing simplified)")

        except subprocess.CalledProcessError as e:
            print(f"⚠ Warning: Could not retrieve firewall rules: {e}")

        return config


# Example usage and testing functions
def test_save_and_load():
    """Test function to verify save and load operations work correctly."""
    print("=" * 60)
    print("TESTING NETWORK CONFIGURATION MANAGER")
    print("=" * 60)

    # Create manager instance (using /tmp for testing, not /etc)
    manager = NetworkConfigManager(config_dir="/tmp/network-tool-test")

    # Create sample configuration
    test_config = {
        'interfaces': {
            'eth0': {
                'enabled': True,
                'type': 'static',
                'address': '192.168.1.100',
                'netmask': '24',
                'gateway': '192.168.1.1'
            },
            'wlan0': {
                'enabled': False
            }
        },
        'firewall_rules': [
            {
                'chain': 'INPUT',
                'protocol': 'tcp',
                'port': 22,
                'action': 'ACCEPT',
                'description': 'Allow SSH'
            },
            {
                'chain': 'INPUT',
                'protocol': 'tcp',
                'port': 80,
                'action': 'ACCEPT',
                'description': 'Allow HTTP'
            }
        ]
    }

    # Test saving
    print("\n[TEST 1] Saving configuration...")
    if manager.save_configuration(test_config):
        print("✓ Save test PASSED")
    else:
        print("✗ Save test FAILED")
        return

    # Test loading
    print("\n[TEST 2] Loading configuration...")
    loaded_config = manager.load_configuration()
    if loaded_config:
        print("✓ Load test PASSED")
        print("\nLoaded configuration preview:")
        print(json.dumps(loaded_config, indent=2))
    else:
        print("✗ Load test FAILED")
        return

    # Verify data integrity
    print("\n[TEST 3] Verifying data integrity...")
    if loaded_config['interfaces'] == test_config['interfaces']:
        print("✓ Interfaces match")
    else:
        print("✗ Interfaces don't match")

    if loaded_config['firewall_rules'] == test_config['firewall_rules']:
        print("✓ Firewall rules match")
    else:
        print("✗ Firewall rules don't match")

    print("\n" + "=" * 60)
    print("TESTING COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    # Run tests when script is executed directly
    test_save_and_load()
