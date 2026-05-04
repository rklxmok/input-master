import customtkinter as ctk
import evdev
from evdev import ecodes, UInput
import threading
import time
import sys
import random
import os
import json
import wave
import struct
import subprocess
import shutil
import math
from PIL import Image, ImageTk
import pystray
from pystray import MenuItem, Menu


# --- KEYBOARD MAPPING (for toggle hotkey) ---
KEY_MAP = {
    "NUMPAD 7": ecodes.KEY_KP7, "NUMPAD 8": ecodes.KEY_KP8, "NUMPAD 9": ecodes.KEY_KP9,
    "NUMPAD 4": ecodes.KEY_KP4, "NUMPAD 5": ecodes.KEY_KP5, "NUMPAD 6": ecodes.KEY_KP6,
    "NUMPAD 1": ecodes.KEY_KP1, "NUMPAD 2": ecodes.KEY_KP2, "NUMPAD 3": ecodes.KEY_KP3,
    "NUMPAD 0": ecodes.KEY_KP0,
    "F1": ecodes.KEY_F1, "F2": ecodes.KEY_F2, "F3": ecodes.KEY_F3, "F4": ecodes.KEY_F4,
    "F5": ecodes.KEY_F5, "F6": ecodes.KEY_F6, "F7": ecodes.KEY_F7, "F8": ecodes.KEY_F8,
    "F9": ecodes.KEY_F9, "F10": ecodes.KEY_F10, "F11": ecodes.KEY_F11, "F12": ecodes.KEY_F12,
    "A": ecodes.KEY_A, "B": ecodes.KEY_B, "C": ecodes.KEY_C, "D": ecodes.KEY_D,
    "X": ecodes.KEY_X, "Y": ecodes.KEY_Y, "Z": ecodes.KEY_Z,
    "CAPS LOCK": ecodes.KEY_CAPSLOCK, "TAB": ecodes.KEY_TAB,
    "ESC": ecodes.KEY_ESC
}

# --- REMAP KEY MAP (for extra mouse button mapping) ---
REMAP_KEY_MAP = {
    "Pass Through": "PASSTHROUGH",
    "Disabled": None,
    # Modifiers
    "Left Alt": ecodes.KEY_LEFTALT,
    "Right Alt": ecodes.KEY_RIGHTALT,
    "Left Ctrl": ecodes.KEY_LEFTCTRL,
    "Right Ctrl": ecodes.KEY_RIGHTCTRL,
    "Left Shift": ecodes.KEY_LEFTSHIFT,
    "Right Shift": ecodes.KEY_RIGHTSHIFT,
    "Super (Win)": ecodes.KEY_LEFTMETA,
    # Letters
    "A": ecodes.KEY_A, "B": ecodes.KEY_B, "C": ecodes.KEY_C, "D": ecodes.KEY_D,
    "E": ecodes.KEY_E, "F": ecodes.KEY_F, "G": ecodes.KEY_G, "H": ecodes.KEY_H,
    "I": ecodes.KEY_I, "J": ecodes.KEY_J, "K": ecodes.KEY_K, "L": ecodes.KEY_L,
    "M": ecodes.KEY_M, "N": ecodes.KEY_N, "O": ecodes.KEY_O, "P": ecodes.KEY_P,
    "Q": ecodes.KEY_Q, "R": ecodes.KEY_R, "S": ecodes.KEY_S, "T": ecodes.KEY_T,
    "U": ecodes.KEY_U, "V": ecodes.KEY_V, "W": ecodes.KEY_W, "X": ecodes.KEY_X,
    "Y": ecodes.KEY_Y, "Z": ecodes.KEY_Z,
    # Numbers
    "1": ecodes.KEY_1, "2": ecodes.KEY_2, "3": ecodes.KEY_3, "4": ecodes.KEY_4,
    "5": ecodes.KEY_5, "6": ecodes.KEY_6, "7": ecodes.KEY_7, "8": ecodes.KEY_8,
    "9": ecodes.KEY_9, "0": ecodes.KEY_0,
    # F-keys
    "F1": ecodes.KEY_F1, "F2": ecodes.KEY_F2, "F3": ecodes.KEY_F3, "F4": ecodes.KEY_F4,
    "F5": ecodes.KEY_F5, "F6": ecodes.KEY_F6, "F7": ecodes.KEY_F7, "F8": ecodes.KEY_F8,
    "F9": ecodes.KEY_F9, "F10": ecodes.KEY_F10, "F11": ecodes.KEY_F11, "F12": ecodes.KEY_F12,
    # Common keys
    "Space": ecodes.KEY_SPACE, "Enter": ecodes.KEY_ENTER, "Tab": ecodes.KEY_TAB,
    "Escape": ecodes.KEY_ESC, "Backspace": ecodes.KEY_BACKSPACE,
    "Delete": ecodes.KEY_DELETE, "Insert": ecodes.KEY_INSERT,
    # Navigation
    "Home": ecodes.KEY_HOME, "End": ecodes.KEY_END,
    "Page Up": ecodes.KEY_PAGEUP, "Page Down": ecodes.KEY_PAGEDOWN,
    "Up": ecodes.KEY_UP, "Down": ecodes.KEY_DOWN,
    "Left Arrow": ecodes.KEY_LEFT, "Right Arrow": ecodes.KEY_RIGHT,
}

