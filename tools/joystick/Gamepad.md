# Gamepad controls

## Rebuild the kernel with Bluetooth

Follow the [AGNOS builder](https://github.com/commaai/agnos-builder) instructions and apply [jyoung8607's kernel patch](https://github.com/jyoung8607/agnos-kernel-sdm845/commit/abef069644673fb19d6837eb10a234bb5fdf5875). This enables Bluetooth modules and switches the order of UART devices.

## Install Bluetooth userspace

```
sudo apt update
sudo apt install bluez
sudo systemctl enable bluetooth
```

Remount the read-only file system for editing. It will be re-locked on reboot. There is an issue with the systemd Bluetooth target, so we will move the service to multi-user.target instead:
```
sudo mount -o rw,remount /
cd /etc/systemd/system
sudo mv bluetooth.target.wants/bluetooth.service multi-user.target.wants/
sudo vim multi-user.target.wants/bluetooth.service
```

Change the systemd target dependency:
```
--- WantedBy=bluetooth.target
+++ WantedBy=multi-user.target
```

Restart the comma three:
```
sudo reboot now
```

Check that Bluetooth is working:
```
systemctl status bluetooth
dmesg | grep Bluetooth
```

joystickd's gamepad controls depend on the [PiBorg Gamepad Library](https://github.com/piborg/Gamepad):

```
cd /data/openpilot/tools/joystick
git clone https://github.com/piborg/Gamepad
cp Gamepad/Gamepad.py .
cp Gamepad/Controllers.py .
```

## Connecting a Gamepad

The device should be /dev/ttyHS1. Attach the device to bluez:
```
sudo hciattach /dev/ttyHS1 any 115200 flow
```

```
bluetoothctl
> list
> select <comma BT MAC>
> agent DisplayYesNo
> default-agent
> scan on
```
Wait for a discoverable device to appear, or:
```
> devices
> connect <device MAC>
[enter pin - PS4 Controller is 0000]
> trust <device MAC>
> pair <device MAC> (May fail if paired already)
```

## Running with joystickd

```
./joystickd --input gamepad &
```

Enable car mode, and start driving!

## Troubleshooting

These instructions were tested with a PlayStation 4 controller (PIN: 0000). There is an intermittent issue where a baud rate change is corrupted. It has been addressed with [several patches](https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/log/drivers/bluetooth/hci_qca.c?h=v6.0.1), and [was eventually root caused in the UART driver:](https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/commit/drivers/bluetooth/hci_qca.c?h=v6.0.1&id=bba79fee7a54ff5351fa36cb324d16b108a7ca06)

If this issue occurs, you have trouble pairing, or you see messages like:
```
Frame reassembly failed (-84)
```
Fully power off the device, wait 1 minute, and power the device back on.

