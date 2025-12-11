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

from netplan_configurator import NetplanConfigurator  # adjust module name if needed


def configure_static_ip():
    """Handler for: 3. Configure static IP for an interface"""
    np = NetplanConfigurator()
    np.check_root()

    # Collect config data interactively (interface, IP, gateway, DNS, ...)
    config_data = np.get_user_input()

    # Build full netplan configuration (static)
    config = np.configure(config_data)

    # Show preview
    np.display_config(config)

    # Confirm and apply
    confirm = input("\nApply this STATIC IP configuration? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("❌ Static configuration cancelled")
        return

  #  np.save_config(config)
  #  if np.apply_config():
      #  print("\n✓ Static IP configuration completed!")
     #   print(f"   Interface: {config_data['interface']}")
      #  print(f"   IP:       {config_data['ip'].split('/')[0]}")
      #  print(f"   Gateway:  {config_data['gateway']}")
       # print(f"   DNS:      {', '.join(config_data['dns'])}")
   # else:
    #    print("⚠️ Configuration saved but failed to apply")


def configure_dhcp_ip():
    """Handler for: 4. Set dynamic (DHCP) IP for an interface"""
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

    # Build full netplan configuration using your class method
    # (assuming you implemented: configure_dhcp(self, interface) -> dict)
    config = np.configure_dhcp(interface)

    # Show preview
    np.display_config(config)

    # Confirm and apply
    confirm = input("\nApply this DHCP configuration? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("❌ DHCP configuration cancelled")
        return

    #np.save_config(config)
    #if np.apply_config():
     #   print(f"\n✓ DHCP enabled on interface: {interface}")
    #else:
     #   print("⚠️ Configuration saved but failed to apply")


def main():
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

        # ---------------- Network Settings ----------------
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
                # TODO: call function to show interfaces and IPs
                print("→ [Stub] Show current network interfaces and IPs")
            elif net_choice == 2:
                # TODO: call function to enable/disable interface
                print("→ [Stub] Enable/Disable a network interface")
            elif net_choice == 3:
                configure_static_ip()
                print("→ [Stub] Configure static IP for an interface")
            elif net_choice == 4:
                configure_dhcp_ip()
                print("→ [Stub] Set dynamic (DHCP) IP for an interface")
            elif net_choice == 5:
                # TODO: call function to save configurations, if needed
                print("→ [Stub] Save configurations")
            elif net_choice == 6:
                # back to main menu
                continue
            else:
                print("❌ Invalid option in Network Settings.")

        # ---------------- Firewall Settings ----------------
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
                # TODO: call function to show firewall rules
                print("→ [Stub] Show current firewall rules")
            elif fw_choice == 2:
                # TODO: call function to add firewall rule
                print("→ [Stub] Add a new firewall rule")
            elif fw_choice == 3:
                # TODO: call function to delete firewall rule
                print("→ [Stub] Delete a firewall rule")
            elif fw_choice == 4:
                # TODO: call function to save firewall config
                print("→ [Stub] Save firewall configurations")
            elif fw_choice == 5:
                # back to main menu
                continue
            else:
                print("❌ Invalid option in Firewall Settings.")

        # ---------------- Exit ----------------
        elif main_choice == 3:
            print("Exiting…")
            break
        else:
            print("❌ Invalid main menu option.")


if __name__ == "__main__":
    main()



