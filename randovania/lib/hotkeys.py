import dataclasses
from typing import Self

SPECIAL_KEY_DISPLAY_NAMES = {
    "alt": "Alt",
    "alt_l": "Left Alt",
    "alt_r": "Right Alt",
    "ctrl": "Ctrl",
    "ctrl_l": "Left Ctrl",
    "ctrl_r": "Right Ctrl",
    "shift": "Shift",
    "shift_l": "Left Shift",
    "shift_r": "Right Shift",
    "cmd": "Command",
    "cmd_l": "Left Command",
    "cmd_r": "Right Command",
    "super": "Super",
    "super_l": "Left Super",
    "super_r": "Right Super",
    "enter": "Enter",
    "esc": "Escape",
    "escape": "Escape",
    "tab": "Tab",
    "space": "Space",
    "backspace": "Backspace",
    "delete": "Delete",
    "insert": "Insert",
    "home": "Home",
    "end": "End",
    "page_up": "Page Up",
    "page_down": "Page Down",
    "caps_lock": "Caps Lock",
    "num_lock": "Num Lock",
    "scroll_lock": "Scroll Lock",
    "print_screen": "Print Screen",
    "pause": "Pause",
    "menu": "Menu",
    "f1": "F1",
    "f2": "F2",
    "f3": "F3",
    "f4": "F4",
    "f5": "F5",
    "f6": "F6",
    "f7": "F7",
    "f8": "F8",
    "f9": "F9",
    "f10": "F10",
    "f11": "F11",
    "f12": "F12",
    "left": "Left Arrow",
    "right": "Right Arrow",
    "up": "Up Arrow",
    "down": "Down Arrow",
}


@dataclasses.dataclass(frozen=True)
class Hotkey:
    """
    Represents a hotkey, which can be either:
    - A regular key (stored as its virtual key code as a string in name_or_vk)
    - A special key (stored as its name, e.g. 'ctrl_l', 'f1', etc. in name_or_vk)

    For regular keys, name_or_vk is a stringified integer (the virtual key code).
    For special keys, name_or_vk is a string name (see SPECIAL_KEY_DISPLAY_NAMES for mapping).
    """

    name_or_vk: str

    @property
    def as_json(self) -> dict:
        return {
            "name_or_vk": self.name_or_vk,
        }

    @classmethod
    def from_json(cls, value: dict) -> Self:
        return cls(
            name_or_vk=value["name_or_vk"],
        )

    def as_int(self) -> int | None:
        """
        Returns the virtual key code as integer if this hotkey represents a regular key.
        Returns None for special keys (which are stored as names).
        """
        return int(self.name_or_vk) if self.name_or_vk.isdigit() else None

    def user_friendly_str(self) -> str:
        """
        Returns a user-friendly string for this hotkey.
        - For numpad keys (VK 96-105), returns 'Numpad X'.
        - For other regular keys, returns the character.
        - For special keys, returns a mapped display name if available, otherwise the raw name.
        """
        as_digit = self.as_int()
        # numpad keys
        if as_digit and 96 <= as_digit <= 105:
            return f"Numpad {as_digit - 96}"
        else:
            # every other key
            if as_digit:
                return chr(as_digit)
        # special keys
        return SPECIAL_KEY_DISPLAY_NAMES.get(self.name_or_vk.lower(), self.name_or_vk)


@dataclasses.dataclass(frozen=True)
class HotkeysOption:
    start_finish_hotkey: Hotkey | None
    pause_hotkey: Hotkey | None

    @property
    def as_json(self) -> dict:
        return {
            "start_finish_hotkey": self.start_finish_hotkey.as_json if self.start_finish_hotkey is not None else None,
            "pause_hotkey": self.pause_hotkey.as_json if self.pause_hotkey is not None else None,
        }

    @classmethod
    def from_json(cls, value: dict) -> Self:
        return cls(
            start_finish_hotkey=(
                Hotkey.from_json(value["start_finish_hotkey"]) if value["start_finish_hotkey"] else None
            ),
            pause_hotkey=Hotkey.from_json(value["pause_hotkey"]) if value["pause_hotkey"] else None,
        )
