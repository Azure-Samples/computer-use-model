import asyncio
import base64
import inspect
import io
import json
import re

import openai
import PIL


class Scaler:
    """Wrapper for a computer that performs resizing and coordinate translation."""

    def __init__(self, computer, dimensions: tuple[int, int] | None = None):
        self.computer = computer
        self.size = dimensions
        self.screen_width = -1
        self.screen_height = -1

    @property
    def environment(self):
        return self.computer.environment

    @property
    def dimensions(self):
        if not self.size:
            # If no dimensions are given, take a screenshot and scale to fit in 2048px
            # https://platform.openai.com/docs/guides/images
            width, height = self.computer.dimensions
            max_size = 2048
            longest = max(width, height)
            if longest <= max_size:
                self.size = (width, height)
            else:
                scale = max_size / longest
                self.size = (int(width * scale), int(height * scale))
        return self.size

    async def screenshot(self) -> str:
        # Take a screenshot from the actual computer
        screenshot = await self.computer.screenshot()
        screenshot = base64.b64decode(screenshot)
        buffer = io.BytesIO(screenshot)
        image = PIL.Image.open(buffer)
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

    async def click(self, x: int, y: int, button: str = "left") -> None:
        x, y = self._point_to_screen_coords(x, y)
        await self.computer.click(x, y, button=button)

    async def double_click(self, x: int, y: int) -> None:
        x, y = self._point_to_screen_coords(x, y)
        await self.computer.double_click(x, y)

    async def scroll(self, x: int, y: int, scroll_x: int, scroll_y: int) -> None:
        x, y = self._point_to_screen_coords(x, y)
        await self.computer.scroll(x, y, scroll_x, scroll_y)

    async def type(self, text: str) -> None:
        await self.computer.type(text)

    async def wait(self, ms: int = 1000) -> None:
        await self.computer.wait(ms)

    async def move(self, x: int, y: int) -> None:
        x, y = self._point_to_screen_coords(x, y)
        await self.computer.move(x, y)

    async def keypress(self, keys: list[str]) -> None:
        await self.computer.keypress(keys)

    async def drag(self, path: list[tuple[int, int]]) -> None:
        path = [self._point_to_screen_coords(*point) for point in path]
        await self.computer.drag(path)

    def _point_to_screen_coords(self, x, y):
        width, height = self.dimensions
        ratio = min(width / self.screen_width, height / self.screen_height)
        x = x / ratio
        y = y / ratio
        return int(x), int(y)


class Agent:
    """CUA agent to start and continue task execution"""

    def __init__(self, client, model: str, computer, logger=None):
        self.client = client
        self.model = model
        self.computer = computer
        self.logger = logger
        self.tools = {}
        self.repsonse = None

    def add_tool(self, tool: dict, func):
        name = tool["name"]
        self.tools[name] = (tool, func)

    @property
    def requires_user_input(self) -> bool:
        if self.response is None or len(self.response.output) == 0:
            return True
        item = self.response.output[-1]
        return item.type == "message" and item.role == "assistant"

    @property
    def requires_consent(self) -> bool:
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
    def messages(self) -> list[str]:
        result: list[str] = []
        if self.response:
            for item in self.response.output:
                if item.type == "message":
                    for content in item.content:
                        if content.type == "output_text":
                            result.append(content.text)
        return result

    @property
    def actions(self):
        actions = []
        for item in self.response.output:
            if item.type == "computer_call":
                action_args = vars(item.action) | {}
                action = action_args.pop("type")
                if action == "drag":
                    path = [(point.x, point.y) for point in item.action.path]
                    action_args["path"] = path
                actions.append((action, action_args))
        return actions

    def start_task(self):
        self.response = None

    async def continue_task(self, user_message: str = "", temperature = None):
        inputs = []
        screenshot = ""
        response_input_param = openai.types.responses.response_input_param
        previous_response = self.response
        previous_response_id = None
        if previous_response:
            previous_response_id = previous_response.id
            for item in previous_response.output:
                if item.type == "computer_call":
                    action, action_args = self.actions[0]
                    method = getattr(self.computer, action)
                    if action != "screenshot":
                        result = method(**action_args)
                        if inspect.isawaitable(result):
                            result = await result
                    screenshot = self.computer.screenshot()
                    if inspect.isawaitable(screenshot):
                        screenshot = await screenshot
                    output = response_input_param.ComputerCallOutput(
                        type="computer_call_output",
                        call_id=item.call_id,
                        output=response_input_param.ResponseComputerToolCallOutputScreenshotParam(
                            type="computer_screenshot",
                            image_url=f"data:image/png;base64,{screenshot}",
                        ),
                        acknowledged_safety_checks=self.pending_safety_checks,
                    )
                    inputs.append(output)
                elif item.type == "function_call":
                    tool_name = item.name
                    tool_args = json.loads(item.arguments)
                    if tool_name not in self.tools:
                        raise ValueError(f"Unsupported tool '{tool_name}'.")
                    tool, func = self.tools[tool_name]
                    result = func(**tool_args)
                    if inspect.isawaitable(result):
                        result = await result
                    output = response_input_param.FunctionCallOutput(
                        type="function_call_output",
                        call_id=item.call_id,
                        output=json.dumps(result),
                    )
                    inputs.append(output)
                elif item.type == "reasoning" or item.type == "message":
                    pass
                else:
                    message = (f"Unsupported response output type '{item.type}'.",)
                    raise NotImplementedError(message)
        if user_message:
            message = response_input_param.Message(role="user", content=user_message)
            inputs.append(message)
        self.response = None
        wait = 0
        for _ in range(10):
            try:
                await asyncio.sleep(wait)
                self.response = self.client.responses.create(
                    model=self.model,
                    input=inputs,
                    previous_response_id=previous_response_id,
                    tools=self.get_tools(),
                    reasoning={"generate_summary": "concise"},
                    temperature=temperature,
                    truncation="auto",
                )
                if inspect.isawaitable(self.response):
                    self.response = await self.response
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

    def get_tools(self) -> list[openai.types.responses.tool_param.ToolParam]:
        tools = [entry[0] for entry in self.tools.values()]
        return [self.computer_tool(), *tools]

    def computer_tool(self) -> openai.types.responses.ComputerToolParam:
        environment = self.computer.environment
        dimensions = self.computer.dimensions
        return openai.types.responses.ComputerToolParam(
            type="computer_use_preview",
            display_width=dimensions[0],
            display_height=dimensions[1],
            environment=environment,
        )
