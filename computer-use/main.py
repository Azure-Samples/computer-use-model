"""
This is a basic example of how to use the CUA model along with the Responses API.
The code will run a loop taking screenshots and perform actions suggested by the model.
Make sure to install the required packages before running the script.
"""

import argparse
import logging
import os

import cua
import local_computer
import openai


def main():
    logging.basicConfig(level=logging.WARNING, format="%(message)s")
    logging.getLogger("cua").setLevel(logging.DEBUG)

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
    parser.add_argument("--vm-address", dest="vm_address", type=str,
        default=None, help="The address of the VM to use")
    args = parser.parse_args()

    if args.endpoint == "azure":
        client = openai.AzureOpenAI(
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            api_version="2025-03-01-preview",
        )
    else:
        client = openai.OpenAI()

    model = args.model

    # Computer is used to take screenshots and send keystrokes or mouse clicks
    computer = local_computer.LocalComputer()

    # Scaler is used to resize the screen to a smaller size
    computer = cua.Scaler(computer)

    # Agent to run the CUA model and keep track of state
    agent = cua.Agent(client, model, computer)

    # Get the user request
    if args.instructions:
        user_message = args.instructions
    else:
        user_message = input("Please enter the initial task for the computer: ")

    print(f"User: {user_message}")
    agent.start_task(user_message)
    while True:
        user_message = None
        if agent.requires_consent and not args.autoplay:
            input("Press Enter to run computer tool...")
        elif agent.pending_safety_checks and not args.autoplay:
            print(f"Safety checks: {agent.pending_safety_checks}")
            input("Press Enter to acknowledge and continue...")
        elif agent.requires_user_input:
            user_message = input("User: ")
        agent.continue_task(user_message)
        print("")
        if agent.reasoning_summary:
            print(f"Action: {agent.reasoning_summary}")
        if agent.message:
            print(f"Agent: {agent.message}")
            print("")


if __name__ == "__main__":
    main()
