
import base64
import io
import time
import re
import logging
import typing
import PIL
import openai

logger = logging.getLogger(__name__)

class State:
    "Tracking and controlling the state."

    previous_response_id: str
    next_action: typing.Literal["user_interaction", "computer_call_output"] = ""
    previous_computer_id: str = ""
    computer_action: str = ""
    computer_action_args: dict = {}
    pending_safety_checks: list = []
    reasoning_summary: str = ""
    message: str = ""

    def __init__(self, response):
        assert response.status == "completed"
        self.previous_response_id = response.id

        # If the item is a computer call, setting the next action and passing the action arguments.
        for item in response.output:
            if item.type == "computer_call":
                self.next_action = "computer_call_output"
                self.previous_computer_id = item.call_id
                self.computer_action = item.action.type
                self.computer_action_args = {k: v for k, v in vars(item.action).items() if k != "type"}
                self.pending_safety_checks = item.pending_safety_checks
            elif item.type == "reasoning":
                self.reasoning_summary = "".join([summary.text for summary in item.summary])
            elif item.type == "message":
                self.next_action = "user_interaction"
                self.message += item.content[-1].text
            else:
                raise NotImplementedError(f"Unsupported response output type '{item.type}'.")

class Scaler:
    """Wrapper for a computer instance that performs resizing and coordinate translation."""

    def __init__(self, width, height, computer):
        self.dimensions = (width, height)
        self.computer = computer
        self.environment = computer.environment
        self.screen_width = -1
        self.screen_height = -1

    def screenshot(self) -> str:
        # Call the underlying computer. Screenshot will be taken after the action
        screenshot = self.computer.screenshot()
        screenshot = base64.b64decode(screenshot)
        # Scale the screenshot
        buffer = io.BytesIO(screenshot)
        image = PIL.Image.open(buffer)
        self.screen_width, self.screen_height = image.size
        width, height = self.dimensions
        ratio = min(width / self.screen_width, height / self.screen_height)
        new_width = int(self.screen_width * ratio)
        new_height = int(self.screen_height * ratio)
        resized_image = image.resize((new_width, new_height), PIL.Image.Resampling.LANCZOS)
        image = PIL.Image.new("RGB", (width, height), (0, 0, 0))
        image.paste(resized_image, (0, 0))
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        data = bytearray(buffer.getvalue())
        return base64.b64encode(data).decode("utf-8")

    def click(self, x: int, y: int, button: str = "left") -> None:
        x, y = self._point_to_screen_coords(x, y)
        self.computer.click(x, y, button=button)

    def double_click(self, x: int, y: int) -> None:
        x, y = self._point_to_screen_coords(x, y)
        self.computer.double_click(x, y)

    def scroll(self, x: int, y: int, scroll_x: int, scroll_y: int) -> None:
        x, y = self._point_to_screen_coords(x, y)
        self.computer.scroll(x, y, scroll_x, scroll_y)

    def type(self, text: str) -> None:
        self.computer.type(text)

    def wait(self, ms: int = 1000) -> None:
        self.computer.wait(ms)

    def move(self, x: int, y: int) -> None:
        x, y = self._point_to_screen_coords(x, y)
        self.computer.move(x, y)

    def keypress(self, keys: list[str]) -> None:
        self.computer.keypress(keys)

    def drag(self, path: list[dict[str, int]]) -> None:
        for point in path:
            x, y = self._point_to_screen_coords(point.x, point.y)
            point.x = x
            point.y = y
        self.computer.drag(path)

    def _point_to_screen_coords(self, x, y):
        width, height = self.dimensions
        ratio = min(width / self.screen_width, height / self.screen_height)
        x = x / ratio
        y = y / ratio
        return int(x), int(y)

class Agent:
    """CUA agent to start and continue task execution"""

    def __init__(self, client, model, computer):
        self.client = client
        self.model = model
        self.computer = computer
        self.state = None

    def start_task(self, user_message):
        tools = [self.computer_tool()]
        response = self.client.responses.create(
            model = self.model,
            input = user_message,
            tools = tools,
            truncation = "auto")
        self.state = State(response)

    @property
    def requires_user_input(self):
        return self.state.next_action == "user_interaction"

    @property
    def requires_consent(self):
        return self.state.next_action == "computer_call_output"

    @property
    def pending_safety_checks(self):
        return self.state.pending_safety_checks

    @property
    def reasoning_summary(self):
        return self.state.reasoning_summary

    @property
    def message(self):
        return self.state.message

    def continue_task(self, user_message=""):
        screenshot = ""
        previous_response_id = self.state.previous_response_id
        if self.state.next_action == "computer_call_output":
            action = self.state.computer_action
            action_args = self.state.computer_action_args
            logger.info("%s %s", action, action_args)
            method = getattr(self.computer, action)
            method(**action_args)
            screenshot = self.computer.screenshot()
        if self.state.next_action == "computer_call_output":
            next_input = openai.types.responses.response_input_param.ComputerCallOutput(
                type = "computer_call_output",
                call_id = self.state.previous_computer_id,
                output = openai.types.responses.response_input_param.ResponseComputerToolCallOutputScreenshotParam(
                    type = "computer_screenshot",
                    image_url = f"data:image/png;base64,{screenshot}"),
                acknowledged_safety_checks = self.state.pending_safety_checks)
        else:
            next_input = openai.types.responses.response_input_param.Message(
                role = "user",
                content = user_message)
        tools = [self.computer_tool()]
        self.state = None
        wait_time = 0
        for _ in range(10):
            try:
                time.sleep(wait_time)
                next_response = self.client.responses.create(
                    model = self.model,
                    input = [next_input],
                    previous_response_id = previous_response_id,
                    tools = tools,
                    reasoning = { "generate_summary": "concise" },
                    truncation = "auto")
                self.state = State(next_response)
                return
            except openai.RateLimitError as e:
                match = re.search(r"Please try again in (\d+)s", e.message)
                wait_time = int(match.group(1)) if match else 10
                logger.info("Rate limit exceeded. Waiting for %s seconds.", wait_time)
        logger.critical("Max retries exceeded.")

    def computer_tool(self):
        return openai.types.responses.ComputerToolParam(
            type = "computer_use_preview",
            display_width = self.computer.dimensions[0],
            display_height = self.computer.dimensions[1],
            environment = self.computer.environment
        )
