import base64
from io import BytesIO
import customtkinter as ctk
import evdev
from evdev import ecodes, UInput
import threading
import time
import sys
import random
import os
import json
import queue
import selectors
import shutil
import subprocess
from PIL import Image, ImageTk
import pystray
from pystray import MenuItem, Menu


# --- KEYBOARD MAPPING (for toggle hotkey) ---
KEY_MAP = {
    "NUMPAD 7": ecodes.KEY_KP7,
    "NUMPAD 8": ecodes.KEY_KP8,
    "NUMPAD 9": ecodes.KEY_KP9,
    "NUMPAD 4": ecodes.KEY_KP4,
    "NUMPAD 5": ecodes.KEY_KP5,
    "NUMPAD 6": ecodes.KEY_KP6,
    "NUMPAD 1": ecodes.KEY_KP1,
    "NUMPAD 2": ecodes.KEY_KP2,
    "NUMPAD 3": ecodes.KEY_KP3,
    "NUMPAD 0": ecodes.KEY_KP0,
    "F1": ecodes.KEY_F1,
    "F2": ecodes.KEY_F2,
    "F3": ecodes.KEY_F3,
    "F4": ecodes.KEY_F4,
    "F5": ecodes.KEY_F5,
    "F6": ecodes.KEY_F6,
    "F7": ecodes.KEY_F7,
    "F8": ecodes.KEY_F8,
    "F9": ecodes.KEY_F9,
    "F10": ecodes.KEY_F10,
    "F11": ecodes.KEY_F11,
    "F12": ecodes.KEY_F12,
    "A": ecodes.KEY_A,
    "B": ecodes.KEY_B,
    "C": ecodes.KEY_C,
    "D": ecodes.KEY_D,
    "E": ecodes.KEY_E,
    "F": ecodes.KEY_F,
    "G": ecodes.KEY_G,
    "H": ecodes.KEY_H,
    "I": ecodes.KEY_I,
    "J": ecodes.KEY_J,
    "K": ecodes.KEY_K,
    "L": ecodes.KEY_L,
    "M": ecodes.KEY_M,
    "N": ecodes.KEY_N,
    "O": ecodes.KEY_O,
    "P": ecodes.KEY_P,
    "Q": ecodes.KEY_Q,
    "R": ecodes.KEY_R,
    "S": ecodes.KEY_S,
    "T": ecodes.KEY_T,
    "U": ecodes.KEY_U,
    "V": ecodes.KEY_V,
    "W": ecodes.KEY_W,
    "X": ecodes.KEY_X,
    "Y": ecodes.KEY_Y,
    "Z": ecodes.KEY_Z,
    "CAPS LOCK": ecodes.KEY_CAPSLOCK,
    "TAB": ecodes.KEY_TAB,
    "ESC": ecodes.KEY_ESC,
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
    "A": ecodes.KEY_A,
    "B": ecodes.KEY_B,
    "C": ecodes.KEY_C,
    "D": ecodes.KEY_D,
    "E": ecodes.KEY_E,
    "F": ecodes.KEY_F,
    "G": ecodes.KEY_G,
    "H": ecodes.KEY_H,
    "I": ecodes.KEY_I,
    "J": ecodes.KEY_J,
    "K": ecodes.KEY_K,
    "L": ecodes.KEY_L,
    "M": ecodes.KEY_M,
    "N": ecodes.KEY_N,
    "O": ecodes.KEY_O,
    "P": ecodes.KEY_P,
    "Q": ecodes.KEY_Q,
    "R": ecodes.KEY_R,
    "S": ecodes.KEY_S,
    "T": ecodes.KEY_T,
    "U": ecodes.KEY_U,
    "V": ecodes.KEY_V,
    "W": ecodes.KEY_W,
    "X": ecodes.KEY_X,
    "Y": ecodes.KEY_Y,
    "Z": ecodes.KEY_Z,
    # Numbers
    "1": ecodes.KEY_1,
    "2": ecodes.KEY_2,
    "3": ecodes.KEY_3,
    "4": ecodes.KEY_4,
    "5": ecodes.KEY_5,
    "6": ecodes.KEY_6,
    "7": ecodes.KEY_7,
    "8": ecodes.KEY_8,
    "9": ecodes.KEY_9,
    "0": ecodes.KEY_0,
    # F-keys
    "F1": ecodes.KEY_F1,
    "F2": ecodes.KEY_F2,
    "F3": ecodes.KEY_F3,
    "F4": ecodes.KEY_F4,
    "F5": ecodes.KEY_F5,
    "F6": ecodes.KEY_F6,
    "F7": ecodes.KEY_F7,
    "F8": ecodes.KEY_F8,
    "F9": ecodes.KEY_F9,
    "F10": ecodes.KEY_F10,
    "F11": ecodes.KEY_F11,
    "F12": ecodes.KEY_F12,
    # Common keys
    "Space": ecodes.KEY_SPACE,
    "Enter": ecodes.KEY_ENTER,
    "Tab": ecodes.KEY_TAB,
    "Escape": ecodes.KEY_ESC,
    "Backspace": ecodes.KEY_BACKSPACE,
    "Delete": ecodes.KEY_DELETE,
    "Insert": ecodes.KEY_INSERT,
    # Navigation
    "Home": ecodes.KEY_HOME,
    "End": ecodes.KEY_END,
    "Page Up": ecodes.KEY_PAGEUP,
    "Page Down": ecodes.KEY_PAGEDOWN,
    "Up": ecodes.KEY_UP,
    "Down": ecodes.KEY_DOWN,
    "Left Arrow": ecodes.KEY_LEFT,
    "Right Arrow": ecodes.KEY_RIGHT,
}

