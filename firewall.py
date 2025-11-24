import iptc

class SimpleFirewall:

    def __init__(self, table_name='filter'):

        if table_name.lower() == 'filter':
            self.table = iptc.Table(iptc.Table.FILTER)
        elif table_name.lower() == 'nat':
            self.table = iptc.Table(iptc.Table.NAT)
        elif table_name.lower() == 'mangle':
            self.table = iptc.Table(iptc.Table.MANGLE)
        else:
            raise ValueError("Unsupported table name. Use 'filter', 'nat', or 'mangle'.")

    def add_rule(self, chain_name, protocol, destination_port, action):
        """
        Adds a rule to the specified chain.
        chain_name: 'INPUT', 'OUTPUT', or 'FORWARD'
        protocol: 'tcp', 'udp', or 'icmp'
        destination_port: integer (required for tcp/udp)
        action: 'ACCEPT', 'DROP', 'REJECT'
        """
        # Basic validation
        if chain_name.upper() not in ['INPUT', 'OUTPUT', 'FORWARD']:
            print("Invalid chain name. Must be INPUT, OUTPUT, or FORWARD.")
            return
        if protocol.lower() not in ['tcp', 'udp', 'icmp']:
            print("Invalid protocol. Must be tcp, udp, or icmp.")
            return
        if protocol.lower() in ['tcp', 'udp'] and not destination_port:
            print("Destination port is required for TCP/UDP.")
            return
        if action.upper() not in ['ACCEPT', 'DROP', 'REJECT']:
            print("Invalid action. Must be ACCEPT, DROP, or REJECT.")
            return

        chain = iptc.Chain(self.table, chain_name.upper())
        rule = iptc.Rule()
        rule.protocol = protocol.lower()

        if protocol.lower() in ['tcp', 'udp']:
            match = iptc.Match(rule, protocol.lower())
            match.dport = str(destination_port)
            rule.add_match(match)

        rule.target = iptc.Target(rule, action.upper())
        chain.append_rule(rule)
        print(f"Rule added: -A {chain_name.upper()} -p {protocol.lower()} --dport {destination_port} -j {action.upper()}")

    def remove_rule_by_spec(self, chain_name, protocol, destination_port, action):
        """
        Remove a rule based on its specification.
        """
        chain = iptc.Chain(self.table, chain_name.upper())
        for rule in chain.rules:
            if rule.protocol == protocol.lower() and rule.target.name == action.upper():
                for match in rule.matches:
                    if hasattr(match, "dport") and match.dport == str(destination_port):
                        chain.delete_rule(rule)
                        print(f"Rule removed: -D {chain_name.upper()} -p {protocol.lower()} --dport {destination_port} -j {action.upper()}")
                        return
        print("Rule not found.")

    def remove_rule_by_number(self, chain_name, rule_number):
        """
        Remove a rule by its position in the chain (1-indexed).
        """
        chain = iptc.Chain(self.table, chain_name.upper())
        try:
            chain.delete_rule(chain.rules[rule_number - 1])
            print(f"Rule at position {rule_number} removed from {chain_name.upper()} chain.")
        except IndexError:
            print(f"Rule at position {rule_number} not found in {chain_name.upper()} chain.")

    def list_rules(self, chain_name):
        """
        List all rules in the specified chain.
        """
        chain = iptc.Chain(self.table, chain_name.upper())
        if not chain.rules:
            print(f"No rules in {chain_name.upper()} chain.")
            return
        print(f"Rules in {chain_name.upper()} chain:")
        for i, rule in enumerate(chain.rules, start=1):
            proto = rule.protocol
            action = rule.target.name
            dport = None
            for match in rule.matches:
                if hasattr(match, "dport"):
                    dport = match.dport
            if dport:
                print(f"{i}. -p {proto} --dport {dport} -j {action}")
            else:
                print(f"{i}. -p {proto} -j {action}")

    def remove_all_rules(self, chain_name):
        """
        Remove all rules in the specified chain.
        """
        if chain_name.upper() not in ['INPUT', 'OUTPUT', 'FORWARD']:
            print("Invalid chain name. Must be INPUT, OUTPUT, or FORWARD.")
            return

        chain = iptc.Chain(self.table, chain_name.upper())
        if not chain.rules:
            print(f"No rules to remove in {chain_name.upper()} chain.")
            return

        for rule in chain.rules[:]:  
            chain.delete_rule(rule)
        print(f"All rules removed from {chain_name.upper()} chain.")


## test 
if __name__ == "__main__":
    fw = SimpleFirewall()

    # Test adding rule
    fw.add_rule("INPUT", "tcp", 8080, "ACCEPT")

    # Test listing
    fw.list_rules("INPUT")

    # Test removing rule
    fw.remove_rule_by_spec("INPUT", "tcp", 8080, "ACCEPT")

    fw.list_rules("INPUT")