"""
This is a basic example of how to use the CUA model along with the Responses API.
The code will run a loop taking screenshots and perform actions suggested by the model.
Make sure to install the required packages before running the script.
"""

import argparse
import asyncio
import logging
import os

import cua
import local_computer
import openai


async def main():

    logging.basicConfig(level=logging.WARNING, format="%(message)s")
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument("--instructions", dest="instructions",
        default="Open web browser and go to microsoft.com.",
        help="Instructions to follow")
    parser.add_argument("--model", dest="model",
        default="computer-use-preview")
    parser.add_argument("--endpoint", default="azure",
        help="The endpoint to use, either OpenAI or Azure OpenAI")
    parser.add_argument("--autoplay", dest="autoplay", action="store_true",
        default=True, help="Autoplay actions without confirmation")
    parser.add_argument("--environment", dest="environment", default="linux")
    args = parser.parse_args()

    if args.endpoint == "azure":
        client = openai.AsyncAzureOpenAI(
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            api_version="2025-03-01-preview",
        )
    else:
        client = openai.AsyncOpenAI()

    model = args.model

    # Computer is used to take screenshots and send keystrokes or mouse clicks
    computer = local_computer.LocalComputer()

    # Scaler is used to resize the screen to a smaller size
    computer = cua.Scaler(computer, (1024, 768))

    # Agent to run the CUA model and keep track of state
    agent = cua.Agent(client, model, computer)

    # Get the user request
    if args.instructions:
        user_input = args.instructions
    else:
        user_input = input("Please enter the initial task: ")

    logger.info(f"User: {user_input}")
    agent.start_task()
    while True:
        if not user_input and agent.requires_user_input:
            logger.info("")
            user_input = input("User: ")
        await agent.continue_task(user_input)
        user_input = ""
        if agent.requires_consent and not args.autoplay:
            input("Press Enter to run computer tool...")
        elif agent.pending_safety_checks and not args.autoplay:
            logger.info(f"Safety checks: {agent.pending_safety_checks}")
            input("Press Enter to acknowledge and continue...")
        if agent.reasoning_summary:
            logger.info("")
            logger.info(f"Action: {agent.reasoning_summary}")
        for action, action_args in agent.actions:
            logger.info(f"  {action} {action_args}")
        if agent.messages:
            logger.info("")
            logger.info(f"Agent: {"".join(agent.messages)}")

if __name__ == "__main__":
    asyncio.run(main())
