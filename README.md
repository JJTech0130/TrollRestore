# TrollRestore
TrollRestore is a TrollStore installer for iOS/iPadOS 15.0 - 16.7 RC (20H18) and 17.0. It will replace a system app of your choice with a TrollHelper binary, which you can then open and use to install TrollStore. TrollRestore makes use of backups in order to restore the binary to a system app container. 

A guide for installing TrollStore using TrollRestore can be found [here](https://ios.cfw.guide/installing-trollstore-trollrestore).

# Usage
To run the script, clone this repository and run the following commands:
```sh
pip install -r requirements.txt
python3 trollstore.py [system app]
```
If you're unsure about which app to use, just use Tips, like so:
```
python3 trollstore.py Tips
```

# Post-installation
TrollRestore does not restore a proper persistence helper - it simply replaces the main binary of a system app with an embedded TrollHelper. Thus, after installing TrollStore, it is recommended to install a persistence helper (you can use the same app used with TrollRestore as your persistence helper). Due to the nature of the installer (and its use of backups), the only way to restore your chosen app to it's original state is to delete it and re-install the app from the App Store.

# Version Support
As stated above, this installer supports iOS/iPadOS 15.0 - 16.7 RC (20H18) and 17.0. 

It should theoretically support iOS 14, but during our testing, we experienced issues restoring the backup to an iOS 14 device. Therefore, using TrollStore on a device below iOS 15 has been disabled for the time being.

# Need Help?
If you run into any issues during the installation, you can get support on the [r/Jailbreak Discord server](https://discord.gg/jb).

# Credits
* [JJTech](https://github.com/JJTech0130) - Sparserestore (the main library used to restore the TrollHelper binary)
* [Nathan](https://github.com/verygenericname) - Turning sparserestore into a TrollStore installer
* [Mike](https://github.com/TheMasterOfMike), [Dhinak G](https://github.com/dhinakg) - Various improvements to the installer
* [doronz88](https://github.com/doronz88) - pymobiledevice3
* [opa334](https://github.com/opa334), [Alfie](https://github.com/alfiecg24) - TrollStore
* [Aaronp613](https://x.com/aaronp613) - Minor improvements
