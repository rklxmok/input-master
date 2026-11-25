# Input Master

A Linux mouse macro and button remapping tool with a system tray interface. Built with Python, CustomTkinter, and evdev.

Input Master captures your physical mouse, creates a virtual mouse device, and lets you remap extra mouse buttons and configure click macros -- all from a clean dark-mode GUI that lives in your system tray.

## Features

- **Extra Mouse Button Remapping** -- Map Mouse Button 4 (Side) and Button 5 (Extra) to any keyboard key, modifier, or disable them entirely
- **Burst Fire Mode** -- Trigger rapid click bursts after a configurable number of clicks within a time window
- **Hold Fire Mode** -- Automatically repeat clicks while holding the left mouse button
- **Global Toggle Hotkey** -- Enable/disable macros with a configurable keyboard shortcut (e.g. Super+Numpad7)
- **System Tray Integration** -- Starts minimized to tray, color-coded icon shows engine status (white=off, blue=active, red=disabled)
- **Audio Notifications** -- Plays sounds when engine starts/stops or macros are toggled (works on both X11 and Wayland)
- **Per-User Config** -- Settings saved to `~/.config/input-master/config.json`
- **No Root Required at Runtime** -- Install script sets up proper permissions via udev rules and the `input` group

## Requirements

- Linux with X11 or Wayland
- Python 3.10+
- A desktop environment with system tray support

## Installation

Clone the repo and run the installer:

```bash
git clone https://github.com/rklxmok/input-master.git
cd input-master
sudo ./install.sh
```

The installer handles everything:

1. Installs system packages (auto-detects `pacman`, `apt`, or `dnf`)
2. Creates a Python virtual environment at `/opt/input-master/`
3. Installs Python dependencies (`customtkinter`, `evdev`, `pystray`, `pillow`)
4. Adds your user to the `input` group
5. Creates udev rules for `/dev/uinput` access (no root needed at runtime)
6. Creates a desktop entry and autostart file

**After installing, log out and back in** for the `input` group membership to take effect.

## Usage

Launch from your application menu or run:

```bash
input-master
```

The app starts in the system tray. Right-click the tray icon for options:

- **Show** -- Open the configuration window
- **Start Engine** -- Start/stop the macro engine
- **Quit** -- Exit the application

### Configuration

1. Select your **Mouse Device** and **Toggle Keyboard** from the dropdowns
2. Set a **Global Toggle Hotkey** (modifier + key) to enable/disable macros on the fly
3. Configure **Extra Mouse Button Mapping** -- choose what Button 4 and Button 5 do
4. Optionally enable **Burst Mode** and/or **Hold Mode** with your preferred settings
5. Click **START ENGINE** -- your mouse is now captured and remapped through the virtual device

Closing the window hides it to the tray. The engine keeps running.

### Tray Icon States

| Icon Color | Meaning |
|---|---|
| White | Engine not running |
| Blue | Engine running, macros enabled |
| Red | Engine running, macros disabled (toggled off) |

## How It Works

Input Master uses Linux's `evdev` subsystem to grab exclusive access to your physical mouse, then creates a virtual mouse (`UInput`) to replay events. Extra button presses are intercepted and remapped before being forwarded to the virtual device. This approach works at the kernel input level, so it's desktop-environment agnostic.

## Uninstall

```bash
sudo rm -rf /opt/input-master
sudo rm /usr/local/bin/input-master
sudo rm /usr/share/applications/input-master.desktop
rm ~/.config/autostart/input-master.desktop
sudo rm /etc/udev/rules.d/99-input-master-uinput.rules
sudo rm /etc/udev/rules.d/99-input-master-evdev.rules
```

## License

MIT
