def firewall_clI():
    print("\n=== Simple Firewall CLI ===")
    print("Type 'help' to show commands.")
    print("Type 'exit' to quit.\n")

    fw = SimpleFirewall()   

    while True:
        cmd = input("fw> ").strip().lower()

        if cmd == "exit":
            print("Exiting firewall CLI.")
            break

        elif cmd == "help":
            print("""
Available commands:

  add            -> Add a firewall rule
  remove-spec    -> Remove rule by specification (protocol, port, action)
  remove-num     -> Remove rule by rule index number
  list           -> List rules in a chain
  clear          -> Remove all rules in a chain
  exit           -> Quit program
""")

        # -----------------------------------------
        elif cmd == "add":
            chain = input("Chain (INPUT/OUTPUT/FORWARD): ").strip()
            protocol = input("Protocol (tcp/udp/icmp): ").strip()
            port = None
            if protocol.lower() in ["tcp", "udp"]:
                port = input("Destination port: ").strip()
            action = input("Action (ACCEPT/DROP/REJECT): ").strip()

            fw.add_rule(chain, protocol, port, action)

        # -----------------------------------------
        elif cmd == "remove-spec":
            chain = input("Chain: ").strip()
            protocol = input("Protocol: ").strip()
            port = input("Destination port: ").strip()
            action = input("Action: ").strip()
            fw.remove_rule_by_spec(chain, protocol, port, action)

        # -----------------------------------------
        elif cmd == "remove-num":
            chain = input("Chain: ").strip()
            number = int(input("Rule number: ").strip())
            fw.remove_rule_by_number(chain, number)

        # -----------------------------------------
        elif cmd == "list":
            chain = input("Chain: ").strip()
            fw.list_rules(chain)

        # -----------------------------------------
        elif cmd == "clear":
            chain = input("Chain: ").strip()
            fw.remove_all_rules(chain)

        else:
            print("Unknown command. Type 'help'.")

from netplan_configurator import NetplanConfigurator   # adjust module name if needed

def configure_static_ip():
    """Menu handler for: 3. Configure static IP for an interface"""
    np = NetplanConfigurator()
    np.check_root()

    # Collect data from user
    config_data = np.get_user_input()

    # Build new config
    config = np.configure(config_data)

    # Show preview
    np.display_config(config)

    # Confirm and apply Save is required here 


def configure_dhcp_ip():
    """Menu handler for: 4. Set dynamic (DHCP) IP for an interface"""
    np = NetplanConfigurator()
    np.check_root()

    # Get interfaces
    interfaces = np.get_interfaces()
    if not interfaces:
        print("❌ No network interfaces found")
        return

    print("\n📌 Available interfaces:")
    for i, iface in enumerate(interfaces, 1):
        print(f"  {i}. {iface}")

    # Select interface
    while True:
        try:
            choice = int(input("\nSelect interface number to set DHCP: ")) - 1
            if 0 <= choice < len(interfaces):
                interface = interfaces[choice]
                break
            print("❌ Invalid selection")
        except ValueError:
            print("❌ Please enter a number")

    # Load current config
    config = np.load_config()

    # Ensure structure exists
    if 'network' not in config:
        config['network'] = {'version': 2, 'ethernets': {}}
    if 'ethernets' not in config['network']:
        config['network']['ethernets'] = {}

    # Set DHCP4 for the chosen interface
    # Remove static-specific keys if present
    config['network']['ethernets'][interface] = {
        'dhcp4': True
    }

    # Show preview
    np.display_config(config)

    # Confirm and apply save function is required here 


