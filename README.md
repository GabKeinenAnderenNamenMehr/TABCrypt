# TABCrypt
This is a (vibecoded) helper tool for modding the game They are Billions that can decrypt and encrypt ZXRules, ZXStrings, ZXCampaign and ZXCampaignStrings with a simple drag and drop. Speeds up the process of testing changes made to those files.

## Installation and Setup

There are 2 Versions available:

### Version 1 (executable)

A single executable that only needs 7-Zip to be installed on your device. Made for Windows 10/11. No installation needed if you already have 7-Zip.
1. Download and install 7-Zip from the [official website](https://www.7-zip.org/) if you don't already have it installed.
2. Download the executable from here or [Nexusmods](https://www.nexusmods.com/theyarebillions/mods/45).
3. Run the executable. Windows Defender will most likely protest, because this is an unsigned executable from a different device. 
4. Decide if you want to trust a random stranger on the internet
5. The app will try to locate 7-Zip (7z.exe) by checking the default installation paths. If it cannot find the .exe there, you should be prompted to add the path manually. I did not check if this part works, because I have 7-Zip installed in the default location.
6. If you have TAB on Steam version 1.0.14 you can skip this step: Go to Settings -> Passwords and change the default passwords to the correct ones for the game version you are using. Every game version has it's own passwords for the files. Here is a guide on how to find the passwords: https://github.com/quasart-zz/mods-theyAreBillions-EasyMode

### Version 2 (python project)

This is the .py file the executable was build from. Requires python 3 and the tkinterdnd2 pakage to be installed on your device as well as 7-Zip.
1. Download and install 7-Zip from the [official website](https://www.7-zip.org/) if you don't already have it installed.
2. Download and install Python (I used version 3.13) from the [official website](https://www.python.org/) or the windows store if not already installed on your device.
3. Install tkinterdnd2 (python extension that allows for drag&drop). You can do so by opening cmd and running the following command:
`pip install tkinterdnd2`
4. Download the .py file from here or [Nexusmods](https://www.nexusmods.com/theyarebillions/mods/45).
5. You should now be able to run the app by double clicking the .py file.
6. The app will try to locate 7-Zip (7z.exe) by checking the default installation paths. If it cannot find the .exe there, you should be prompted to add the path manually. I did not check if this part works, because I have 7-Zip installed in the default location.
7. If you have TAB on Steam version 1.0.14 you can skip this step: Go to Settings -> Passwords and change the default passwords to the correct ones for the game version you are using. Every game version has it's own passwords for the files. Here is a guide on how to find the passwords: https://github.com/quasart-zz/mods-theyAreBillions-EasyMode


***You should now be ready to go. Just drag&drop any of the ZXxyz.dat files onto the marked area and the app will work it's magic!***

## How to use
The App does 2 things:

### Unpacking/Decrypting
When you drop an encrypted ZX.dat file from the game on it, the app will recognize it as encrypted and try to determin the password it needs to use via the filename. The file will then be decrypted if a correct password is set in the settings and you will recieve an unlocked file. If the checkbox below the drag&drop field is checked (on by default), the original encrypted archive will be deleted as well (as it's usually not needed anymore). The app will try to avoid naming conflicts to not overwrite existing files if the checkbox is unchecked.

### Packaging/Re-encrypting
When you drop an unencrypted ZX.dat file from the game on it, the app will recognize it as unencrypted and try to determin the password it needs to use via the filename. As long as any password is set for this filename, it will be put into an encrypted archive with the correct archiving properties and said password. It will also first rename the file to the proper vanilla name (e.g. ZXRules.dat) if you added anything to it and change the resulting .zip archive to .dat. Caution: It will overwrite existing files with the same vanilla name if present in the same location as the file you just dropped onto the app.

***Important note: The app auto recognizes which ZX.dat file you dropped by it's name. Due to this, the filename HAS to start with the original name. You can add anything after, such as _test or _version2 (e.g. ZXRules_test.dat), the app will still work. Only the name and extension need to be correct. This is due to the fact that only ZXRules and ZXStrings share a password, the other two have unique ones and the app needs to know which password to apply.***
