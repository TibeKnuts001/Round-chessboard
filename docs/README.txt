Chess Board Project - VS Code Setup & Installation
===================================================

SFTP CONFIGURATION

This project uses VS Code SFTP sync to automatically upload files to the Raspberry Pi.

1. Install VS Code Extension:
   - Open Extensions (Cmd+Shift+X)
   - Search for "SFTP" by Natizyskunk
   - Install it

2. Configure IP Address:
   - Edit .vscode/sftp.json
   - Change "host" to your Raspberry Pi's IP address
   - Change "username" if needed (default: tibe)
   - Change "remotePath" if needed (default: /home/tibe/chess)

3. Auto-Upload:
   - Files are automatically uploaded to the Pi when you save (Cmd+S)
   - Check VS Code output panel for upload status

===================================================

FIRST TIME INSTALLATION

1. Upload All Files:
   - Right-click project folder in VS Code
   - Select "SFTP: Upload Folder"
   - Wait for all files to upload

2. SSH to Raspberry Pi:
   ssh tibe@<your-pi-ip>

3. Navigate to Project:
   cd chess

4. Run Installation:
   bash install.sh
   
   This will:
   - Create Python virtual environment
   - Install all dependencies (rpi-ws281x, spidev, etc.)
   - Make run.sh and install_splash.sh executable

===================================================

CUSTOM SPLASH SCREEN (Optional)

Install a custom boot/shutdown splash screen:

1. Place your PNG in: assets/splashscreen/splash.png
   (Recommended: 1920x1080 or your screen resolution)

2. Install:
   ./install_splash.sh

3. Reboot to see:
   sudo reboot

To restore original:
   sudo cp /usr/share/plymouth/themes/pix/splash.png.backup \
           /usr/share/plymouth/themes/pix/splash.png

===================================================

RUNNING THE PROJECT

Main application:
   ./run.sh chessgame.py      (Full game with GUI)

Test scripts (in OLD/ folder):
   cd OLD
   python3 test_sensors_simple.py  (Hall sensor test)
   python3 test.py                 (LED row mapping test)
   python3 test_all_leds.py        (All LEDs 100%)
   python3 chess_sensors.py        (Sensor→LED demo)
   python3 effects.py              (LED effects)

IMPORTANT: For GUI applications (chessgame.py):
- Best: Start directly on the Pi (keyboard/VNC), not via SSH
- Via SSH: First run on the Pi itself (not via SSH):
  
  xhost +local:
  
  Then you can start via SSH with ./run.sh chessgame.py

Stop with Ctrl+C

===================================================

DEVELOPMENT WORKFLOW

1. Edit files in VS Code (local)
2. Save (Cmd+S) - files auto-upload to Pi
3. Run on Pi via SSH: ./run.sh <script.py>
4. Iterate

===================================================
