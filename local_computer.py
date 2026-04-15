import asyncio
import base64
import contextlib
import io

import pyautogui


_KEYMAP = {
    "arrowdown": "down",
    "arrowleft": "left",
    "arrowright": "right",
    "arrowup": "up",
    "cmd": "win",
    "command": "win",
    "meta": "win",
    "super": "win",
    "control": "ctrl",
    "return": "enter",
    "esc": "escape",
}


def _normalize_key(key: str) -> str:
    key = key.lower()
    return _KEYMAP.get(key, key)


class LocalComputer:
    """Use pyautogui to take screenshots and perform actions on the local computer."""

    def __init__(self):
        self.size = None

    @property
    def dimensions(self):
        if not self.size:
            screenshot = pyautogui.screenshot()
            self.size = screenshot.size
        return self.size

    @contextlib.contextmanager
    def _with_modifiers(self, keys: list[str] | None):
        """Hold modifier keys down for the duration of a mouse action."""
        pressed: list[str] = []
        try:
            for key in keys or []:
                normalized = _normalize_key(key)
                pyautogui.keyDown(normalized)
                pressed.append(normalized)
            yield
        finally:
            for key in reversed(pressed):
                pyautogui.keyUp(key)

    async def screenshot(self) -> str:
        screenshot = pyautogui.screenshot()
        self.size = screenshot.size
        buffer = io.BytesIO()
        screenshot.save(buffer, format="PNG")
        buffer.seek(0)
        data = bytearray(buffer.getvalue())
        return base64.b64encode(data).decode("utf-8")

    async def click(self, x: int, y: int, button: str = "left", keys: list[str] | None = None) -> None:
        width, height = self.size
        if 0 <= x < width and 0 <= y < height:
            button = "middle" if button == "wheel" else button
            pyautogui.moveTo(x, y, duration=0.1)
            with self._with_modifiers(keys):
                pyautogui.click(x, y, button=button)

    async def double_click(self, x: int, y: int, keys: list[str] | None = None) -> None:
        width, height = self.size
        if 0 <= x < width and 0 <= y < height:
            pyautogui.moveTo(x, y, duration=0.1)
            with self._with_modifiers(keys):
                pyautogui.doubleClick(x, y)

    async def scroll(self, x: int, y: int, scroll_x: int, scroll_y: int, keys: list[str] | None = None) -> None:
        pyautogui.moveTo(x, y, duration=0.5)
        with self._with_modifiers(keys):
            pyautogui.scroll(-scroll_y)
            pyautogui.hscroll(scroll_x)

    async def type(self, text: str) -> None:
        pyautogui.write(text)

    async def wait(self, ms: int = 1000) -> None:
        await asyncio.sleep(ms / 1000)

    async def move(self, x: int, y: int, keys: list[str] | None = None) -> None:
        with self._with_modifiers(keys):
            pyautogui.moveTo(x, y, duration=0.1)

    async def keypress(self, keys: list[str]) -> None:
        keys = [_normalize_key(key) for key in keys]
        for key in keys:
            pyautogui.keyDown(key)
        for key in reversed(keys):
            pyautogui.keyUp(key)

    async def drag(self, path: list[tuple[int, int]], keys: list[str] | None = None) -> None:
        with self._with_modifiers(keys):
            if len(path) <= 1:
                pass
            elif len(path) == 2:
                pyautogui.moveTo(*path[0], duration=0.5)
                pyautogui.dragTo(*path[1], duration=1.0, button="left")
            else:
                pyautogui.moveTo(*path[0], duration=0.5)
                pyautogui.mouseDown(button="left")
                for point in path[1:]:
                    pyautogui.dragTo(*point, duration=1.0, mouseDownUp=False)
                pyautogui.mouseUp(button="left")
