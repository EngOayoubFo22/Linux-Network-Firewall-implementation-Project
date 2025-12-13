import Network as nw
from firewall import *
import persistence as pst
from ip_config import NetplanConfigurator


# ==============================================================================
# FIREWALL MENU FUNCTIONS
# ==============================================================================

def show_firewall_rules():
    """
    Show current firewall rules for a chosen chain.
    """
    fw = SimpleFirewall()
    chain = input("Chain to list (INPUT/OUTPUT/FORWARD): ").strip()
    fw.list_rules(chain)


def add_firewall_rule():
    """
    Add a firewall rule (interactive).
    """
    fw = SimpleFirewall()

    chain = input("Chain (INPUT/OUTPUT/FORWARD): ").strip()
    protocol = input("Protocol (tcp/udp/icmp): ").strip()

    port = None
    if protocol.lower() in ["tcp", "udp"]:
        port = input("Destination port: ").strip()

    action = input("Action (ACCEPT/DROP/REJECT): ").strip()

    fw.add_rule(chain, protocol, port, action)


def delete_firewall_rule():
    """
    Delete a firewall rule.
    """
    fw = SimpleFirewall()

    print("\nDelete rule by:")
    print("  1. Full specification (chain, protocol, port, action)")
    print("  2. Rule number (index in chain)")

    choice = input("Choose option [1-2]: ").strip()

    if choice == "1":
        chain = input("Chain (INPUT/OUTPUT/FORWARD): ").strip()
        protocol = input("Protocol (tcp/udp/icmp): ").strip()
        port = input("Destination port (leave empty if not applicable): ").strip()
        action = input("Action (ACCEPT/DROP/REJECT): ").strip()

        if port == "":
            port = None

        fw.remove_rule_by_spec(chain, protocol, port, action)

    elif choice == "2":
        chain = input("Chain (INPUT/OUTPUT/FORWARD): ").strip()
        try:
            number = int(input("Rule number: ").strip())
        except ValueError:
            print("❌ Invalid rule number.")
            return

        fw.remove_rule_by_number(chain, number)

    else:
        print("❌ Invalid choice, no rule deleted.")


# ==============================================================================
# NETWORK IP CONFIGURATION FUNCTIONS
# ==============================================================================

