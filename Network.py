import subprocess
import psutil
import socket
import re

class NetworkManager:
    """
    Handles network interface operations:
    - list interfaces
    - show status
    - enable/disable interfaces
    - advanced detection (future)
    """

    def __init__(self):
        pass


    def run_command(self, command):
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)

            if result.returncode == 0:
                    return "Command executed successfully!"
            else:
                    # Return the actual error message
                    error_msg = result.stderr.strip() or "Unknown error."
                    return f"Command failed: {error_msg}"

        except Exception as e:
                return f"Exception: {str(e)}"

    def get_interface_state(self, interface):
        """
        Get current state of a network interface.

        Args:
            interface: Interface name (e.g., 'eth0', 'wlan0')

        Returns:
            dict: Interface state containing:
                - enabled: bool (is interface up?)
                - addresses: list of IP addresses
                - type: 'static' or 'dhcp' (simplified detection)
        """
        state = {
            'enabled': False,
            'addresses': [],
            'type': 'unknown'
        }

        try:
            # Get interface details using 'ip addr show'
            result = subprocess.run(
                ['ip', 'addr', 'show', interface],
                capture_output=True,
                text=True,
                check=True
            )

            output = result.stdout

            # Check if interface is UP
            if 'state UP' in output or 'UP' in output.split('\n')[0]:
                state['enabled'] = True

            # Extract IP addresses
            # Look for lines like: inet 192.168.1.100/24
            ip_pattern = r'inet (\d+\.\d+\.\d+\.\d+)/(\d+)'
            matches = re.findall(ip_pattern, output)

            for ip, netmask in matches:
                if ip != '127.0.0.1':  # Skip localhost
                    state['addresses'].append({
                        'ip': ip,
                        'netmask': netmask
                    })

            # Simple heuristic: if it has an IP, assume it's configured
            # (Real detection would need to check DHCP lease files or netplan config)
            if state['addresses']:
                state['type'] = 'configured'

        except subprocess.CalledProcessError as e:
            print(f"⚠️  Could not get state for {interface}: {e}")
        except Exception as e:
            print(f"⚠️  Error reading {interface} state: {e}")

        return state


    def get_interfaces(self):
        """
        Uses psutil to retrieve:
        - MAC address
        - IPv4 / IPv6 addresses
        - UP/DOWN status
        """
        interfaces = {}

        # psutil.net_if_addrs() gives IPs + MAC
        addr = psutil.net_if_addrs()
        stat = psutil.net_if_stats()
        for iface, address_list in addr.items():
            interfaces[iface] = {
                "mac": "N/A",
                "ipv4": [],
                "ipv6": [],
                "status": "Down"
            }
            for address in address_list:
                if address.family == psutil.AF_LINK:
                    interfaces[iface]["mac"] = address.address
                elif address.family == socket.AF_INET:
                    interfaces[iface]["ipv4"].append(
                        f"{address.address}/{address.netmask}"
                    )
                elif address.family == socket.AF_INET6:
                    interfaces[iface]["ipv6"].append(
                        f"{address.address}/{address.netmask}"
                    )
            if iface in stat:
                interfaces[iface]["status"] = "UP" if stat[iface].isup else "DOWN"
        return interfaces

    def enable(self, iface):
        if iface not in psutil.net_if_addrs():
            return f"Error: interface '{iface}' does not exist."

        return self.run_command(f"sudo ip link set dev {iface} up")

    def disable(self, iface):
        if iface not in psutil.net_if_addrs():
            return f"Error: interface '{iface}' does not exist."
        return self.run_command(f"sudo ip link set dev {iface} down")

    def get_interface_names(self):
        return list(psutil.net_if_addrs().keys())

    def show_interfaces(self):
        interfaces = self.get_interfaces()
        for iface, data in interfaces.items():
            print(f"\nInterface: {iface}")
            print(f"  Status : {data['status']}")
            print(f"  MAC    : {data['mac']}")
            print(f"  IPv4   : {', '.join(data['ipv4']) if data['ipv4'] else 'None'}")
            print(f"  IPv6   : {', '.join(data['ipv6']) if data['ipv6'] else 'None'}")

