#!/usr/bin/env python3

import json
import os
import subprocess
import yaml
from datetime import datetime
from pathlib import Path


class NetworkConfigManager:
    """
    Manages saving and loading network configurations.
    Stores data in JSON format for easy reading and writing.
    """

    def __init__(self, config_dir="/etc/network-tool"):
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "network_config.json"
        self.backup_dir = self.config_dir / "backups"

        # ✅ FIX: Use the SAME netplan file path as ip_config2.py
        self.netplan_config_file = Path("/etc/netplan/01-netcfg.yaml")
        # WHY: This is the actual file that netplan reads from

        self._ensure_directories()

    def _ensure_directories(self):
        """Create configuration and backup directories if they don't exist."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            print(f"✓ Configuration directory ready: {self.config_dir}")
        except PermissionError:
            print(f"✗ Error: Need root/sudo permission to create {self.config_dir}")
            raise

    def save_configuration(self, config_data):
        """
        Save network configuration to a JSON file.
        """
        try:
            # Add timestamp
            config_data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            config_data['version'] = "1.0"

            # Create backup of existing config
            if self.config_file.exists():
                self._create_backup()

            # Write configuration to file
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=4)

            print(f"✓ Configuration saved successfully to {self.config_file}")

            # Show what was saved
            if 'netplan_config' in config_data:
                print(f"  ├─ Network interface settings saved")
            if 'firewall_rules' in config_data:
                print(f"  ├─ Firewall rules saved ({len(config_data['firewall_rules'])} rules)")
            if 'interfaces' in config_data:
                print(f"  └─ Interface states saved ({len(config_data['interfaces'])} interfaces)")

            return True

        except Exception as e:
            print(f"✗ Error saving configuration: {e}")
            return False

    def load_configuration(self):
        """Load network configuration from JSON file."""
        try:
            if not self.config_file.exists():
                print(f"ℹ No existing configuration found at {self.config_file}")
                return None

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
        """Create a backup of the current configuration file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"network_config_{timestamp}.json"

        try:
            import shutil
            shutil.copy2(self.config_file, backup_file)
            print(f"✓ Backup created: {backup_file}")
        except Exception as e:
            print(f"⚠  Warning: Could not create backup: {e}")

    def apply_network_configuration(self, config_data):
        """
        Apply loaded configuration to the system.
        """
        if not config_data:
            print("✗ No configuration data to apply")
            return False

        success = True

        # =====================================================================
        # STEP 1: Restore netplan YAML file FIRST
        # =====================================================================
        if 'netplan_config' in config_data:
            print("\n→ Restoring netplan configuration...")
            if not self._restore_netplan_config(config_data['netplan_config']):
                print("  ⚠️  Warning: Could not restore netplan config")
                success = False
        else:
            print("\n⚠️  No netplan configuration found in saved data")
        # Step 2: Apply interface states (up/down)
        if 'interfaces' in config_data:
            print("\n→ Applying network interface states...")
            for interface, settings in config_data['interfaces'].items():
                # Skip loopback
                if interface == 'lo':
                    continue

                # Only handle up/down state, not IP addresses
                # (IP addresses are handled by netplan)
                if not self._apply_interface_state(interface, settings):
                    success = False


        # Step 3: Apply firewall rules
        if 'firewall_rules' in config_data:
            print("\n→ Applying firewall rules...")
            if not self._apply_firewall_rules(config_data['firewall_rules']):
                success = False

        return success

    def _restore_netplan_config(self, netplan_full_config):

        try:
            # Write the full config to netplan YAML file
            with open(self.netplan_config_file, 'w') as f:
                yaml.dump(netplan_full_config, f, default_flow_style=False, sort_keys=False)

            print(f"Netplan YAML restored to {self.netplan_config_file}")

            # Apply netplan changes
            try:
                result = subprocess.run(
                    ['netplan', 'apply'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    print(f"  ✓ Netplan configuration applied")
                    return True
                else:
                    print(f"Warning: netplan apply failed: {result.stderr}")
                    return False
            except subprocess.TimeoutExpired:
                print(f"Warning: netplan apply timed out")
                return False

        except Exception as e:
            print(f"  ✗ Error restoring netplan config: {e}")
            return False

    def _apply_interface_state(self, interface, settings):
        """
        Apply interface up/down state only.
        IP addresses are managed by netplan, not here.
        """
        try:
            status = settings.get('status', 'UP')

            if status == 'UP':
                subprocess.run(['ip', 'link', 'set', interface, 'up'],
                               capture_output=True)
                print(f"  ✓ Interface {interface} enabled")
            else:
                subprocess.run(['ip', 'link', 'set', interface, 'down'],
                               capture_output=True)
                print(f"  ✓ Interface {interface} disabled")

            return True

        except subprocess.CalledProcessError as e:
            print(f"  ✗ Error configuring {interface}: {e}")
            return False

    def _apply_firewall_rules(self, rules):
        """Apply firewall rules using iptables."""
        try:
            for rule in rules:
                # Build iptables command from rule dictionary
                cmd = ['iptables']

                # Add chain
                cmd.extend(['-A', rule.get('chain', 'INPUT')])

                # Add protocol
                if 'protocol' in rule:
                    cmd.extend(['-p', rule['protocol']])

                # Add port
                if 'port' in rule:
                    cmd.extend(['--dport', str(rule['port'])])

                # Add source IP
                if 'source' in rule:
                    cmd.extend(['-s', rule['source']])

                # Add action
                cmd.extend(['-j', rule.get('action', 'ACCEPT')])

                # Execute the command
                subprocess.run(cmd, check=True, capture_output=True)
                print(f"  ✓ Applied rule: {' '.join(cmd[1:])}")

            return True

        except subprocess.CalledProcessError as e:
            print(f"  ✗ Error applying firewall rules: {e}")
            return False