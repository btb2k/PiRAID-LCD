**SCRIPT INSTALLATION using install_piraid.sh script  -- SEE BELOW FOR MANUAL INSTALLATION** 

🚀 How to Run This Installer

1️⃣ Save the script

bash
Copy
nano install_piraid.sh
Paste the script inside the file, then save (CTRL + X, Y, ENTER).

2️⃣ Make It Executable

bash
Copy
chmod +x install_piraid.sh
3️⃣ Run the Installer

bash
Copy
./install_piraid.sh

**MANUAL Installation:**

1️⃣ Install System Dependencies
bash
Copy
sudo apt update && sudo apt install -y python3 python3-pip python3-venv i2c-tools

2️⃣ Create a Virtual Environment for PiRAID
bash
Copy
mkdir -p /home/pi/piraid
cd /home/pi/piraid
python3 -m venv venv  # ✅ Create the virtual environment

3️⃣ Activate the Virtual Environment
bash
Copy
source venv/bin/activate

4️⃣ Upgrade pip and Install Required Packages
bash
Copy
venv/bin/python -m pip install --upgrade pip
venv/bin/python -m pip install RPLCD requests psutil

5️⃣ Copy the LCD Script
bash
Copy
cp /path/to/lcd_display.py /home/pi/piraid/lcd_display.py
chmod +x /home/pi/piraid/lcd_display.py
chown pi:pi /home/pi/piraid/lcd_display.py

6️⃣ Create the Systemd Service File
bash
Copy
sudo nano /etc/systemd/system/piraid.service
Paste the following:

ini
Copy
[Unit]
Description=PiRAID LCD Display Service
After=multi-user.target

[Service]
Type=simple
ExecStart=/home/pi/piraid/venv/bin/python /home/pi/piraid/lcd_display.py
WorkingDirectory=/home/pi/piraid
Environment="PATH=/home/pi/piraid/venv/bin"
Restart=always
User=pi
Group=pi
ProtectSystem=full
ProtectHome=false
NoNewPrivileges=false

[Install]
WantedBy=multi-user.target
Save and exit (CTRL + X, then Y, then ENTER).

🚀 Running & Managing the Service
1️⃣ Enable & Start the Service
bash
Copy
sudo systemctl daemon-reload
sudo systemctl enable piraid.service
sudo systemctl start piraid.service
2️⃣ Check Service Status
bash
Copy
sudo systemctl status piraid.service
If everything is correct, you should see "active (running)".

🐛 Troubleshooting
1️⃣ Activate the Virtual Environment Manually
If the service isn't running, activate the environment manually and test:

bash
Copy
source /home/pi/piraid/venv/bin/activate
python /home/pi/piraid/lcd_display.py
If errors occur, check dependencies.

2️⃣ Check Logs for Errors
bash
Copy
journalctl -u piraid.service --no-pager --lines=30
🎉 Now Fully Using a Virtual Environment!
Your PiRAID LCD service now installs and runs correctly in a Python virtual environment for better dependency management. 🚀

Let me know if you need any refinements! 😃
