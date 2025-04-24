import base64
import io
import json
import re
import time

import openai
import PIL


class Scaler:
    """Wrapper for a computer that performs resizing and coordinate translation."""

    def __init__(self, computer, dimensions=None):
        self.computer = computer
        self.dimensions = dimensions
        self.screen_width = -1
        self.screen_height = -1

    def get_environment(self):
        return self.computer.get_environment()

    def get_dimensions(self):
        if not self.dimensions:
            # If no dimensions are given, take a screenshot and scale to fit in 2048px
            # https://platform.openai.com/docs/guides/images
            width, height = self.computer.get_dimensions()
            max_size = 2048
            longest = max(width, height)
            if longest <= max_size:
                self.dimensions = (width, height)
            else:
                scale = max_size / longest
                self.dimensions = (int(width * scale), int(height * scale))
        return self.dimensions

    def screenshot(self) -> str:
        # Take a screenshot from the actual computer
        screenshot = self.computer.screenshot()
        screenshot = base64.b64decode(screenshot)
        buffer = io.BytesIO(screenshot)
        image = PIL.Image.open(buffer)
        # Scale the screenshot
        self.screen_width, self.screen_height = image.size
        width, height = self.get_dimensions()
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
            x, y = self._point_to_screen_coords(point["x"], point["y"])
            point["x"] = x
            point["y"] = y
        self.computer.drag(path)

    def _point_to_screen_coords(self, x, y):
        width, height = self.get_dimensions()
        ratio = min(width / self.screen_width, height / self.screen_height)
        x = x / ratio
        y = y / ratio
        return int(x), int(y)


class Agent:
    """CUA agent to start and continue task execution"""

    def __init__(self, client, model, computer, logger=None):
        self.client = client
        self.model = model
        self.computer = computer
        self.logger = logger
        self.tools = {}
        self.repsonse = None

    def start_task(self, user_message):
        self.response = self.client.responses.create(
            model=self.model,
            input=user_message,
            tools=self.get_tools(),
            truncation="auto",
        )
        assert self.response.status == "completed"

    def add_tool(self, tool, func):
        name = tool["name"]
        self.tools[name] = (tool, func)

    @property
    def requires_user_input(self):
        return not any(
            item.type in ("computer_call", "function_call")
            for item in self.response.output
        )

    @property
    def requires_consent(self):
        return any(item.type == "computer_call" for item in self.response.output)

    @property
    def pending_safety_checks(self):
        items = [item for item in self.response.output if item.type == "computer_call"]
        return [check for item in items for check in item.pending_safety_checks]

    @property
    def reasoning_summary(self):
        items = [item for item in self.response.output if item.type == "reasoning"]
        return "".join([summary.text for item in items for summary in item.summary])

    @property
    def message(self):
        messages = [item for item in self.response.output if item.type == "message"]
        return "".join([item.content[-1].text for item in messages])

    @property
    def actions(self):
        actions = []
        for item in self.response.output:
            if item.type == "computer_call":
                action_args = vars(item.action) | {}
                action = action_args.pop("type")
                if action == "drag":
                    path = [{"x": point.x, "y": point.y} for point in item.action.path]
                    action_args["path"] = path
                actions.append((action, action_args))
        return actions

    def continue_task(self, user_message=""):
        next_input = None
        screenshot = ""
        response_input_param = openai.types.responses.response_input_param
        for item in self.response.output:
            if item.type == "computer_call":
                assert next_input is None
                action, action_args = self.actions[0]
                method = getattr(self.computer, action)
                method(**action_args)
                screenshot = self.computer.screenshot()
                next_input = response_input_param.ComputerCallOutput(
                    type="computer_call_output",
                    call_id=item.call_id,
                    output=response_input_param.ResponseComputerToolCallOutputScreenshotParam(
                        type="computer_screenshot",
                        image_url=f"data:image/png;base64,{screenshot}",
                    ),
                    acknowledged_safety_checks=self.pending_safety_checks,
                )
            elif item.type == "function_call":
                assert next_input is None
                tool_name = item.name
                tool_args = json.loads(item.arguments)
                if tool_name not in self.tools:
                    raise ValueError(f"Unsupported tool '{tool_name}'.")
                tool, func = self.tools[tool_name]
                result = func(**tool_args)
                next_input = response_input_param.FunctionCallOutput(
                    type="function_call_output",
                    call_id=item.call_id,
                    output=json.dumps(result),
                )
            elif item.type == "message":
                assert next_input is None
                next_input = response_input_param.Message(
                    role="user", content=user_message
                )
            elif item.type == "reasoning":
                pass
            else:
                message = (f"Unsupported response output type '{item.type}'.",)
                raise NotImplementedError(message)
        previous_response = self.response
        self.response = None
        wait = 0
        for _ in range(10):
            try:
                time.sleep(wait)
                self.response = self.client.responses.create(
                    model=self.model,
                    input=[next_input],
                    previous_response_id=previous_response.id,
                    tools=self.get_tools(),
                    reasoning={"generate_summary": "concise"},
                    truncation="auto",
                )
                assert self.response.status == "completed"
                return
            except openai.RateLimitError as e:
                match = re.search(r"Please try again in (\d+)s", e.message)
                wait = int(match.group(1)) if match else 10
                if self.logger:
                    message = f"Rate limit exceeded. Waiting for {wait} seconds."
                    self.logger.info(message)
        if self.logger:
            self.logger.critical("Max retries exceeded.")

    def get_tools(self):
        tools = [entry[0] for entry in self.tools.values()]
        return [self.computer_tool(), *tools]

    def computer_tool(self):
        environment = self.computer.get_environment()
        dimensions = self.computer.get_dimensions()
        return openai.types.responses.ComputerToolParam(
            type="computer_use_preview",
            display_width=dimensions[0],
            display_height=dimensions[1],
            environment=environment,
        )
