
import base64
import io
import platform
import time

import pyautogui


class LocalComputer:
    """Controls the local computer by using pyautogui to take screenshots and perform actions."""

    def __init__(self):
        screenshot = pyautogui.screenshot()
        self.dimensions = screenshot.size
        system = platform.system()
        if system == "Windows":
            self.environment = "windows"
        elif system == "Darwin":
            self.environment = "mac"
        elif system == "Linux":
            self.environment = "linux"
        else:
            raise NotImplementedError(f"Unsupported operating system: '{system}'")

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
        for key in keys:
            key = key.lower()
            pyautogui.keyDown(key)
        for key in keys:
            key = key.lower()
            pyautogui.keyUp(key)

    def drag(self, path: list[dict[str, int]]) -> None:
        x = path[0].x
        y = path[0].y
        pyautogui.moveTo(x, y, duration=0.1)
        pyautogui.mouseDown()
        for point in path[1:]:
            x = point.x
            y = point.y
            pyautogui.moveTo(x, y, duration=0.1)
        pyautogui.mouseUp()
