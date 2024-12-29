# On Button
This project is designed to be run on a Rasberry Pico W, an when configured can control a PROXMOX linux container (LXC) using its WEB API. 

You will need to supply it a PROXMOX API Token https://pve.proxmox.com/wiki/Proxmox_VE_API#Example:_Use_API_Token

You will need to supply your router credentials as well

## The exacts
The software so far can

- Run different functions for press and hold
- Hold is configurable
- Has spam protection that is configurable
- LED Matches PROXMOX container state for configured LXC id
- Press turns on, Hold turns off.

## Limitations
- Errors are not handled for the requests or router login
