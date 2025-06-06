import asyncio
import base64
import io
import platform

import pyautogui


class LocalComputer:
    """Use pyautogui to take screenshots and perform actions on the local computer."""

    def __init__(self):
        self.size = None

    @property
    def environment(self):
        system = platform.system()
        if system == "Windows":
            return "windows"
        elif system == "Darwin":
            return "mac"
        elif system == "Linux":
            return "linux"
        else:
            raise NotImplementedError(f"Unsupported operating system: '{system}'")

    @property
    def dimensions(self):
        if not self.size:
            screenshot = pyautogui.screenshot()
            self.size = screenshot.size
        return self.size

    async def screenshot(self) -> str:
        screenshot = pyautogui.screenshot()
        self.size = screenshot.size
        buffer = io.BytesIO()
        screenshot.save(buffer, format="PNG")
        buffer.seek(0)
        data = bytearray(buffer.getvalue())
        return base64.b64encode(data).decode("utf-8")

    async def click(self, x: int, y: int, button: str = "left") -> None:
        width, height = self.size
        if 0 <= x < width and 0 <= y < height:
            button = "middle" if button == "wheel" else button
            pyautogui.moveTo(x, y, duration=0.1)
            pyautogui.click(x, y, button=button)

    async def double_click(self, x: int, y: int) -> None:
        width, height = self.size
        if 0 <= x < width and 0 <= y < height:
            pyautogui.moveTo(x, y, duration=0.1)
            pyautogui.doubleClick(x, y)

    async def scroll(self, x: int, y: int, scroll_x: int, scroll_y: int) -> None:
        pyautogui.moveTo(x, y, duration=0.5)
        pyautogui.scroll(-scroll_y)
        pyautogui.hscroll(scroll_x)

    async def type(self, text: str) -> None:
        pyautogui.write(text)

    async def wait(self, ms: int = 1000) -> None:
        await asyncio.sleep(ms / 1000)

    async def move(self, x: int, y: int) -> None:
        pyautogui.moveTo(x, y, duration=0.1)

    async def keypress(self, keys: list[str]) -> None:
        keys = [key.lower() for key in keys]
        keymap = {
            "arrowdown": "down",
            "arrowleft": "left",
            "arrowright": "right",
            "arrowup": "up",
        }
        keys = [keymap.get(key, key) for key in keys]
        for key in keys:
            pyautogui.keyDown(key)
        for key in keys:
            pyautogui.keyUp(key)

    async def drag(self, path: list[tuple[int, int]]) -> None:
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
