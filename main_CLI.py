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
