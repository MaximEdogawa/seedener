# Manual Installation Instructions
### Install dependencies
```
sudo apt-get update && sudo apt-get install build-essential libcap-dev python3-pip python3-venv python3 git
```
### Setup a virtual environment
```
python3 -m venv venv --system-site-packages
source /venv/bin/activate
```

### Install Python `pip` dependencies:
```
pip install -r requirements.txt
```

### Configure `systemd` to run SeedSigner at boot:
```
sudo nano /etc/systemd/system/seedsigner.service
```

## Disable wifi/Bluetooth when using other Raspi boards
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

You can now safely power the Raspberry Pi off from the SeedSigner main menu.

If you do not plan to use your installation for testing/development, it is also a good idea to disable WiFi and Bluetooth by editing the config.txt file found in the installation's "boot" partition. You can add the following text to the end of that file with any simple text editor (Windows: Notepad, Mac: TextEdit, Linux: nano):
```
dtoverlay=disable-bt
dtoverlay=pi3-disable-wifi
```
