# 🛡️ Linux Network & Firewall Administration Tool

![Linux](https://img.shields.io/badge/platform-Linux-blue)
![Python](https://img.shields.io/badge/python-3.x-green)
![Firewall](https://img.shields.io/badge/firewall-iptables-red)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## 📌 Overview

This project is a **Linux-based Network and Firewall Administration Tool** implemented in Python.  
It provides a **command-line interface (CLI)** for managing network interfaces, configuring IP addressing (static and DHCP), administering firewall rules using `iptables`, and persisting configurations across system reboots.

The tool is designed for **system administrators, DevOps engineers, and cybersecurity students** who require a modular, extensible, and educational framework for Linux network and firewall management.

---

## 🧱 System Architecture

The project follows a **modular architecture**, separating networking, firewall, persistence, and CLI concerns.


```
main_CLI.py
│
├── Network.py        → Network interface inspection & control
├── ip_config.py      → Static & DHCP IP configuration (Netplan)
├── firewall.py       → Firewall rule management (iptables)
├── persistence.py    → Configuration persistence & restoration
```

Each module is independently reusable and testable.

---

## ✨ Key Features

- 🔧 Enable and disable network interfaces
- 🌐 Display MAC, IPv4, IPv6, and interface status
- 📡 Configure static IP addressing using Netplan
- 🔄 Switch interfaces to DHCP
- 🔐 Add, list, and remove firewall rules (INPUT / OUTPUT / FORWARD)
- 💾 Save and restore network and firewall configurations
- ♻️ Automatic configuration backup with timestamps
- 🧪 Built-in save/load verification logic

---

## 🛠️ Technologies and Tools

| Category | Tools |
|--------|------|
| Language | Python 3 |
| OS | Linux |
| Firewall | iptables (python-iptables) |
| Networking | iproute2, psutil |
| IP Configuration | Netplan |
| Persistence | JSON |
| Privileges | sudo / root |

---

## 📋 Prerequisites

- Linux system (Ubuntu/Debian recommended)
- Python ≥ 3.8
- Root privileges
- Required packages:

```bash
sudo apt install iproute2 netplan.io iptables
pip install psutil python-iptables pyyaml
```
## 🚀 Installation

Clone the repository:
```
git clone https://github.com/yourusername/linux-network-firewall-tool.git
cd linux-network-firewall-tool
```

Make the main script executable:
```
chmod +x main_CLI.py
```

Run the tool:
```
sudo python3 main_CLI.py
```
## 🔐 Firewall Configuration

Firewall rules are managed using iptables through a Python abstraction.

Supported operations:

- Add firewall rules
- Delete rules by specification or index
- List rules by chain
- Clear chains safely

--- 

Example rule:
```
-A INPUT -p tcp --dport 22 -j ACCEPT
```
## 🌐 Network Configuration
- Interface Management
- Detects all active interfaces
- Displays MAC, IPv4, IPv6, and status
- Enables/disables interfaces using ip link
- Static IP Configuration (Netplan)
- Interactive user input
- IP and gateway validation
- YAML preview before applying
- Applied safely using netplan apply
- DHCP Configuration
- Removes static IPv4 configuration
- Enables DHCP dynamically per interface

## 💾 Configuration Persistence

The tool supports saving and restoring configurations using JSON:
    - Network interface state
    - Firewall rules
    - Versioning and timestamps
    - Automatic backup creation

---

Default storage path:
```
/etc/network-tool/
```

Example saved configuration:
```
{
  "interfaces": {
    "eth0": {
      "enabled": true,
      "type": "static"
    }
  },
  "firewall_rules": [],
  "timestamp": "2025-01-15 10:30:00"
}
```
## 🖥️ CLI Usage

Start the CLI:
```
sudo python3 main_CLI.py
```



## Main menu:

1. Alter Network Settings
2. Alter Firewall Settings
3. Exit


Each menu provides guided, interactive administration options.

## 🔐 Security Considerations

- Requires explicit root privileges
- No silent firewall flushing
- Rule validation before insertion
- Human-readable configuration backups
- Clear separation between networking and firewall logic

## 🧪 Testing

The persistence module includes a test routine that verifies:

- Saving configurations
- Loading configurations
- Backup creation
- Data integrity

## ⚠️ Limitations

- iptables-based (no nftables support yet)
- Netplan-focused (Ubuntu/Debian)
- Simplified parsing of existing system rules
- CLI-only (no GUI)

## 🚧 Future Enhancements

- nftables backend support
- Firewall rule templates
- Improved parsing of existing configurations
- Systemd service for auto-restore on boot
- Role-based access control
- Network topology visualization

## 🤝 Contributing

Contributions are welcome.
- Fork the repository
- Create a feature branch
- Commit changes with clear messages
- Submit a pull request

## 📄 License

This project is released under the MIT License.

## 📚 References

iptables documentation: https://man7.org/linux/man-pages/man8/iptables.8.html

Netplan documentation: https://netplan.io/reference

python-iptables: https://github.com/ldx/python-iptables

psutil networking API: https://psutil.readthedocs.io/

## 📬 Contact

For questions, improvements, or academic use, please open an issue on GitHub.