def configure_static_ip(config_manager, nm, fw):
    """
    Handler for: 3. Configure static IP for an interface

    🔧 CHANGE: Added config_manager, nm, fw parameters
    WHY: So we can auto-save after configuration
    """
    np = NetplanConfigurator()
    np.check_root()

    # Collect config data interactively (interface, IP, gateway, DNS, ...)
    config_data = np.get_user_input()

    # Build full netplan configuration (static)
    config = np.configure_static(config_data)

    # Show preview
    np.display_config(config)

    # Confirm and apply
    confirm = input("\nApply this STATIC IP configuration? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("❌ Static configuration cancelled")
        return

    # Apply the configuration
    np.save_config(config)
    if np.apply_config():
        print("\n✓ Static IP configuration completed!")
        print(f"   Interface: {config_data['interface']}")
        print(f"   IP:       {config_data['ip'].split('/')[0]}")
        print(f"   Gateway:  {config_data['gateway']}")
        print(f"   DNS:      {', '.join(config_data['dns'])}")

        # =====================================================================
        # 🆕 NEW: Auto-save after successful configuration
        # =====================================================================
        print("\n💾 Auto-saving configuration...")
        save_current_configuration(config_manager, nm, fw)
        # WHY: User just changed IP settings, we should save it automatically
        # so it persists after reboot
        # =====================================================================
    else:
        print("⚠️ Configuration saved but failed to apply")


def configure_dhcp_ip(config_manager, nm, fw):
    """
    Handler for: 4. Set dynamic (DHCP) IP for an interface

    🔧 CHANGE: Added config_manager, nm, fw parameters
    WHY: So we can auto-save after configuration
    """
    np = NetplanConfigurator()
    np.check_root()

    # Get available interfaces
    interfaces = np.get_interfaces()
    if not interfaces:
        print("❌ No network interfaces found")
        return

    print("\nAvailable interfaces:")
    for i, iface in enumerate(interfaces, 1):
        print(f"  {i}. {iface}")

    # Select interface
    while True:
        try:
            choice = int(input("\nSelect interface number to use DHCP: ")) - 1
            if 0 <= choice < len(interfaces):
                interface = interfaces[choice]
                break
            print("❌ Invalid selection")
        except ValueError:
            print("❌ Please enter a number")

    # Build full netplan configuration for DHCP
    config = np.configure_dhcp(interface)

    # Show preview
    np.display_config(config)

    # Confirm and apply
    confirm = input("\nApply this DHCP configuration? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("❌ DHCP configuration cancelled")
        return

    # Apply the configuration
    np.save_config(config)
    if np.apply_config():
        print(f"\n✓ DHCP enabled on interface: {interface}")

        # =====================================================================
        # 🔧 FIX: Wait for DHCP to get IP, then save
        # =====================================================================
        import time
        print("\n⏳ Waiting for DHCP to assign IP address...")
        time.sleep(3)  # Give DHCP client time to get IP

        print("💾 Auto-saving configuration...")
        save_current_configuration(config_manager, nm, fw)
        # WHY: User just changed to DHCP, we should save it so it persists
        # =====================================================================
    else:
        print("⚠️ Configuration saved but failed to apply")


# ==============================================================================
# 🆕 PERSISTENCE HELPER FUNCTIONS (NEW!)
# ==============================================================================

def capture_current_network_state(nm, fw):
    """
    Capture current network and firewall state for saving.

    This captures:
    1. Interface states (UP/DOWN, IPs) from NetworkManager
    2. Firewall rules from SimpleFirewall
    3. The FULL netplan YAML configuration

    Returns a dict ready to be saved by persistence.py
    """
    config = {
        'interfaces': {},
        'firewall_rules': [],
        'netplan_config': {}  # ✅ NEW: Store full netplan config
    }

    # Step 1: Capture network interface states
    try:
        all_interfaces = nm.get_interfaces()

        for interface, state in all_interfaces.items():
            config['interfaces'][interface] = {
                'status': state['status'],
                'ipv6': state['ipv6'],
                'ipv4': state['ipv4'],
                'mac': state['mac']
            }

        print(f"✓ Captured state for {len(config['interfaces'])} interface(s)")

    except Exception as e:
        print(f"⚠️  Warning: Could not capture interface state: {e}")

    # STEP 2: Capture firewall rules
    try:
        rules = fw.get_all_rules()
        config['firewall_rules'] = rules
        print(f"✓ Captured {len(rules)} firewall rule(s)")

    except Exception as e:
        print(f"⚠️  Warning: Could not capture firewall rules: {e}")


    # Step 3: Capture full netplan configuration
    try:
        from ip_config import NetplanConfigurator
        np = NetplanConfigurator()

        # Load the FULL netplan config (includes network, version, ethernets)
        netplan_config = np.load_config()

        # ✅ CRITICAL: Save the ENTIRE config, not just ethernets
        config['netplan_config'] = netplan_config

        # Show what we captured
        if 'network' in netplan_config and 'ethernets' in netplan_config['network']:
            num_ifaces = len(netplan_config['network']['ethernets'])
            print(f"✓ Captured full netplan configuration ({num_ifaces} interface(s))")
        else:
            print(f"⚠️  Warning: Netplan config is empty or malformed")

    except Exception as e:
        print(f"⚠️  Warning: Could not capture netplan config: {e}")
        config['netplan_config'] = {'network': {'version': 2, 'ethernets': {}}}

    # WHY THIS MATTERS:
    # - We need the FULL netplan structure {'network': {'version': 2, 'ethernets': {...}}}
    # - Not just the 'ethernets' part
    # - This way when we restore, we write back the exact same YAML structure
    # =========================================================================

    return config


def save_current_configuration(config_manager, nm, fw):
    """
    Save current network configuration to disk.
    This is called when user selects "Save Configurations" from menu.
    """
    print("\n💾 Saving current configuration...")

    # ✅ Capture includes full netplan config now
    current_config = capture_current_network_state(nm, fw)

    # Save to disk
    if config_manager.save_configuration(current_config):
        print("✅ Configuration saved successfully!")
        print("   Your settings will persist after reboot.")
    else:
        print("❌ Failed to save configuration.")


def restore_saved_configuration(config_manager, nm, fw):
    """
    Load and apply previously saved configuration.
    Called automatically when the program starts.
    """
    print("\n🔄 Checking for saved configuration...")

    # Try to load saved configuration
    saved_config = config_manager.load_configuration()

    if not saved_config:
        print("ℹ️  No previous configuration found (this is normal for first run)")
        return False

    # Show user what was saved
    print(f"✅ Found saved configuration from: {saved_config.get('timestamp', 'unknown time')}")
    print("\nSaved configuration contains:")
    print(f"  - {len(saved_config.get('interfaces', {}))} network interface(s)")
    print(f"  - {len(saved_config.get('firewall_rules', []))} firewall rule(s)")

    # Check if netplan config exists
    if 'netplan_config' in saved_config:
        if 'network' in saved_config['netplan_config']:
            ethernets = saved_config['netplan_config'].get('network', {}).get('ethernets', {})
            print(f"  - Netplan configuration for {len(ethernets)} interface(s)")
    else:
        print(f"  ⚠️  No netplan configuration found (may not restore IP settings)")

    # Ask user if they want to restore
    restore = input("\nRestore this configuration? (yes/no): ").strip().lower()

    if restore != 'yes':
        print("→ Starting with current system configuration")
        return False

    # Apply the saved configuration
    print("\n→ Restoring configuration...")

    if config_manager.apply_network_configuration(saved_config):
        print("✅ Configuration restored successfully!")
        return True
    else:
        print("⚠️  Some settings may not have been applied correctly")
        return False


# ==============================================================================
# MAIN PROGRAM
# ==============================================================================

def main():
    config_manager = pst.NetworkConfigManager()
    nm = nw.NetworkManager()
    fw = SimpleFirewall()
    restore_saved_configuration(config_manager, nm, fw)

    # =========================================================================
    # Main menu loop
    # =========================================================================
    while True:
        print("\n=== Main Menu ===")
        print("1. Alter Network Settings")
        print("2. Alter Firewall Settings")
        print("3. Exit")

        try:
            main_choice = int(input("Choose option [1-3]: ").strip())
        except ValueError:
            print("❌ Please enter a valid number.")
            continue

        # =====================================================================
        # NETWORK SETTINGS SUBMENU
        # =====================================================================
        if main_choice == 1:
            print("\n=== Network Settings ===")
            print("1. Show current network interfaces and IPs")
            print("2. Enable/Disable a network interface")
            print("3. Configure static IP for an interface")
            print("4. Set dynamic (DHCP) IP for an interface")
            print("5. Save Configurations")
            print("6. Back to Main Menu")

            try:
                net_choice = int(input("Choose option [1-6]: ").strip())
            except ValueError:
                print("❌ Please enter a valid number.")
                continue

            if net_choice == 1:
                # Show current interfaces
                nm.show_interfaces()

            elif net_choice == 2:
                # Enable/Disable interface
                print("Available interfaces:", ", ".join(nm.get_interface_names()))
                iface = input("Please enter the interface: ").strip()
                option = input("Enter 'e' to enable or 'd' to disable: ").strip().lower()

                if option == "e":
                    result = nm.enable(iface)
                    print(result)
                elif option == "d":
                    result = nm.disable(iface)
                    print(result)
                else:
                    print("❌ Please enter a valid option (e or d)")

            elif net_choice == 3:
                configure_static_ip(config_manager, nm, fw)
            elif net_choice == 4:
                configure_dhcp_ip(config_manager, nm, fw)

            elif net_choice == 5:
                save_current_configuration(config_manager, nm, fw)

            elif net_choice == 6:
                # Back to main menu
                continue
            else:
                print("❌ Invalid option in Network Settings.")

        # =====================================================================
        # FIREWALL SETTINGS SUBMENU
        # =====================================================================
        elif main_choice == 2:
            print("\n=== Firewall Settings ===")
            print("1. Show current firewall rules")
            print("2. Add a new firewall rule")
            print("3. Delete a firewall rule")
            print("4. Save Configurations")
            print("5. Back to Main Menu")

            try:
                fw_choice = int(input("Choose option [1-5]: ").strip())
            except ValueError:
                print("❌ Please enter a valid number.")
                continue

            if fw_choice == 1:
                # Show firewall rules
                show_firewall_rules()

            elif fw_choice == 2:
                # Add firewall rule
                add_firewall_rule()

            elif fw_choice == 3:
                # Delete firewall rule
                delete_firewall_rule()

            elif fw_choice == 4:
                save_current_configuration(config_manager, nm, fw)

            elif fw_choice == 5:
                # Back to main menu
                continue
            else:
                print("❌ Invalid option in Firewall Settings.")

        # =====================================================================
        # EXIT
        # =====================================================================
        elif main_choice == 3:
            print("Exiting…")
            break
        else:
            print("❌ Invalid main menu option.")


if __name__ == "__main__":
    main()