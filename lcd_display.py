import time
import socket
import requests
import psutil
from RPLCD.i2c import CharLCD
import os

lcd = CharLCD(i2c_expander='PCF8574', address=0x27, port=1, cols=20, rows=4, charmap='A00', auto_linebreaks=False)

NET_INTERFACE = "eth0"
MAX_SPEED_MBPS = 1000
SCREEN_DURATION = 3

def get_hostname():
    return os.uname().nodename

def get_uptime():
    uptime_seconds = time.time() - psutil.boot_time()
    days = int(uptime_seconds // (24 * 3600))
    hours = int((uptime_seconds % (24 * 3600)) // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    return f"{days}d {hours}h {minutes}m"

def get_cpu_temp():
    """Retrieves CPU temperature in Fahrenheit."""
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp_c = int(f.read()) / 1000.0
        temp_f = (temp_c * 9/5) + 32  # Convert to Fahrenheit
        return f"{temp_f:.1f}F"
    except:
        return "N/A"

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "No IP"

def get_public_ip():
    try:
        return requests.get("https://api64.ipify.org?format=text", timeout=5).text
    except:
        return "No Internet"

def get_storage_info():
    """Retrieves storage info for real mounted drives (HDDs, SSDs, USBs)."""
    storage_data = []
    seen_devices = set()
    for part in psutil.disk_partitions(all=False):  
        device = part.device.replace("1", "")  
        if device.startswith("/dev/loop") or "snap" in part.mountpoint or device in seen_devices:
            continue  
        seen_devices.add(device)  
        try:
            usage = psutil.disk_usage(part.mountpoint)
            total_gb = usage.total / (1024**3)
            percent_used = usage.percent
            storage_data.append(f"{device}: {total_gb:.1f}GB {percent_used:.0f}%")
        except:
            continue  

    if not storage_data:
        storage_data = ["No Drives Detected", " ", " "]  # Ensure at least 3 lines

    return storage_data  

def get_network_utilization():
    try:
        net1 = psutil.net_io_counters(pernic=True).get(NET_INTERFACE, None)
        if net1 is None:
            return {"util": "No Eth0", "tx": "TX: N/A", "rx": "RX: N/A"}
        time.sleep(1)
        net2 = psutil.net_io_counters(pernic=True).get(NET_INTERFACE, None)
        if net2 is None:
            return {"util": "No Eth0", "tx": "TX: N/A", "rx": "RX: N/A"}
        up_speed_mbps = ((net2.bytes_sent - net1.bytes_sent) * 8) / (1024**2)
        down_speed_mbps = ((net2.bytes_recv - net1.bytes_recv) * 8) / (1024**2)
        up_util = (up_speed_mbps / MAX_SPEED_MBPS) * 100 if MAX_SPEED_MBPS > 0 else 0
        down_util = (down_speed_mbps / MAX_SPEED_MBPS) * 100 if MAX_SPEED_MBPS > 0 else 0
        total_util = (up_util + down_util) / 2
        return {
            "util": f"Up: {up_speed_mbps:.1f} / Dn: {down_speed_mbps:.1f} Mbps | {total_util:.0f}%",
            "tx": f"TX: {net2.bytes_sent / (1024**3):.2f}GB",
            "rx": f"RX: {net2.bytes_recv / (1024**3):.2f}GB",
        }
    except:
        return {"util": "Net Err", "tx": "TX: N/A", "rx": "RX: N/A"}

def update_lcd(lines):
    lcd.clear()  # ✅ Ensure the screen is cleared before updating
    for row, text in enumerate(lines[:4]):
        lcd.cursor_pos = (row, 0)
        lcd.write_string(text[:20].ljust(20))

try:
    screen_index = 0

    while True:
        hostname = get_hostname()
        storage = get_storage_info()  # ✅ Fetch storage inside the loop (fixes scope issue)

        # ✅ Debugging: Print storage data to verify
        #print(f"Screen Index: {screen_index}, Storage Data: {storage}")

        if screen_index == 0:
            lines = [
                f"PiRAID - {hostname}",
                f"Time: {time.strftime('%I:%M %p')}",
                f"Date: {time.strftime('%m/%d/%y')}",
                f"Uptime: {get_uptime()}"
            ]

        elif screen_index == 1:
            cpu_mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            cpu_temp = get_cpu_temp()
            lines = [
                "PiRAID - System",
                f"CPU: {psutil.cpu_percent(interval=1)}% {cpu_temp}",  
                f"RAM: {cpu_mem.used // (1024**3)}GB/{cpu_mem.total // (1024**3)}GB {cpu_mem.percent}%",
                f"SWAP: {swap.used // (1024**3)}GB/{swap.total // (1024**3)}GB {swap.percent}%"
            ]

        elif screen_index == 2:
            network = get_network_utilization()
            lines = [
                "PiRAID - Network 1",
                f"LAN: {get_local_ip()}",
                f"WAN: {get_public_ip()}",
                f"{network['util']}"
            ]

        elif screen_index == 3:
            network = get_network_utilization()
            lines = [
                "PiRAID - Network 2",
                f"Upload: {network['tx']}",
                f"Download: {network['rx']}",
                " "
            ]

        elif screen_index == 4:
            lines = ["PiRAID - Storage (1)"]

            if len(storage) > 0:
                lines.extend(storage[:3])  # ✅ Show first 3 drives
            else:
                lines.append("No Drives Found")

            while len(lines) < 4:
                lines.append(" ")  

        elif screen_index == 5:
            lines = ["PiRAID - Storage (2)"]

            if len(storage) > 3:
                lines.extend(storage[3:6])  # ✅ Show next 3 drives
            else:
                lines.append("No More Drives")  

            while len(lines) < 4:
                lines.append(" ")  

        update_lcd(lines)  
        time.sleep(SCREEN_DURATION)

        screen_index = (screen_index + 1) % 6  

except KeyboardInterrupt:
    lcd.clear()
    print("Exiting...")
except Exception as e:
    lcd.clear()
    print(f"Error: {e}")
