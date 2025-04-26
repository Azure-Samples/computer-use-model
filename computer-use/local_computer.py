import base64
import io
import platform
import time

import pyautogui


class LocalComputer:
    """Use pyautogui to take screenshots and perform actions on the local computer."""

    def __init__(self):
        self.dimensions = None
        system = platform.system()
        if system == "Windows":
            self.environment = "windows"
        elif system == "Darwin":
            self.environment = "mac"
        elif system == "Linux":
            self.environment = "linux"
        else:
            raise NotImplementedError(f"Unsupported operating system: '{system}'")

    def get_environment(self):
        return self.environment

    def get_dimensions(self):
        if not self.dimensions:
            screenshot = pyautogui.screenshot()
            self.dimensions = screenshot.size
        return self.dimensions

    def screenshot(self) -> str:
        screenshot = pyautogui.screenshot()
        self.dimensions = screenshot.size
        buffer = io.BytesIO()
        screenshot.save(buffer, format="PNG")
        buffer.seek(0)
        data = bytearray(buffer.getvalue())
        return base64.b64encode(data).decode("utf-8")

    def click(self, x: int, y: int, button: str = "left") -> None:
        width, height = self.dimensions
        if 0 <= x < width and 0 <= y < height:
            button = "middle" if button == "wheel" else button
            pyautogui.moveTo(x, y, duration=0.1)
            pyautogui.click(x, y, button=button)

    def double_click(self, x: int, y: int) -> None:
        width, height = self.dimensions
        if 0 <= x < width and 0 <= y < height:
            pyautogui.moveTo(x, y, duration=0.1)
            pyautogui.doubleClick(x, y)

    def scroll(self, x: int, y: int, scroll_x: int, scroll_y: int) -> None:
        pyautogui.scroll(-scroll_y, x=x, y=y)
        pyautogui.hscroll(scroll_x, x=x, y=y)

    def type(self, text: str) -> None:
        pyautogui.write(text)

    def wait(self, ms: int = 1000) -> None:
        time.sleep(ms / 1000)

    def move(self, x: int, y: int) -> None:
        pyautogui.moveTo(x, y, duration=0.1)

    def keypress(self, keys: list[str]) -> None:
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

    def drag(self, path: list[dict[str, int]]) -> None:
        if len(path) >= 2:
            x = path[0]["x"]
            y = path[0]["y"]
            pyautogui.moveTo(x, y, duration=0.5)
            for point in path[1:]:
                x = point["x"]
                y = point["y"]
                pyautogui.dragTo(x, y, duration=1.0, button="left")
