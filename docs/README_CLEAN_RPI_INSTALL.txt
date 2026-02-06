Clean Raspberry Pi Installation Guide

==============================================

1. Flash OS with Raspberry Pi Imager

1. Download and open Raspberry Pi Imager
2. Select Raspberry Pi OS (64-bit) as the operating system
3. Click Settings (gear icon) and configure:
   - Hostname: Chess1 (or your preferred name)
   - Location: Brussels, Belgium
   - Timezone: Europe/Brussels
   - Keyboard layout: Belgian (BE)
   - Username and Password: Choose your credentials
   - WiFi: Enable and enter SSID + Password
   - SSH: Enable with "Use password authentication"
   - Raspberry Pi Connect: Keep disabled
4. Click Write and wait for completion

==============================================

2. Configure Display Settings

After flashing, the SD card will be ejected on macOS.

1. Re-insert the SD card into your Mac
2. Open config.txt in the root of the SD card:
   
   sudo nano -w /Volumes/bootfs/config.txt

3. Find the line (usually first): dtoverlay=vc4-kms-v3d
4. Add BELOW it:
   
   dtoverlay=vc4-kms-dsi-7inch

5. Save and close (Ctrl+X, Y, Enter)

Note: Leave the [cm5] section untouched - it's for CM5 modules only.

==============================================

3. First Boot

1. Eject the SD card and insert it into your Raspberry Pi
2. Power on the Pi
3. IMPORTANT: The Pi will auto-restart after the first graphical display appears - this is normal
4. Wait for the second boot to complete

==============================================

4. Update System

After first boot, connect via SSH and update the system:

   sudo apt update
   sudo apt dist-upgrade

Note: dist-upgrade can take a while, be patient.

==============================================

5. Troubleshooting

If you get locale errors when logging in via SSH:

   -bash: warning: setlocale: LC_CTYPE: cannot change locale (UTF-8): No such file or directory

Fix it by editing SSH config:

   sudo nano /etc/ssh/sshd_config

Find the line:
   AcceptEnv LANG LC_* COLORTERM NO_COLOR

Replace it with:
   AcceptEnv LANG COLORTERM NO_COLOR

Save (Ctrl+X, Y, Enter) and restart SSH:

   sudo systemctl restart sshd

==============================================

Your Raspberry Pi is now ready!
