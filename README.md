# Build an offline, airgapped Chia signing device
Raspberry pi HSM (Hardware Security Module) for Chia blockchain custody solution. 
To generate keys and air-gapped sign spend bundles.

# Project Summary
Seedner offers anyone the opportunity to build a verifiably air-gapped, stateless Chia signing device using inexpensive, publicly available hardware components. 

The goal of Seedener is to make Chia custody solution more accessible to users. By providing a user interface were they can easily create, transcribe and export Keys for signing Spend Bundles which are used for custody solution. 


### Feature Highlights:
* Create Keys for custody solution
* Scan Priv Key, Encrypted Priv Key, SpendBundle
* Backup Priv Key flow 
* Export Pub Key via QR
* Export Encrypted Priv Key via QR
* Export Transcribe Priv Key via mark down QR view
* Sign Spend Bundle with Priv Keys
* Merge Spend Bundle Signed Parts
* Export Signed Spend Bundle via QR Transfer Loop
* Rekey Priv Keys

### Planned Upcoming Improvements / Functionality:
* Build a companion app to create & scan Spend Bundle QRs and send them to the blockchain
* Encrypted QRKey print via usb/TTL printer
* Add Green Pill enclosure
* Other optimizations based on user feedback!

### Considerations:
* Create a (CIC) Wallet which can manage vaults
* Calculate word 24 of a BIP39 Chia seed phrase 
* DID sign

---------------
# Shopping List

To build a Seedener, you will need:

* Raspberry Pi Zero (preferably version 1.3 with no WiFi/Bluetooth capability, but any Raspberry Pi 2/3/4, Zero or Compute 4 model will work, Raspberry Pi 1 devices will require a hardware modification to the Waveshare LCD Hat, as per the [instructions here](./docs/legacy_hardware.md))
* Waveshare 1.3" 240x240 pxl LCD (correct pixel count is important, more info at https://www.waveshare.com/wiki/1.3inch_LCD_HAT)
* Pi Zero-compatible camera (tested to work with the Aokin / AuviPal 5MP 1080p with OV5647 Sensor)

Notes:
* You will need to solder the 40 GPIO pins (20 pins per row) to the Raspberry Pi Zero board. If you don't want to solder, purchase "GPIO Hammer Headers" for a solderless experience.
* Other cameras with the above sensor module should work, but may not fit in the Green Pill enclosure
* Choose the Waveshare screen carefully; make sure to purchase the model that has a resolution of 240x240 pixels

---------------

# SeedQR Printable Templates
You can use Seedener to export your key to a hand-transcribed KeyQR format that enables you to instantly load your key back into Seedener.

[More information about KeyQRs](docs/key_qr/README.md)

Standard KeyQR templates:
* [24-word KeyQR template dots (29x29)](docs/key_qr/printable_templates/dots_29x29.pdf)
* [24-word KeyQR template grid (29x29)](docs/key_qr/printable_templates/grid_29x29.pdf)
* [24-word KeyQR template grid (29x29) fingerprint](docs/key_qr/grid_wfingerprint_21x21.pdf)

---------------

# Enclosure Designs

### Open Pill

The Open Pill enclosure design is all about quick, simple and inexpensive depoloyment of a Seedener device. The design does not require any additional hardware and can be printed using a standard FDM 3D printer in about 2 hours, no supports necessary. A video demonstrating the assembly process can be found [here](https://youtu.be/gXPFJygZobEa). To access the design file and printable model, click [here](https://github.com/MaximEdogawa/seedener/enclosures/open_pill).

### Thanks
This project is heavily inspired from the Project SeedSigner. I give many thanks to the hard work and knowledge they provided! [here] (https://github.com/SeedSigner/seedsigner)

# Manual Installation Instructions
see the docs: [Manual Installation Instructions](docs/manual_installation.md)

# Donations to
- MaximEdogawa.xch
- did:chia:1w0hjc9aja50f0895f8lj3pfvxdcp3ngl0e0yk64lz3yw34js5mvstx2cnk
