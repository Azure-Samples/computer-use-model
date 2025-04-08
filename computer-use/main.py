'''
This is a basic example of how to use the CUA model along with the Responses API.
The CUA model will take the screenshot of the current screen, and then take action to try and complete the task.
Make sure to install the required packages before running the script.
'''

import argparse
import logging
import os

import openai

import cua
import local_computer


def main():
    logging.basicConfig(level=logging.WARNING, format='%(message)s')
    logging.getLogger("cua").setLevel(logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument("--instructions", dest="instructions", help="Instructions to follow", default="Open web browser and go to microsoft.com.")
    parser.add_argument("--model", dest="model", default="computer-use-preview")
    parser.add_argument("--endpoint", default="azure", help="The endpoint to use, either openai or azure")
    parser.add_argument("--autoplay", dest="autoplay", help="Autoplay VM actions without confirmation, only pause when the turn ends", action="store_true", default=True)
    parser.add_argument("--environment", dest="environment", default="linux")
    parser.add_argument("--vm-address", dest="vm_address", help="The address of the VM to use", type=str, default=None)
    args = parser.parse_args()

    if args.endpoint == "azure":
        client = openai.AzureOpenAI(
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            api_version="2025-03-01-preview")
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
    user_message = args.instructions if args.instructions else input("Please enter the initial task for the computer: ")

    print(f"User: {user_message}")
    agent.start_task(user_message)
    while True:
        user_message = None
        if agent.requires_consent and not args.autoplay:
            input("Press Enter to run computer tool...")
        elif agent.pending_safety_checks and not args.autoplay:
            input(f"Press Enter to acknowledge the following safety checks: {agent.pending_safety_checks}...")
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
