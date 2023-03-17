# Manual Installation Instructions
# Manual Installation Instructions

Begin by acquiring a specific copy of the Raspberry Pi Lite operating system, dated 2022-09-26; this version can be found here:

For 32-bit Raspberry pi Zero 1.3
https://downloads.raspberrypi.org/raspios_lite_armhf/images/raspios_lite_armhf-2022-09-26/

For 64-bit Raspberry pi 4, Compute 4, Zero 2 W
https://downloads.raspberrypi.org/raspios_lite_arm64/images/raspios_lite_arm64-2022-09-26/


Best practice is to verify the downloaded .zip file containing the Raspberry Pi Lite OS matches the published SHA256 hash of the file; for additional reference that hash for 32-bit os lite is: 9bf5234efbadd2d39769486e0a20923d8526a45eba57f74cda45ef78e2b628da.  After verifying the file's data integrity, you can decompress the .zip file to obtain the operating system image that it contains. You can then use Balena's Etcher tool (https://www.balena.io/etcher/) to write the Raspberry Pi Lite software image to a memory card (4 GB or larger). It's important to note that an image authoring tool must be used (the operating system image cannot be simply copied into a file storage partition on the memory card).

The manual Seedener installation and configuration process requires an internet connection on the device to download the necessary libraries and code. But because the Pi Zero 1.3 does not have onboard wifi, you have two options:

1. Run these steps on a separate Raspberry Pi 2/3/4 or Zero W which can connect to the internet and then transfer the SD card to the Pi Zero 1.3 when complete.
2. OR configure the Pi Zero 1.3 directly by relaying through your computer's internet connection over USB. See instructions [here](usb_relay.md).

For the following steps you'll need to either connect a keyboard & monitor to the network-connected Raspberry Pi you are working with, or SSH into the Pi if you're familiar with that process.

### Configure the Pi
First things first, verify that you are using the correct version of the Raspberry Pi Lite operating system by typing the command:
```
cat /etc/os-release
```
The output of this command should match the following text:
```
PRETTY_NAME="Raspbian GNU/Linux 11 (bullseye)"
NAME="Raspbian GNU/Linux"
VERSION_ID="11"
VERSION="11 (bullseye)"
VERSION_CODENAME=bullseye
ID=raspbian
ID_LIKE=debian
HOME_URL="http://www.raspbian.org/"
SUPPORT_URL="http://www.raspbian.org/RaspbianForums"
BUG_REPORT_URL="http://www.raspbian.org/RaspbianBugs"
```

Now launch the Raspberry Pi's System Configuration tool using the command:
```
sudo raspi-config
```

Set the following:
* `Interface Options`:
    * `Camera`: enable
    * `SPI`: enable
* `Localisation Options`:
    * `Locale`: arrow up and down through the list and select or deselect languages with the spacebar.
        * Deselect the default language option that is selected
        * Select `en_US.UTF-8 UTF-8` for US English
* You will also need to configure the WiFi settings if you are using the #1 option above to connect to the internet

When you exit the System Configuration tool, you will be prompted to reboot the system; allow the system to reboot and continue with these instructions.


### Change the default password
Change the system's default password from the default "raspberry". Run the command:
```
passwd
```

### Install dependencies
```
sudo apt-get update && sudo apt-get install build-essential python3 python3-wheel python3-pip python3-venv python3-opencv git cmake zbar-tools libssl-dev libcap-dev libatlas-base-dev qrencode
```
### Install Rust
```
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

### Download the Seedener code:
```
git clone https://github.com/MaximEdogawa/seedener.git
cd seedener
```

If you want to run a specific branch within the main Seedener repo, switch to it with:
```
git checkout yourtargetbranch
```

### Setup a virtual environment
64-bit version for libcamera (Only system site packages)
```
python3 -m venv venv --system-site-packages
source venv/bin/activate
```

32-bit version
```
python3 -m venv venv
source venv/bin/activate
```

### Install Python `pip` dependencies:
64-bit version ( with picamera2)
```
pip install -r requirements.txt
```

32-bit version (with picamera)
```
pip install -r requirements_zero.txt
```
Notice that it can take a long time to build blspy==1.0.14 and clvm_tools_rs==0.1.22 in rust & c on raspberry pi zero. Build it seperatly if you have problems. I could take hours to build!

### Configure `systemd` to run Seedener at boot:
```
sudo nano /etc/systemd/system/seedener.service
```

### Configure Spi and Camera for Raspberry pi 4 and Compute
Add this to lines on the end of /boot/config.txt
```
#Enable usb dongle
dtoverlay=dwc2
```
```
#spi connect
dtoverlay=spi0-hw-cs
```
```
#camera connect
dtoverlay=ov5647
```
Now we have some incomprehensible configuration steps to set up the internet access relay.

Edit `config.txt`:
```
# mac/Linux:
nano config.txt

# Windows:
notepad config.txt
```
Add `dtoverlay=dwc2` to the end of `config.txt`. Exit and save changes (CTRL-X, then "y" in nano).
```
blah blah rootwait modules-load=dwc2,g_ether [possibly more blah]
```
Enable ssh
```
sudo touch /boot/ssh
```

### Configure 'systemd' to run Seedener at boot:
Open new seedener.service file
```
sudo nano /etc/systemd/system/seedener.service
```
Add this line to it. Remember to change lines with your project directory
```
[Unit]
Description=Seedener

[Service]
User=pi
Group=pi
NOPASSWD:/usr/bin/systemctl restart seedener
NOPASSWD:/sbin/shutdown
Environment="PATH=/home/pi/seedener/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
WorkingDirectory=/home/pi/seedener/src/
ExecStart=/home/pi/seedener/venv/bin/python3 main.py > /dev/null 2>&1
Restart=always

[Install]
WantedBy=multi-user.target
```

Note: For local dev you'll want to edit the Restart=always line to Restart=no. This way when your dev code crashes it won't keep trying to restart itself. Note that the UI "Reset" will no longer work when auto-restarts are disabled.

Note: Debugging output is completely wiped via routing the output to /dev/null 2>&1. When working in local dev, you're better off disabling the systemd SeedSigner service and just directly running the app so you can see all the debugging output live.

Use `CTRL-X` and `y` to exit and save changes.

Configure the service to start running (this will restart the seedsigner code automatically at startup and if it crashes):
```
sudo systemctl enable seedener.service
```

Now reboot the Raspberry Pi:
```
sudo reboot
```

After the Raspberry Pi reboots, you should see the Seedener splash screen and the Seedener menu subsequently appear on the LCD screen (note that it can take up to 60 seconds for the menu to appear).

## Disable wifi/Bluetooth when using other Raspi boards# Manual Installation Instructions
If you plan to use your installation on a Raspberry Pi that is not a Zero version 1.3, but rather on a Raspberry Pi that has WiFi and Bluetooth capabilities, it is a good idea to disable the following WiFi & Bluetooth, as well as other relevant services (assuming you are not creating this installation for testing/development purposes). Enter the followiing commands to disable WiFi, Bluetooth, & other relevant services:
```
sudo systemctl disable bluetooth.service
sudo systemctl disable wpa_supplicant.service
sudo systemctl disable dhcpcd.service
sudo systemctl disable sshd.service
sudo systemctl disable networking.service
sudo systemctl disable dphys-swapfile.service
sudo ifconfig wlan0 down
```
Please note that if you are using WiFi to connect/interact with your Raspberry Pi, the last command will sever that connection.

You can now safely power the Raspberry Pi off from the Seedener main menu.

If you do not plan to use your installation for testing/development, it is also a good idea to disable WiFi and Bluetooth by editing the config.txt file found in the installation's "boot" partition. You can add the following text to the end of that file with any simple text editor (Windows: Notepad, Mac: TextEdit, Linux: nano):
```
dtoverlay=disable-bt
dtoverlay=pi3-disable-wifi
```
