#!/bin/bash

echo "🚀 Installing dependencies..."
sudo apt update && sudo apt install -y python3 python3-pip python3-venv i2c-tools

echo "🔍 Detecting current user..."
DEFAULT_USER=$(whoami)
read -p "Enter the username to run the PiRAID service [$DEFAULT_USER]: " PI_USER
PI_USER=${PI_USER:-$DEFAULT_USER}

echo "🔧 Using user: $PI_USER"

echo "📂 Creating script directory..."
sudo mkdir -p /home/$PI_USER/piraid
sudo chown -R $PI_USER:$PI_USER /home/$PI_USER/piraid
cd /home/$PI_USER/piraid

echo "🐍 Creating Python Virtual Environment..."
sudo -u $PI_USER python3 -m venv venv

echo "🔄 Activating Virtual Environment & Installing Packages..."
sudo -u $PI_USER /home/$PI_USER/piraid/venv/bin/python -m pip install --upgrade pip
sudo -u $PI_USER /home/$PI_USER/piraid/venv/bin/python -m pip install RPLCD requests psutil

echo "💾 Downloading LCD script..."
cat <<EOF > /home/$PI_USER/piraid/lcd_display.py
#!/home/$PI_USER/piraid/venv/bin/python
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

def update_lcd(lines):
    lcd.clear()
    for row, text in enumerate(lines[:4]):
        lcd.cursor_pos = (row, 0)
        lcd.write_string(text[:20].ljust(20))

try:
    screen_index = 0

    while True:
        hostname = get_hostname()

        if screen_index == 0:
            lines = [
                f"PiRAID - {hostname}",
                f"Time: {time.strftime('%I:%M %p')}",
                f"Date: {time.strftime('%m/%d/%y')}",
                f"Uptime: {get_uptime()}"
            ]

        update_lcd(lines)
        time.sleep(SCREEN_DURATION)
        screen_index = (screen_index + 1) % 6

except KeyboardInterrupt:
    lcd.clear()
    print("Exiting...")
except Exception as e:
    lcd.clear()
    print(f"Error: {e}")
EOF

echo "🛠️ Creating systemd service..."
cat <<EOF | sudo tee /etc/systemd/system/piraid.service
[Unit]
Description=PiRAID LCD Display Service
After=multi-user.target

[Service]
Type=simple
ExecStart=/home/$PI_USER/piraid/venv/bin/python /home/$PI_USER/piraid/lcd_display.py
WorkingDirectory=/home/$PI_USER/piraid
Environment="PATH=/home/$PI_USER/piraid/venv/bin"
Restart=always
User=$PI_USER
Group=$PI_USER
ProtectSystem=full
ProtectHome=false
NoNewPrivileges=false

[Install]
WantedBy=multi-user.target
EOF

echo "🔄 Setting permissions..."
sudo chmod +x /home/$PI_USER/piraid/lcd_display.py
sudo chown -R $PI_USER:$PI_USER /home/$PI_USER/piraid

echo "🔄 Enabling and starting service..."
sudo systemctl daemon-reload
sudo systemctl enable piraid.service
sudo systemctl start piraid.service

echo "✅ Installation complete! PiRAID LCD will now run on startup."