# --- CONFIG DEFAULTS ---
DEFAULT_CONFIG = {
    "mouse_name": "Mouse",
    "keyboard_name": "Keyboard",
    "toggle_modifier": "SUPER",
    "toggle_key": "NUMPAD 7",
    "enable_burst": False,
    "enable_hold": False,
    "trigger_clicks": 5,
    "trigger_window": 1.0,
    "burst_count": 10,
    "burst_duration": 1.0,
    "hold_delay": 0.2,
    "hold_rate": 0.1,
    "btn_side_map": "X",
    "btn_extra_map": "Left Alt"
}

# --- CONFIG PATH (User-level) ---
CONFIG_DIR = os.path.expanduser("~/.config/input-master")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

# --- AUDIO PATH ---
AUDIO_DIR = os.path.join(CONFIG_DIR, "audio")
BEEP_ON_FILE = os.path.join(AUDIO_DIR, "beep-on.wav")
BEEP_OFF_FILE = os.path.join(AUDIO_DIR, "beep-off.wav")


def _generate_sine_beep(filepath, frequency=2400, duration_ms=120, volume=0.5, double=False):
    sample_rate = 44100
    if double:
        gap_ms = 80
        total_ms = duration_ms * 2 + gap_ms
        num_samples = int(sample_rate * total_ms / 1000)
    else:
        total_ms = duration_ms
        num_samples = int(sample_rate * duration_ms / 1000)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        if double:
            beep1_end = int(sample_rate * duration_ms / 1000)
            beep2_start = int(sample_rate * (duration_ms + gap_ms) / 1000)
            if i < beep1_end:
                local_i = i
                local_dur = beep1_end
            elif i >= beep2_start:
                local_i = i - beep2_start
                local_dur = num_samples - beep2_start
            else:
                samples.append(struct.pack("<h", 0))
                continue
        else:
            local_i = i
            local_dur = num_samples
        envelope = 1.0
        fade_len = int(sample_rate * 0.005)
        if local_i < fade_len:
            envelope = local_i / fade_len
        elif local_i > local_dur - fade_len:
            envelope = (local_dur - local_i) / fade_len
        sine_val = math.sin(2 * math.pi * frequency * t)
        raw = int(volume * 32767 * sine_val)
        clamped = max(-32768, min(32767, raw))
        samples.append(struct.pack("<h", int(envelope * clamped)))
    with wave.open(filepath, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"".join(samples))


