import socket
import psutil
import os
import subprocess
import netifaces
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

# -------------------- Collect Info --------------------

def get_ip():
    ip_info = {}
    for iface in netifaces.interfaces():
        addrs = netifaces.ifaddresses(iface).get(netifaces.AF_INET)
        if addrs:
            ip_info[iface] = addrs[0]['addr']
    return ip_info

def get_hostname():
    return socket.gethostname()

def get_disk_usage():
    disk_info = {}
    for part in psutil.disk_partitions():
        usage = psutil.disk_usage(part.mountpoint)
        disk_info[part.device] = {
            "Mountpoint": part.mountpoint,
            "Filesystem Type": part.fstype,
            "Total": f"{usage.total // (1024**3)} GB",
            "Used": f"{usage.used // (1024**3)} GB",
            "Free": f"{usage.free // (1024**3)} GB",
            "Percent": f"{usage.percent}%"
        }
    return disk_info

def get_user_count():
    users = psutil.users()
    return len(users), [user.name for user in users]

def get_command_history():
    user_histories = {}
    for user in os.listdir('/home'):
        hist_file = f"/home/{user}/.bash_history"
        if os.path.exists(hist_file):
            with open(hist_file) as f:
                lines = f.readlines()[-10:]  # Last 10 commands
                user_histories[user] = lines
    return user_histories

def get_open_ports():
    result = subprocess.getoutput("ss -tuln")
    return result

def get_ram_usage():
    vm = psutil.virtual_memory()
    return {
        "Total": f"{vm.total // (1024**2)} MB",
        "Used": f"{vm.used // (1024**2)} MB",
        "Available": f"{vm.available // (1024**2)} MB",
        "Percent": f"{vm.percent}%"
    }

    services = []
    output = subprocess.getoutput("systemctl list-units --type=service --state=running")
    for line in output.splitlines():
        if '.service' in line:
            parts = line.split()
            service_name = parts[0]
            # Get Main PID of the service
            pid_output = subprocess.getoutput(f"systemctl show {service_name} --property=MainPID")
            pid = pid_output.split('=')[1]
            if pid and pid != '0':
                # Get elapsed time
                etime = subprocess.getoutput(f"ps -p {pid} -o etime=").strip()
                services.append((service_name, etime))
            else:
                services.append((service_name, "N/A"))
    return services

def get_running_services():
    services = []
    output = subprocess.getoutput("systemctl list-units --type=service --state=running")
    for line in output.splitlines():
        if '.service' in line:
            parts = line.split()
            service_name = parts[0]
            # Get Main PID of the service
            pid_output = subprocess.getoutput(f"systemctl show {service_name} --property=MainPID")
            pid = pid_output.split('=')[1]
            if pid and pid != '0':
                # Get elapsed time
                etime = subprocess.getoutput(f"ps -p {pid} -o etime=").strip()
                services.append((service_name, etime))
            else:
                services.append((service_name, "N/A"))
    return services

# -------------------- Email Report --------------------
def generate_report():
    report = []
    report.append(f"Hostname: {get_hostname()}")
    report.append(f"IP Addresses: {get_ip()}")
    report.append("\nDisk Usage:")
    for device, stats in get_disk_usage().items():
        report.append(f"  {device}: {stats}")
    count, users = get_user_count()
    report.append(f"\nLogged-in Users ({count}): {users}")
    report.append("\nCommand History:")
    for user, cmds in get_command_history().items():
        report.append(f"  {user}: {''.join(cmds)}")
    report.append("\nOpen Ports:")
    report.append(get_open_ports())
    report.append("\nRAM Usage:")
    report.append(str(get_ram_usage()))
    report.append("\nRunning Services:")
    report.append(str(get_running_services()))
    return "\n".join(report)


def generate_report_html():
    html = f"""
    <html>
    <body style="font-family:Arial,sans-serif;">
        <h2>Server Audit Report - {datetime.now().strftime('%Y-%m-%d')}</h2>
        <h3>Hostname: {get_hostname()}</h3>
        <h4>IP Addresses:</h4>
        <ul>
    """
    for iface, ip in get_ip().items():
        html += f"<li><b>{iface}:</b> {ip}</li>"
    html += "</ul>"

    html += "<h4>Disk Usage:</h4><table border='1' cellpadding='5' cellspacing='0'><tr><th>Device</th><th>Mountpoint</th><th>Type</th><th>Total</th><th>Used</th><th>Free</th><th>Usage</th></tr>"
    for device, stats in get_disk_usage().items():
        html += f"<tr><td>{device}</td><td>{stats['Mountpoint']}</td><td>{stats['Filesystem Type']}</td><td>{stats['Total']}</td><td>{stats['Used']}</td><td>{stats['Free']}</td><td>{stats['Percent']}</td></tr>"
    html += "</table>"

    count, users = get_user_count()
    html += f"<h4>Logged-in Users ({count}):</h4><ul>" + ''.join(f"<li>{u}</li>" for u in users) + "</ul>"

    html += "<h4>Command History (Last 10 commands):</h4>"
    for user, cmds in get_command_history().items():
        html += f"<b>{user}</b><pre>{''.join(cmds)}</pre>"

    html += f"<h4>Open Ports:</h4><pre>{get_open_ports()}</pre>"

    ram = get_ram_usage()
    html += f"""
    <h4>RAM Usage:</h4>
    <ul>
        <li>Total: {ram['Total']}</li>
        <li>Used: {ram['Used']}</li>
        <li>Available: {ram['Available']}</li>
        <li>Percent: {ram['Percent']}</li>
    </ul>
    </body>
    </html>
    """

    html += "<h4>Running Services:</h4><table border='1' cellpadding='5' cellspacing='0'><tr><th>Service</th><th>Uptime</th></tr>"
    for service, uptime in get_running_services():
        html += f"<tr><td>{service}</td><td>{uptime}</td></tr>"
    html += "</table>"

    return html

def send_email(report_html):
    sender = "you@example.com"
    receiver = "admin@example.com"
    subject = f"Server Audit Report - {datetime.now().strftime('%Y-%m-%d')}"
    password = "your_email_password"

    msg = MIMEText(report_html, 'html')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = receiver

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.starttls()
            s.login(sender, password)
            s.send_message(msg)
        print("HTML email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")



# main
if __name__ == "__main__":
    # daily_report = generate_report_html()
    daily_report = generate_report()
    print(daily_report)
    # send_email(daily_report)