ICON_BASE64 = """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
"""

# --- CONFIG DEFAULTS ---
DEFAULT_CONFIG = {
    "mouse_name": "Mouse",
    "keyboard_name": "Keyboard",
    "toggle_modifier": "SUPER",
    "toggle_key": "NUMPAD 7",
    "enable_burst": False,
    "enable_hold": False,
    "enable_audio": True,
    "trigger_clicks": 5,
    "trigger_window": 1.0,
    "burst_count": 10,
    "burst_duration": 1.0,
    "hold_delay": 0.2,
    "hold_rate": 0.1,
    "btn_side_map": "X",
    "btn_extra_map": "Left Alt",
}

# --- CONFIG PATH (User-level) ---
CONFIG_DIR = os.path.expanduser("~/.config/input-master")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

# Collect all possible remap keycodes for UInput capabilities
_REMAP_KEYCODES = list(set(v for v in REMAP_KEY_MAP.values() if isinstance(v, int)))


class MacroBackend:
    def __init__(self):
        self.running = False
        self.stop_event = threading.Event()
        self.thread = None
        self.config = DEFAULT_CONFIG.copy()
        self.physical_left_down = False
        self.firing_active = False
        self._fire_lock = threading.Lock()
        self._fire_cond = threading.Condition(self._fire_lock)
        self.click_timestamps = []
        self.macro_enabled_toggle = True
        self.meta_held = False
        self.mod_ctrl = False
        self.mod_alt = False
        self._audio_player = self._detect_audio_player()

    def update_config(self, new_config):
        self.config = new_config

    def _detect_audio_player(self):
        players = ["paplay", "aplay", "ffplay", "play", "mpg123"]
        for player in players:
            if shutil.which(player):
                return player
        return None

    def _play_notification_sound(self, sound_type):
        if not self.config.get("enable_audio", True):
            print(f">>> AUDIO: disabled in config")
            return
        if not self._audio_player:
            print(f">>> AUDIO: no player found")
            return

        script_dir = os.path.dirname(os.path.abspath(__file__))
        sound_file = os.path.join(script_dir, f"sound_{sound_type}.wav")
        if not os.path.exists(sound_file):
            sound_file = f"/opt/input-master/sound_{sound_type}.wav"
        if not os.path.exists(sound_file):
            print(f">>> AUDIO: file not found: sound_{sound_type}.wav")
            return

        print(f">>> AUDIO: playing {sound_file} with {self._audio_player}")

        try:
            if self._audio_player == "paplay":
                subprocess.Popen(
                    ["paplay", sound_file],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            elif self._audio_player == "aplay":
                subprocess.Popen(
                    ["aplay", "-q", sound_file],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            elif self._audio_player == "ffplay":
                subprocess.Popen(
                    [
                        "ffplay",
                        "-nodisp",
                        "-autoexit",
                        "-loglevel",
                        "quiet",
                        sound_file,
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            elif self._audio_player == "play":
                subprocess.Popen(
                    ["play", "-q", sound_file],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            elif self._audio_player == "mpg123":
                subprocess.Popen(
                    ["mpg123", "-q", sound_file],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
        except Exception as e:
            print(f"Audio playback error: {e}")

    def start(self):
        if self.running:
            return
        self.stop_event.clear()
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def stop(self):
        if not self.running:
            return
        self.stop_event.set()
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.5)
        print(">>> ENGINE STOPPED")

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
        with self._fire_lock:
            if self.firing_active:
                return
            self.firing_active = True
        time.sleep(0.2)
        count = max(1, int(self.config["burst_count"]))
        duration = max(0.05, float(self.config["burst_duration"]))
        min_hold = 0.04
        base_delay = max(0.0, (duration / count) - min_hold)

        try:
            for _ in range(count):
                if self.stop_event.is_set():
                    break
                hold = random.uniform(min_hold, min_hold + 0.02)
                wait = max(0.0, random.uniform(base_delay * 0.9, base_delay * 1.1))
                vmouse.write(ecodes.EV_KEY, ecodes.BTN_LEFT, 1)
                vmouse.syn()
                time.sleep(hold)
                vmouse.write(ecodes.EV_KEY, ecodes.BTN_LEFT, 0)
                vmouse.syn()
                time.sleep(wait)
        except Exception:
            pass
        finally:
            with self._fire_lock:
                self.firing_active = False
            self.click_timestamps.clear()

    def _hold_fire(self, vmouse):
        with self._fire_lock:
            if self.firing_active:
                return
            self.firing_active = True

        delay = max(0.0, float(self.config["hold_delay"]))
        rate = max(0.01, float(self.config["hold_rate"]))
        time.sleep(delay)
        try:
            while (
                self.physical_left_down
                and self.config["enable_hold"]
                and self.macro_enabled_toggle
            ):
                if self.stop_event.is_set():
                    break
                vmouse.write(ecodes.EV_KEY, ecodes.BTN_LEFT, 0)
                vmouse.syn()
                time.sleep(rate / 2)
                vmouse.write(ecodes.EV_KEY, ecodes.BTN_LEFT, 1)
                vmouse.syn()
                time.sleep(rate / 2)
        except Exception:
            pass
        finally:
            with self._fire_lock:
                self.firing_active = False
            try:
                vmouse.write(ecodes.EV_KEY, ecodes.BTN_LEFT, 0)
                vmouse.syn()
            except Exception:
                pass

    def _find_keyboard(self):
        name = self.config["keyboard_name"]
        code = KEY_MAP.get(self.config.get("toggle_key", "NUMPAD 7"), ecodes.KEY_KP7)
        kb = self._get_device(name, code)
        if not kb:
            kb = self._get_device(name, ecodes.KEY_ESC)
        return kb

    def _handle_kb_event(self, event):
        if event.type != ecodes.EV_KEY:
            return
        if event.code in (ecodes.KEY_LEFTMETA, ecodes.KEY_RIGHTMETA):
            self.meta_held = event.value in (1, 2)
        elif event.code in (ecodes.KEY_LEFTCTRL, ecodes.KEY_RIGHTCTRL):
            self.mod_ctrl = event.value in (1, 2)
        elif event.code in (ecodes.KEY_LEFTALT, ecodes.KEY_RIGHTALT):
            self.mod_alt = event.value in (1, 2)

        if event.code == self._toggle_code and event.value == 1:
            if self._toggle_mod == "NONE":
                authorized = True
            else:
                held = {
                    "SUPER": self.meta_held,
                    "CTRL": self.mod_ctrl,
                    "ALT": self.mod_alt,
                }
                authorized = held.get(self._toggle_mod, False)
            if authorized:
                self.macro_enabled_toggle = not self.macro_enabled_toggle
                state = "ENABLED" if self.macro_enabled_toggle else "DISABLED"
                self._play_notification_sound(
                    "toggle" if self.macro_enabled_toggle else "inactive"
                )
                print(f">>> KEY SHORTCUT: Macros {state}")

    def _handle_mouse_event(self, vmouse, event):
        # Handle extra mouse button remapping
        if event.type == ecodes.EV_KEY and event.code in (
            ecodes.BTN_SIDE,
            ecodes.BTN_EXTRA,
        ):
            target = (
                self.extra_target if event.code == ecodes.BTN_EXTRA else self.side_target
            )
            if target == "PASSTHROUGH":
                vmouse.write(event.type, event.code, event.value)
                vmouse.syn()
            elif target is not None:
                vmouse.write(ecodes.EV_KEY, target, event.value)
                vmouse.syn()
            # If target is None (Disabled), event is eaten
            return

        # Handle left click with macro logic
        if event.type == ecodes.EV_KEY and event.code == ecodes.BTN_LEFT:
            vmouse.write(event.type, event.code, event.value)
            vmouse.syn()
            if event.value == 1:
                self.physical_left_down = True
            elif event.value == 0:
                self.physical_left_down = False
            if not self.macro_enabled_toggle:
                return
            if event.value == 1 and not self.firing_active:
                now = time.time()
                self.click_timestamps.append(now)
                valid = [
                    t
                    for t in self.click_timestamps
                    if now - t <= self.config["trigger_window"]
                ]
                self.click_timestamps[:] = valid
                if (
                    self.config["enable_burst"]
                    and len(self.click_timestamps)
                    >= self.config["trigger_clicks"]
                ):
                    self.click_timestamps.clear()
                    threading.Thread(
                        target=self._burst_fire, args=(vmouse,)
                    ).start()
                if self.config["enable_hold"]:
                    threading.Thread(
                        target=self._hold_fire, args=(vmouse,)
                    ).start()
            return

        # Forward everything else (right click, middle click, mouse movement, scroll)
        vmouse.write(event.type, event.code, event.value)

    def _run_loop(self):
        mouse = self._get_device(self.config["mouse_name"], ecodes.BTN_LEFT)
        if not mouse:
            print(f"ERROR: Mouse '{self.config['mouse_name']}' not found.")
            self.running = False
            return
        kb = self._find_keyboard()

        self.meta_held = False
        self.mod_ctrl = False
        self.mod_alt = False
        self.physical_left_down = False
        self.click_timestamps.clear()

        # Resolve toggle hotkey and remap targets from config
        self._toggle_code = KEY_MAP.get(
            self.config.get("toggle_key", "NUMPAD 7"), ecodes.KEY_KP7
        )
        self._toggle_mod = self.config.get("toggle_modifier", "SUPER")
        self.side_target = REMAP_KEY_MAP.get(
            self.config.get("btn_side_map", "Pass Through"), "PASSTHROUGH"
        )
        self.extra_target = REMAP_KEY_MAP.get(
            self.config.get("btn_extra_map", "Pass Through"), "PASSTHROUGH"
        )

        side_label = self.config.get("btn_side_map", "Pass Through")
        extra_label = self.config.get("btn_extra_map", "Pass Through")
        print(f"Captured: {mouse.name}")
        print(f"Mouse Button 4 (Side) -> {side_label}")
        print(f"Mouse Button 5 (Extra) -> {extra_label}")
        if kb:
            print(
                f"Listening for Toggle [{self._toggle_mod} + "
                f"{self.config.get('toggle_key', 'NUMPAD 7')}] on {kb.name}"
            )
        else:
            print("Toggle keyboard not found - hotkey disabled.")

        cap = {
            ecodes.EV_KEY: [
                ecodes.BTN_LEFT,
                ecodes.BTN_RIGHT,
                ecodes.BTN_MIDDLE,
                ecodes.BTN_SIDE,
                ecodes.BTN_EXTRA,
            ]
            + _REMAP_KEYCODES,
            ecodes.EV_REL: [
                ecodes.REL_X,
                ecodes.REL_Y,
                ecodes.REL_WHEEL,
                ecodes.REL_HWHEEL,
            ],
        }
        vmouse = UInput(events=cap, name="Python-Master-Mouse", version=0x1)
        mouse.grab()

        sel = selectors.DefaultSelector()
        sel.register(mouse, selectors.EVENT_READ)
        if kb:
            sel.register(kb, selectors.EVENT_READ)

        print(">>> ENGINE STARTED")
        try:
            while not self.stop_event.is_set():
                for key, _ in sel.select(timeout=0.25):
                    dev = key.fileobj
                    for event in dev.read():
                        if dev is mouse:
                            self._handle_mouse_event(vmouse, event)
                        else:
                            self._handle_kb_event(event)
        except Exception as e:
            print(f"Engine loop error: {e}")
        finally:
            try:
                mouse.ungrab()
            except Exception:
                pass
            sel.close()
            vmouse.close()
            mouse.close()
            if kb:
                kb.close()
            self.running = False


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        # Thread-safe bridge for UI updates from backend/tray threads
        self._ui_queue = queue.Queue()
        self.backend = MacroBackend()
        self.load_config()
        self.title("Input Master Control")
        self.geometry("700x820")

        # --- WINDOW ICON (embedded base64, PNG fallback) ---
        self._icon_image = None
        try:
            icon_image = None
            if ICON_BASE64:
                icon_image = Image.open(BytesIO(base64.b64decode(ICON_BASE64)))
            else:
                icon_path = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)), "input-master.png"
                )
                if not os.path.exists(icon_path):
                    icon_path = "/opt/input-master/input-master.png"
                if os.path.exists(icon_path):
                    icon_image = Image.open(icon_path)
            if icon_image:
                self._icon_image = icon_image
                tk_icon = ImageTk.PhotoImage(icon_image)
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

        self.led_label = ctk.CTkLabel(
            self.sidebar, text="STATUS", font=ctk.CTkFont(size=14, weight="bold")
        )
        self.led_label.grid(row=0, column=0, padx=20, pady=(20, 5))
        self.led_indicator = ctk.CTkFrame(
            self.sidebar, width=30, height=30, corner_radius=15, fg_color="#0078FF"
        )
        self.led_indicator.grid(row=1, column=0, padx=20, pady=5)

        ctk.CTkLabel(
            self.sidebar, text="MASTER TOGGLE", font=ctk.CTkFont(size=12)
        ).grid(row=2, column=0, padx=20, pady=(30, 0))
        self.switch_master = ctk.CTkSwitch(
            self.sidebar, text="Active", command=self.on_master_toggle
        )
        self.switch_master.grid(row=3, column=0, padx=20, pady=10)
        self.switch_master.select()

        ctk.CTkLabel(self.sidebar, text="SUB-MODES", font=ctk.CTkFont(size=12)).grid(
            row=4, column=0, padx=20, pady=(30, 0)
        )
        self.var_burst = ctk.StringVar(value="off")
        self.var_hold = ctk.StringVar(value="off")
        self.switch_burst = ctk.CTkSwitch(
            self.sidebar, text="Burst Mode",
            variable=self.var_burst, onvalue="on", offvalue="off",
            command=self._on_burst_toggle
        )
        self.switch_burst.grid(row=5, column=0, padx=20, pady=10)

        self.switch_hold = ctk.CTkSwitch(
            self.sidebar, text="Hold Mode",
            variable=self.var_hold, onvalue="on", offvalue="off",
            command=self._on_hold_toggle
        )
        self.switch_hold.grid(row=6, column=0, padx=20, pady=10)
        self.switch_audio = ctk.CTkSwitch(self.sidebar, text="Audio Notifications")
        self.switch_audio.grid(row=7, column=0, padx=20, pady=10)

        # --- MAIN AREA (scrollable) ---
        self.main_frame = ctk.CTkScrollableFrame(
            self, corner_radius=0, fg_color="transparent"
        )
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        row = 0

        # Device Selection
        ctk.CTkLabel(
            self.main_frame,
            text="Device Selection",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=row, column=0, sticky="w", pady=(0, 5))
        row += 1
        ctk.CTkLabel(
            self.main_frame, text="Mouse Device", font=ctk.CTkFont(size=12)
        ).grid(row=row, column=0, sticky="w")
        row += 1
        self.combo_mouse = ctk.CTkComboBox(
            self.main_frame, width=300, values=self.get_device_list()
        )
        self.combo_mouse.grid(row=row, column=0, sticky="w", pady=(0, 10))
        row += 1
        self.combo_mouse.set(self.backend.config["mouse_name"])

        ctk.CTkLabel(
            self.main_frame, text="Toggle Keyboard", font=ctk.CTkFont(size=12)
        ).grid(row=row, column=0, sticky="w")
        row += 1
        self.combo_kb = ctk.CTkComboBox(
            self.main_frame, width=300, values=self.get_device_list()
        )
        self.combo_kb.grid(row=row, column=0, sticky="w", pady=(0, 10))
        row += 1
        self.combo_kb.set(self.backend.config["keyboard_name"])

        # Global Toggle Hotkey
        ctk.CTkLabel(
            self.main_frame,
            text="Global Toggle Hotkey",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=row, column=0, sticky="w", pady=(15, 5))
        row += 1
        frame_hotkey = ctk.CTkFrame(self.main_frame)
        frame_hotkey.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        row += 1

        ctk.CTkLabel(frame_hotkey, text="Mod:").grid(row=0, column=0, padx=10, pady=10)
        self.combo_mod = ctk.CTkComboBox(
            frame_hotkey, width=100, values=["SUPER", "CTRL", "ALT", "NONE"]
        )
        self.combo_mod.grid(row=0, column=1, padx=5)
        self.combo_mod.set(self.backend.config.get("toggle_modifier", "SUPER"))

        ctk.CTkLabel(frame_hotkey, text="Key:").grid(row=0, column=2, padx=10)
        sorted_keys = sorted(KEY_MAP.keys())
        self.combo_key = ctk.CTkComboBox(frame_hotkey, width=140, values=sorted_keys)
        self.combo_key.grid(row=0, column=3, padx=5)
        self.combo_key.set(self.backend.config.get("toggle_key", "NUMPAD 7"))

        # --- EXTRA MOUSE BUTTON MAPPING ---
        ctk.CTkLabel(
            self.main_frame,
            text="Extra Mouse Button Mapping",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=row, column=0, sticky="w", pady=(15, 5))
        row += 1

        sorted_remap_keys = ["Pass Through", "Disabled"] + sorted(
            k for k in REMAP_KEY_MAP.keys() if k not in ("Pass Through", "Disabled")
        )

        frame_remap = ctk.CTkFrame(self.main_frame)
        frame_remap.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        row += 1

        ctk.CTkLabel(frame_remap, text="Button 4 (Side):").grid(
            row=0, column=0, padx=10, pady=10
        )
        self.combo_btn_side = ctk.CTkComboBox(
            frame_remap, width=160, values=sorted_remap_keys
        )
        self.combo_btn_side.grid(row=0, column=1, padx=5)
        self.combo_btn_side.set(self.backend.config.get("btn_side_map", "X"))

        ctk.CTkLabel(frame_remap, text="Button 5 (Extra):").grid(
            row=1, column=0, padx=10, pady=10
        )
        self.combo_btn_extra = ctk.CTkComboBox(
            frame_remap, width=160, values=sorted_remap_keys
        )
        self.combo_btn_extra.grid(row=1, column=1, padx=5)
        self.combo_btn_extra.set(self.backend.config.get("btn_extra_map", "Left Alt"))

        # Burst Settings
        ctk.CTkLabel(
            self.main_frame,
            text="Burst Settings",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=row, column=0, sticky="w", pady=(10, 5))
        row += 1
        frame_burst = ctk.CTkFrame(self.main_frame)
        frame_burst.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        row += 1
        ctk.CTkLabel(frame_burst, text="Shots:").grid(row=0, column=0, padx=10, pady=10)
        self.entry_burst_count = ctk.CTkEntry(frame_burst, width=60)
        self.entry_burst_count.grid(row=0, column=1, padx=5)
        self.entry_burst_count.insert(0, str(self.backend.config["burst_count"]))
        ctk.CTkLabel(frame_burst, text="Dur (s):").grid(row=0, column=2, padx=10)
        self.entry_burst_dur = ctk.CTkEntry(frame_burst, width=60)
        self.entry_burst_dur.grid(row=0, column=3, padx=5)
        self.entry_burst_dur.insert(0, str(self.backend.config["burst_duration"]))

        # Hold Settings
        ctk.CTkLabel(
            self.main_frame,
            text="Hold Settings",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=row, column=0, sticky="w", pady=(10, 5))
        row += 1
        frame_hold = ctk.CTkFrame(self.main_frame)
        frame_hold.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        row += 1
        ctk.CTkLabel(frame_hold, text="Delay (s):").grid(
            row=0, column=0, padx=10, pady=10
        )
        self.entry_hold_delay = ctk.CTkEntry(frame_hold, width=60)
        self.entry_hold_delay.grid(row=0, column=1, padx=5)
        self.entry_hold_delay.insert(0, str(self.backend.config["hold_delay"]))
        ctk.CTkLabel(frame_hold, text="Rate (s):").grid(row=0, column=2, padx=10)
        self.entry_hold_rate = ctk.CTkEntry(frame_hold, width=60)
        self.entry_hold_rate.grid(row=0, column=3, padx=5)
        self.entry_hold_rate.insert(0, str(self.backend.config["hold_rate"]))

        # Engine Button
        self.btn_start = ctk.CTkButton(
            self.main_frame,
            text="START ENGINE",
            height=50,
            fg_color="#0078FF",
            command=self.toggle_engine,
        )
        self.btn_start.grid(row=row, column=0, sticky="ew", pady=20)
        row += 1
        self.log_box = ctk.CTkTextbox(self.main_frame, height=80)
        self.log_box.grid(row=row, column=0, sticky="ew")
        row += 1

        # Initial sub-mode switch state from config (mutually exclusive)
        if self.backend.config["enable_burst"]:
            self.var_burst.set("on")
            self.backend.config["enable_hold"] = False
        elif self.backend.config["enable_hold"]:
            self.var_hold.set("on")
        if self.backend.config.get("enable_audio", True):
            self.switch_audio.select()
        sys.stdout = self
        self.after(20, self._pump)

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
                p = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    f"tray-icon-{variant}.png",
                )
                if not os.path.exists(p):
                    p = f"/opt/input-master/tray-icon-{variant}.png"
                if os.path.exists(p):
                    img = Image.open(p)
            except Exception:
                pass
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
            ),
        )
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def _hide_to_tray(self):
        self.withdraw()

    def _tray_show(self, icon=None, item=None):
        self._ui_queue.put(self._do_show)

    def _do_show(self):
        self.deiconify()
        self.lift()
        self.focus_force()

    def _tray_toggle_engine(self, icon=None, item=None):
        self._ui_queue.put(self.toggle_engine)

    def _tray_quit(self, icon=None, item=None):
        self._ui_queue.put(self._do_quit)

    def _do_quit(self):
        self.backend.stop()
        try:
            self.save_config()
        except Exception as e:
            print(f"Config save failed: {e}")
        if self.tray_icon:
            self.tray_icon.stop()
        sys.stdout = sys.__stdout__
        self.destroy()

    def sync_ui_state(self):
        if not self.winfo_exists():
            return
        running = self.backend.running
        enabled = self.backend.macro_enabled_toggle

        # LED: blue running+enabled, red running+disabled, gray stopped
        if running and enabled:
            self.led_indicator.configure(fg_color="#0078FF")
        elif running:
            self.led_indicator.configure(fg_color="#FF0000")
        else:
            self.led_indicator.configure(fg_color="#555555")

        current_switch_val = 1 if self.switch_master.get() else 0
        backend_val = 1 if enabled else 0
        if current_switch_val != backend_val:
            if backend_val == 1:
                self.switch_master.select()
            else:
                self.switch_master.deselect()

        # Engine button reflects the actual engine state
        desired_text = "STOP ENGINE" if running else "START ENGINE"
        if self.btn_start.cget("text") != desired_text:
            self.btn_start.configure(
                text=desired_text, fg_color="red" if running else "#0078FF"
            )

        # Update tray icon color
        if not running:
            new_state = "white"
        elif enabled:
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

    def _on_burst_toggle(self):
        if self.var_burst.get() == "on":
            self.var_hold.set("off")
            self.backend.config["enable_hold"] = False
            self.backend.config["enable_burst"] = True
        else:
            self.backend.config["enable_burst"] = False

    def _on_hold_toggle(self):
        if self.var_hold.get() == "on":
            self.var_burst.set("off")
            self.backend.config["enable_burst"] = False
            self.backend.config["enable_hold"] = True
        else:
            self.backend.config["enable_hold"] = False

    def _pump(self):
        try:
            while True:
                fn = self._ui_queue.get_nowait()
                try:
                    fn()
                except Exception:
                    pass
        except queue.Empty:
            pass
        try:
            self.after(20, self._pump)
        except Exception:
            pass

    def write(self, text):
        self._ui_queue.put(lambda: self._append_log(text))

    def _append_log(self, text):
        try:
            self.log_box.insert("end", text)
            self.log_box.see("end")
        except Exception:
            pass

    def flush(self):
        pass

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
                with open(CONFIG_FILE, "r") as f:
                    self.backend.config.update(json.load(f))
            except Exception as e:
                print(f"Config load failed: {e}")

    def save_config(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.backend.config, f, indent=4)

    def _parse_setting(self, widget, name, lo, hi, cast, default):
        try:
            value = cast(widget.get().strip())
            if lo <= value <= hi:
                return value
        except ValueError:
            pass
        print(f">>> GUI: '{name}' must be between {lo} and {hi}; using {default}")
        return default

    def toggle_engine(self):
        if self.backend.running:
            self.backend.stop()
            return
        self.backend.config["mouse_name"] = self.combo_mouse.get()
        self.backend.config["keyboard_name"] = self.combo_kb.get()
        self.backend.config["toggle_modifier"] = self.combo_mod.get()
        self.backend.config["toggle_key"] = self.combo_key.get()
        self.backend.config["enable_burst"] = (self.var_burst.get() == "on")
        self.backend.config["enable_hold"] = (self.var_hold.get() == "on")
        self.backend.config["enable_audio"] = bool(self.switch_audio.get())
        self.backend.config["btn_side_map"] = self.combo_btn_side.get()
        self.backend.config["btn_extra_map"] = self.combo_btn_extra.get()
        self.backend.config["burst_count"] = self._parse_setting(
            self.entry_burst_count, "Burst shots", 1, 100, int, 10
        )
        self.backend.config["burst_duration"] = self._parse_setting(
            self.entry_burst_dur, "Burst duration", 0.1, 60.0, float, 1.0
        )
        self.backend.config["hold_delay"] = self._parse_setting(
            self.entry_hold_delay, "Hold delay", 0.0, 60.0, float, 0.2
        )
        self.backend.config["hold_rate"] = self._parse_setting(
            self.entry_hold_rate, "Hold rate", 0.01, 60.0, float, 0.1
        )
        self.save_config()
        self.backend.start()


if __name__ == "__main__":
    app = App()
    app.mainloop()