def _ensure_beep_files():
    os.makedirs(AUDIO_DIR, exist_ok=True)
    if not os.path.exists(BEEP_ON_FILE):
        _generate_sine_beep(BEEP_ON_FILE, frequency=2400, duration_ms=120, double=True)
    if not os.path.exists(BEEP_OFF_FILE):
        _generate_sine_beep(BEEP_OFF_FILE, frequency=1800, duration_ms=120, double=False)


AUDIO_PLAYERS = [
    "/usr/bin/paplay",
    "/usr/bin/aplay",
    "/usr/bin/canberra-gtk-play",
]

def _find_player():
    for p in AUDIO_PLAYERS:
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    for player in ("paplay", "aplay", "canberra-gtk-play"):
        found = shutil.which(player)
        if found:
            return found
    return None


def _play_beep(filepath):
    try:
        cmd = _find_player()
        if not cmd:
            return
        if cmd.endswith("paplay"):
            subprocess.Popen([cmd, filepath], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif cmd.endswith("aplay"):
            subprocess.Popen([cmd, "-q", filepath], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif cmd.endswith("canberra-gtk-play"):
            subprocess.Popen([cmd, "-f", filepath], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

# Collect all possible remap keycodes for UInput capabilities
_REMAP_KEYCODES = list(set(v for v in REMAP_KEY_MAP.values() if isinstance(v, int)))

class MacroBackend:
    def __init__(self):
        self.running = False
        self.stop_event = threading.Event()
        self.thread = None
        self.config = DEFAULT_CONFIG.copy()
        self.physical_left_down = False
        self.firing_burst = False
        self.click_timestamps = []
        self.macro_enabled_toggle = True
        self.meta_held = False
        self.mod_ctrl = False
        self.mod_alt = False

    def update_config(self, new_config):
        self.config = new_config

    def start(self):
        if self.running: return
        self.stop_event.clear()
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        print(">>> ENGINE STARTED")
        threading.Thread(target=_play_beep, args=(BEEP_ON_FILE,), daemon=True).start()

    def stop(self):
        if not self.running: return
        self.stop_event.set()
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        print(">>> ENGINE STOPPED")
        threading.Thread(target=_play_beep, args=(BEEP_OFF_FILE,), daemon=True).start()

    def _get_device(self, name_fragment, capability=None):
        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        for dev in devices:
            if name_fragment.lower() in dev.name.lower():
                if capability:
                    if capability in dev.capabilities().get(ecodes.EV_KEY, []):
                        return dev
                else:
                    return dev
        return None

    def _burst_fire(self, vmouse):
        self.firing_burst = True
        time.sleep(0.2)
        count = int(self.config["burst_count"])
        duration = float(self.config["burst_duration"])
        min_hold = 0.04
        base_delay = (duration / count) - min_hold

        for _ in range(count):
            if not self.firing_burst or not self.macro_enabled_toggle: break
            hold = random.uniform(min_hold, min_hold + 0.02)
            wait = random.uniform(base_delay * 0.9, base_delay * 1.1)
            vmouse.write(ecodes.EV_KEY, ecodes.BTN_LEFT, 1)
            vmouse.syn()
            time.sleep(hold)
            vmouse.write(ecodes.EV_KEY, ecodes.BTN_LEFT, 0)
            vmouse.syn()
            time.sleep(wait)
        self.click_timestamps.clear()
        self.firing_burst = False

    def _hold_fire(self, vmouse):
        delay = float(self.config["hold_delay"])
        rate = float(self.config["hold_rate"])
        time.sleep(delay)
        while self.physical_left_down and self.config["enable_hold"] and self.macro_enabled_toggle and not self.firing_burst:
            if self.stop_event.is_set(): break
            vmouse.write(ecodes.EV_KEY, ecodes.BTN_LEFT, 0)
            vmouse.syn()
            time.sleep(rate / 2)
            vmouse.write(ecodes.EV_KEY, ecodes.BTN_LEFT, 1)
            vmouse.syn()
            time.sleep(rate / 2)
        vmouse.write(ecodes.EV_KEY, ecodes.BTN_LEFT, 0)
        vmouse.syn()

    def _keyboard_listener(self):
        target_key_name = self.config.get("toggle_key", "NUMPAD 7")
        target_code = KEY_MAP.get(target_key_name, ecodes.KEY_KP7)
        target_mod = self.config.get("toggle_modifier", "SUPER")

        kb = self._get_device(self.config["keyboard_name"], target_code)
        if not kb:
            kb = self._get_device(self.config["keyboard_name"], ecodes.KEY_ESC)

        if not kb:
            print("Keyboard not found for toggle listener.")
            return

        print(f"Listening for Toggle [{target_mod} + {target_key_name}] on {kb.name}")

        try:
            for event in kb.read_loop():
                if self.stop_event.is_set(): break
                if event.type == ecodes.EV_KEY:
                    if event.code in [ecodes.KEY_LEFTMETA, ecodes.KEY_RIGHTMETA]:
                        self.meta_held = (event.value == 1 or event.value == 2)
                    elif event.code in [ecodes.KEY_LEFTCTRL, ecodes.KEY_RIGHTCTRL]:
                        self.mod_ctrl = (event.value == 1 or event.value == 2)
                    elif event.code in [ecodes.KEY_LEFTALT, ecodes.KEY_RIGHTALT]:
                        self.mod_alt = (event.value == 1 or event.value == 2)

                    if event.code == target_code and event.value == 1:
                        authorized = False
                        if target_mod == "SUPER" and self.meta_held: authorized = True
                        elif target_mod == "CTRL" and self.mod_ctrl: authorized = True
                        elif target_mod == "ALT" and self.mod_alt: authorized = True
                        elif target_mod == "NONE": authorized = True

                        if authorized:
                            self.macro_enabled_toggle = not self.macro_enabled_toggle
                            state = "ENABLED" if self.macro_enabled_toggle else "DISABLED"
                            print(f">>> KEY SHORTCUT: Macros {state}")
                            sound = BEEP_ON_FILE if self.macro_enabled_toggle else BEEP_OFF_FILE
                            threading.Thread(target=_play_beep, args=(sound,), daemon=True).start()
        except: pass

    def _run_loop(self):
        mouse = self._get_device(self.config["mouse_name"], ecodes.BTN_LEFT)
        if not mouse:
            print(f"ERROR: Mouse '{self.config['mouse_name']}' not found.")
            self.running = False
            return
        print(f"Captured: {mouse.name}")
        threading.Thread(target=self._keyboard_listener, daemon=True).start()

        # Resolve remap targets from config
        side_target = REMAP_KEY_MAP.get(self.config.get("btn_side_map", "Pass Through"), "PASSTHROUGH")
        extra_target = REMAP_KEY_MAP.get(self.config.get("btn_extra_map", "Pass Through"), "PASSTHROUGH")

        side_label = self.config.get("btn_side_map", "Pass Through")
        extra_label = self.config.get("btn_extra_map", "Pass Through")
        print(f"Mouse Button 4 (Side) -> {side_label}")
        print(f"Mouse Button 5 (Extra) -> {extra_label}")

        cap = {
            ecodes.EV_KEY: [ecodes.BTN_LEFT, ecodes.BTN_RIGHT, ecodes.BTN_MIDDLE,
                            ecodes.BTN_SIDE, ecodes.BTN_EXTRA] + _REMAP_KEYCODES,
            ecodes.EV_REL: [ecodes.REL_X, ecodes.REL_Y, ecodes.REL_WHEEL]
        }
        vmouse = UInput(events=cap, name="Python-Master-Mouse", version=0x1)
        mouse.grab()
        try:
            for event in mouse.read_loop():
                if self.stop_event.is_set(): break

                # Handle extra mouse button remapping
                if event.type == ecodes.EV_KEY and event.code in (ecodes.BTN_SIDE, ecodes.BTN_EXTRA):
                    target = extra_target if event.code == ecodes.BTN_EXTRA else side_target
                    if target == "PASSTHROUGH":
                        vmouse.write(event.type, event.code, event.value)
                        vmouse.syn()
                    elif target is not None:
                        vmouse.write(ecodes.EV_KEY, target, event.value)
                        vmouse.syn()
                    # If target is None (Disabled), event is eaten
                    continue

                # Handle left click with macro logic
                if event.type == ecodes.EV_KEY and event.code == ecodes.BTN_LEFT:
                    vmouse.write(event.type, event.code, event.value)
                    vmouse.syn()
                    if event.value == 1: self.physical_left_down = True
                    elif event.value == 0: self.physical_left_down = False
                    if not self.macro_enabled_toggle: continue
                    if event.value == 1 and not self.firing_burst:
                        now = time.time()
                        self.click_timestamps.append(now)
                        valid = [t for t in self.click_timestamps if now - t <= self.config["trigger_window"]]
                        self.click_timestamps[:] = valid
                        if self.config["enable_burst"] and len(self.click_timestamps) >= self.config["trigger_clicks"]:
                            self.click_timestamps.clear()
                            threading.Thread(target=self._burst_fire, args=(vmouse,)).start()
                        if self.config["enable_hold"]:
                            threading.Thread(target=self._hold_fire, args=(vmouse,)).start()
                    continue

                # Forward everything else (right click, middle click, mouse movement, scroll)
                vmouse.write(event.type, event.code, event.value)
        except Exception as e: print(f"Error: {e}")
        finally:
            mouse.ungrab()
            vmouse.close()

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.backend = MacroBackend()
        _ensure_beep_files()
        self._suppress_toggle_audio = False
        self.load_config()
        self.title("Input Master Control")
        self.geometry("700x820")

        # --- WINDOW ICON ---
        self._icon_image = None
        try:
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "input-master.png")
            if not os.path.exists(icon_path):
                icon_path = "/opt/input-master/input-master.png"
            if os.path.exists(icon_path):
                self._icon_image = Image.open(icon_path)
                tk_icon = ImageTk.PhotoImage(self._icon_image)
                self.wm_iconbitmap()
                self.iconphoto(False, tk_icon)
        except Exception as e:
            print(f"Icon Load Failed: {e}")

        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("dark-blue")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- SIDEBAR ---
        self.sidebar = ctk.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(6, weight=1)

        self.led_label = ctk.CTkLabel(self.sidebar, text="STATUS", font=ctk.CTkFont(size=14, weight="bold"))
        self.led_label.grid(row=0, column=0, padx=20, pady=(20, 5))
        self.led_indicator = ctk.CTkFrame(self.sidebar, width=30, height=30, corner_radius=15, fg_color="#0078FF")
        self.led_indicator.grid(row=1, column=0, padx=20, pady=5)

        ctk.CTkLabel(self.sidebar, text="MASTER TOGGLE", font=ctk.CTkFont(size=12)).grid(row=2, column=0, padx=20, pady=(30, 0))
        self.switch_master = ctk.CTkSwitch(self.sidebar, text="Active", command=self.on_master_toggle)
        self.switch_master.grid(row=3, column=0, padx=20, pady=10)
        self.switch_master.select()

        ctk.CTkLabel(self.sidebar, text="SUB-MODES", font=ctk.CTkFont(size=12)).grid(row=4, column=0, padx=20, pady=(30, 0))
        self.switch_burst = ctk.CTkSwitch(self.sidebar, text="Burst Mode")
        self.switch_burst.grid(row=5, column=0, padx=20, pady=10)
        self.switch_hold = ctk.CTkSwitch(self.sidebar, text="Hold Mode")
        self.switch_hold.grid(row=6, column=0, padx=20, pady=10)

        # --- MAIN AREA (scrollable) ---
        self.main_frame = ctk.CTkScrollableFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        row = 0

        # Device Selection
        ctk.CTkLabel(self.main_frame, text="Device Selection", font=ctk.CTkFont(size=16, weight="bold")).grid(row=row, column=0, sticky="w", pady=(0, 5)); row += 1
        ctk.CTkLabel(self.main_frame, text="Mouse Device", font=ctk.CTkFont(size=12)).grid(row=row, column=0, sticky="w"); row += 1
        self.combo_mouse = ctk.CTkComboBox(self.main_frame, width=300, values=self.get_device_list())
        self.combo_mouse.grid(row=row, column=0, sticky="w", pady=(0, 10)); row += 1
        self.combo_mouse.set(self.backend.config["mouse_name"])

        ctk.CTkLabel(self.main_frame, text="Toggle Keyboard", font=ctk.CTkFont(size=12)).grid(row=row, column=0, sticky="w"); row += 1
        self.combo_kb = ctk.CTkComboBox(self.main_frame, width=300, values=self.get_device_list())
        self.combo_kb.grid(row=row, column=0, sticky="w", pady=(0, 10)); row += 1
        self.combo_kb.set(self.backend.config["keyboard_name"])

        # Global Toggle Hotkey
        ctk.CTkLabel(self.main_frame, text="Global Toggle Hotkey", font=ctk.CTkFont(size=14, weight="bold")).grid(row=row, column=0, sticky="w", pady=(15, 5)); row += 1
        frame_hotkey = ctk.CTkFrame(self.main_frame)
        frame_hotkey.grid(row=row, column=0, sticky="ew", pady=(0, 10)); row += 1

        ctk.CTkLabel(frame_hotkey, text="Mod:").grid(row=0, column=0, padx=10, pady=10)
        self.combo_mod = ctk.CTkComboBox(frame_hotkey, width=100, values=["SUPER", "CTRL", "ALT", "NONE"])
        self.combo_mod.grid(row=0, column=1, padx=5)
        self.combo_mod.set(self.backend.config.get("toggle_modifier", "SUPER"))

        ctk.CTkLabel(frame_hotkey, text="Key:").grid(row=0, column=2, padx=10)
        sorted_keys = sorted(KEY_MAP.keys())
        self.combo_key = ctk.CTkComboBox(frame_hotkey, width=140, values=sorted_keys)
        self.combo_key.grid(row=0, column=3, padx=5)
        self.combo_key.set(self.backend.config.get("toggle_key", "NUMPAD 7"))

        # --- EXTRA MOUSE BUTTON MAPPING ---
        ctk.CTkLabel(self.main_frame, text="Extra Mouse Button Mapping", font=ctk.CTkFont(size=14, weight="bold")).grid(row=row, column=0, sticky="w", pady=(15, 5)); row += 1

        sorted_remap_keys = ["Pass Through", "Disabled"] + sorted(
            k for k in REMAP_KEY_MAP.keys() if k not in ("Pass Through", "Disabled")
        )

        frame_remap = ctk.CTkFrame(self.main_frame)
        frame_remap.grid(row=row, column=0, sticky="ew", pady=(0, 10)); row += 1

        ctk.CTkLabel(frame_remap, text="Button 4 (Side):").grid(row=0, column=0, padx=10, pady=10)
        self.combo_btn_side = ctk.CTkComboBox(frame_remap, width=160, values=sorted_remap_keys)
        self.combo_btn_side.grid(row=0, column=1, padx=5)
        self.combo_btn_side.set(self.backend.config.get("btn_side_map", "X"))

        ctk.CTkLabel(frame_remap, text="Button 5 (Extra):").grid(row=1, column=0, padx=10, pady=10)
        self.combo_btn_extra = ctk.CTkComboBox(frame_remap, width=160, values=sorted_remap_keys)
        self.combo_btn_extra.grid(row=1, column=1, padx=5)
        self.combo_btn_extra.set(self.backend.config.get("btn_extra_map", "Left Alt"))

        # Burst Settings
        ctk.CTkLabel(self.main_frame, text="Burst Settings", font=ctk.CTkFont(size=14, weight="bold")).grid(row=row, column=0, sticky="w", pady=(10, 5)); row += 1
        frame_burst = ctk.CTkFrame(self.main_frame)
        frame_burst.grid(row=row, column=0, sticky="ew", pady=(0, 10)); row += 1
        ctk.CTkLabel(frame_burst, text="Shots:").grid(row=0, column=0, padx=10, pady=10)
        self.entry_burst_count = ctk.CTkEntry(frame_burst, width=60)
        self.entry_burst_count.grid(row=0, column=1, padx=5)
        self.entry_burst_count.insert(0, str(self.backend.config["burst_count"]))
        ctk.CTkLabel(frame_burst, text="Dur (s):").grid(row=0, column=2, padx=10)
        self.entry_burst_dur = ctk.CTkEntry(frame_burst, width=60)
        self.entry_burst_dur.grid(row=0, column=3, padx=5)
        self.entry_burst_dur.insert(0, str(self.backend.config["burst_duration"]))

        # Hold Settings
        ctk.CTkLabel(self.main_frame, text="Hold Settings", font=ctk.CTkFont(size=14, weight="bold")).grid(row=row, column=0, sticky="w", pady=(10, 5)); row += 1
        frame_hold = ctk.CTkFrame(self.main_frame)
        frame_hold.grid(row=row, column=0, sticky="ew", pady=(0, 10)); row += 1
        ctk.CTkLabel(frame_hold, text="Delay (s):").grid(row=0, column=0, padx=10, pady=10)
        self.entry_hold_delay = ctk.CTkEntry(frame_hold, width=60)
        self.entry_hold_delay.grid(row=0, column=1, padx=5)
        self.entry_hold_delay.insert(0, str(self.backend.config["hold_delay"]))
        ctk.CTkLabel(frame_hold, text="Rate (s):").grid(row=0, column=2, padx=10)
        self.entry_hold_rate = ctk.CTkEntry(frame_hold, width=60)
        self.entry_hold_rate.grid(row=0, column=3, padx=5)
        self.entry_hold_rate.insert(0, str(self.backend.config["hold_rate"]))

        # Engine Button
        self.btn_start = ctk.CTkButton(self.main_frame, text="START ENGINE", height=50, fg_color="#0078FF", command=self.toggle_engine)
        self.btn_start.grid(row=row, column=0, sticky="ew", pady=20); row += 1
        self.log_box = ctk.CTkTextbox(self.main_frame, height=80)
        self.log_box.grid(row=row, column=0, sticky="ew"); row += 1

        if self.backend.config["enable_burst"]: self.switch_burst.select()
        if self.backend.config["enable_hold"]: self.switch_hold.select()
        sys.stdout = self

        # --- SYSTEM TRAY (must init before sync_ui_state) ---
        self.protocol("WM_DELETE_WINDOW", self._hide_to_tray)
        self.tray_icon = None
        self._setup_tray()
        self.after(100, self._hide_to_tray)

        self.sync_ui_state()

    def _load_tray_icons(self):
        self._tray_icons = {}
        fallback = Image.new("RGB", (64, 64), "gray")
        for variant in ("white", "blue", "red"):
            img = None
            try:
                p = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"tray-icon-{variant}.png")
                if not os.path.exists(p):
                    p = f"/opt/input-master/tray-icon-{variant}.png"
                if os.path.exists(p):
                    img = Image.open(p)
            except: pass
            self._tray_icons[variant] = img or fallback
        self._current_tray_state = None

    def _setup_tray(self):
        self._load_tray_icons()

        self.tray_icon = pystray.Icon(
            "InputMaster",
            self._tray_icons["white"],
            "Input Master",
            menu=Menu(
                MenuItem("Show", self._tray_show),
                MenuItem("Start Engine", self._tray_toggle_engine),
                MenuItem("Quit", self._tray_quit),
            )
        )
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def _hide_to_tray(self):
        self.withdraw()

    def _tray_show(self, icon=None, item=None):
        self.after(0, self._do_show)

    def _do_show(self):
        self.deiconify()
        self.lift()
        self.focus_force()

    def _tray_toggle_engine(self, icon=None, item=None):
        self.after(0, self.toggle_engine)

    def _tray_quit(self, icon=None, item=None):
        if self.tray_icon:
            self.tray_icon.stop()
        self.after(0, self._do_quit)

    def _do_quit(self):
        self.backend.stop()
        sys.stdout = sys.__stdout__
        self.destroy()

    def sync_ui_state(self):
        if self.backend.macro_enabled_toggle: self.led_indicator.configure(fg_color="#0078FF")
        else: self.led_indicator.configure(fg_color="#FF0000")
        current_switch_val = 1 if self.switch_master.get() else 0
        backend_val = 1 if self.backend.macro_enabled_toggle else 0
        if current_switch_val != backend_val:
            self._suppress_toggle_audio = True
            if backend_val == 1: self.switch_master.select()
            else: self.switch_master.deselect()
            self.after(50, self._clear_toggle_suppress)

        # Update tray icon color
        if not self.backend.running:
            new_state = "white"
        elif self.backend.macro_enabled_toggle:
            new_state = "blue"
        else:
            new_state = "red"
        if new_state != self._current_tray_state and self.tray_icon:
            self._current_tray_state = new_state
            self.tray_icon.icon = self._tray_icons[new_state]

        self.after(200, self.sync_ui_state)

    def on_master_toggle(self):
        new_state = bool(self.switch_master.get())
        self.backend.macro_enabled_toggle = new_state
        state_text = "ENABLED" if new_state else "DISABLED"
        print(f">>> GUI TOGGLE: Macros {state_text}")
        if not self._suppress_toggle_audio:
            sound = BEEP_ON_FILE if new_state else BEEP_OFF_FILE
            threading.Thread(target=_play_beep, args=(sound,), daemon=True).start()

    def _clear_toggle_suppress(self):
        self._suppress_toggle_audio = False

    def write(self, text):
        self.log_box.insert("end", text)
        self.log_box.see("end")
    def flush(self): pass

    def get_device_list(self):
        try:
            devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
            names = sorted(list(set([d.name for d in devices])))
        except PermissionError:
            names = ["(no permission - add user to input group)"]
        return names if names else ["(no devices found)"]

    def load_config(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    self.backend.config.update(json.load(f))
            except: pass

    def save_config(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.backend.config, f, indent=4)

    def toggle_engine(self):
        if not self.backend.running:
            self.backend.config["mouse_name"] = self.combo_mouse.get()
            self.backend.config["keyboard_name"] = self.combo_kb.get()
            self.backend.config["toggle_modifier"] = self.combo_mod.get()
            self.backend.config["toggle_key"] = self.combo_key.get()
            self.backend.config["enable_burst"] = bool(self.switch_burst.get())
            self.backend.config["enable_hold"] = bool(self.switch_hold.get())
            self.backend.config["burst_count"] = int(self.entry_burst_count.get())
            self.backend.config["burst_duration"] = float(self.entry_burst_dur.get())
            self.backend.config["hold_delay"] = float(self.entry_hold_delay.get())
            self.backend.config["hold_rate"] = float(self.entry_hold_rate.get())
            self.backend.config["btn_side_map"] = self.combo_btn_side.get()
            self.backend.config["btn_extra_map"] = self.combo_btn_extra.get()
            self.save_config()
            self.backend.start()
            self.btn_start.configure(text="STOP ENGINE", fg_color="red")
        else:
            self.backend.stop()
            self.btn_start.configure(text="START ENGINE", fg_color="#0078FF")

if __name__ == "__main__":
    app = App()
    app.mainloop()
