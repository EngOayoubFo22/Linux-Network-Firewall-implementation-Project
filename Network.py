import subprocess
import psutil
import socket


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


nm = NetworkManager()
i = nm.enable("eth0")
nm.show_interfaces()

