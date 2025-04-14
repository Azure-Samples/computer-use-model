import base64
import io
import json
import logging
import re
import time
import typing

import openai
import PIL

logger = logging.getLogger(__name__)


class State:
    "Tracking and controlling the state."

    previous_response_id: str
    next_action: typing.Literal[
        "user_interaction", "computer_call_output", "function_call"
    ] = ""
    call_id: str = ""
    computer_action: str = ""
    computer_action_args: dict = {}
    pending_safety_checks: list = []
    reasoning_summary: str = ""
    message: str = ""

    def __init__(self, response):
        assert response.status == "completed"
        self.previous_response_id = response.id
        for item in response.output:
            if item.type == "computer_call":
                self.next_action = "computer_call_output"
                self.call_id = item.call_id
                self.computer_action_args = vars(item.action) | {}
                self.computer_action = self.computer_action_args.pop("type")
                self.pending_safety_checks = item.pending_safety_checks
            elif item.type == "reasoning":
                self.reasoning_summary = "".join([entry.text for entry in item.summary])
            elif item.type == "message":
                self.next_action = "user_interaction"
                self.message += item.content[-1].text
            elif item.type == "function_call":
                self.next_action = "function_call"
                self.call_id = item.call_id
                self.tool_name = item.name
                self.tool_args = json.loads(item.arguments)
            else:
                message = (f"Unsupported response output type '{item.type}'.",)
                raise NotImplementedError(message)


class Scaler:
    """Wrapper for a computer that performs resizing and coordinate translation."""

    def __init__(self, computer, dimensions=None):
        self.computer = computer
        self.dimensions = dimensions
        if not self.dimensions:
            # If no dimensions are given, take a screenshot and scale to fit in 2048px
            # https://platform.openai.com/docs/guides/images
            image = self._screenshot()
            width, height = image.size
            max_size = 2048
            longest = max(width, height)
            if longest <= max_size:
                self.dimensions = (width, height)
            else:
                scale = max_size / longest
                self.dimensions = (int(width * scale), int(height * scale))
        self.environment = computer.environment
        self.screen_width = -1
        self.screen_height = -1

    def screenshot(self) -> str:
        # Take a screenshot from the actual computer
        image = self._screenshot()
        # Scale the screenshot
        self.screen_width, self.screen_height = image.size
        width, height = self.dimensions
        ratio = min(width / self.screen_width, height / self.screen_height)
        new_width = int(self.screen_width * ratio)
        new_height = int(self.screen_height * ratio)
        new_size = (new_width, new_height)
        resized_image = image.resize(new_size, PIL.Image.Resampling.LANCZOS)
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

    def _screenshot(self):
        # Take screenshot from the actual computer.
        screenshot = self.computer.screenshot()
        screenshot = base64.b64decode(screenshot)
        buffer = io.BytesIO(screenshot)
        return PIL.Image.open(buffer)

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
        self.tools = {}

    def start_task(self, user_message):
        response = self.client.responses.create(
            model=self.model,
            input=user_message,
            tools=self.get_tools(),
            truncation="auto",
        )
        self.state = State(response)

    def add_tool(self, tool, func):
        name = tool["name"]
        self.tools[name] = (tool, func)

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
            next_input = openai.types.responses.response_input_param.ComputerCallOutput(
                type="computer_call_output",
                call_id=self.state.call_id,
                output=openai.types.responses.response_input_param.ResponseComputerToolCallOutputScreenshotParam(
                    type="computer_screenshot",
                    image_url=f"data:image/png;base64,{screenshot}",
                ),
                acknowledged_safety_checks=self.state.pending_safety_checks,
            )
        elif self.state.next_action == "function_call":
            if self.state.tool_name not in self.tools:
                raise ValueError(f"Unsupported tool '{self.state.tool_name}'.")
            tool, func = self.tools[self.state.tool_name]
            result = func(**self.state.tool_args)
            next_input = openai.types.responses.response_input_param.FunctionCallOutput(
                type="function_call_output",
                call_id=self.state.call_id,
                output=json.dumps(result),
            )
        else:
            next_input = openai.types.responses.response_input_param.Message(
                role="user", content=user_message
            )
        self.state = None
        wait_time = 0
        for _ in range(10):
            try:
                time.sleep(wait_time)
                next_response = self.client.responses.create(
                    model=self.model,
                    input=[next_input],
                    previous_response_id=previous_response_id,
                    tools=self.get_tools(),
                    reasoning={"generate_summary": "concise"},
                    truncation="auto",
                )
                self.state = State(next_response)
                return
            except openai.RateLimitError as e:
                match = re.search(r"Please try again in (\d+)s", e.message)
                wait_time = int(match.group(1)) if match else 10
                logger.info("Rate limit exceeded. Waiting for %s seconds.", wait_time)
        logger.critical("Max retries exceeded.")

    def get_tools(self):
        tools = [entry[0] for entry in self.tools.values()]
        return [self.computer_tool(), *tools]

    def computer_tool(self):
        return openai.types.responses.ComputerToolParam(
            type="computer_use_preview",
            display_width=self.computer.dimensions[0],
            display_height=self.computer.dimensions[1],
            environment=self.computer.environment,
        )
