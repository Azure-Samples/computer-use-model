# Computer Use Assistant (CUA)
> **Important:** You must apply for access in order to use the Computer Use model. Apply here: https://aka.ms/oai/cuaaccess

This is a sample repository demonstrating how to use the Computer Use model, an AI model capable of interacting with graphical user interfaces (GUIs) through natural language instructions. The Computer Use model can understand visual interfaces, take actions, and complete tasks by controlling a computer just like a human would.

This framework provides a bridge between the Computer Use model and computer control, allowing for automated task execution while maintaining safety checks and user consent. It serves as a practical example of how to integrate the Computer Use model into applications that require GUI interaction.

## Features

* Natural language computer control through AI models
* Screenshot capture and analysis
* Mouse and keyboard control
* Safety checks and user consent mechanisms
* Support for both OpenAI and Azure OpenAI endpoints
* Cross-platform compatibility (Windows, macOS, Linux)
* Screen resolution scaling for consistent AI model input

## Getting Started

### Prerequisites

* Python 3.7 or higher
* Operating System: Windows, macOS, or Linux
* OpenAI API key or Azure OpenAI credentials

### Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd computer-use
```

2. Install the required packages:
```bash
pip install -r requirements.txt
```

3. Set up your environment variables:

**For macOS or Linux:**
```bash
# Azure OpenAI
export AZURE_OPENAI_ENDPOINT="your-azure-endpoint"
export AZURE_OPENAI_API_KEY="your-azure-api-key"

# OpenAI
export OPENAI_API_KEY="your-openai-api-key"
```
**For Windows:**
```powershell
# Azure OpenAI
setx AZURE_OPENAI_ENDPOINT "your-azure-endpoint"
setx AZURE_OPENAI_API_KEY "your-azure-api-key"

# OpenAI
setx OPENAI_API_KEY "your-openai-api-key"
```

## Usage

### Local Computer Control

The framework is designed to work directly with your local computer. Here's how to use it:

1. Run the example application:
```bash
python main.py --instructions "Open web browser and go to microsoft.com"
```

2. The AI model will:
   - Take screenshots of your screen
   - Analyze the visual information
   - Execute appropriate actions to complete the task
   - Request user consent for safety-critical actions

### Command Line Arguments

* `--instructions`: The task to perform (default: "Open web browser and go to microsoft.com")
* `--model`: The AI model to use (default: "computer-use-preview")
* `--endpoint`: The API endpoint to use ("azure" or "openai", default: "azure")
* `--autoplay`: Automatically execute actions without confirmation (default: true)

### VM/Remote Control

For scenarios requiring remote computer control or VM automation, we recommend using Playwright. Playwright provides robust browser automation capabilities and is well-suited for VM-based testing and automation scenarios.

For more information on VM automation with Playwright, please refer to:
* [Playwright Documentation](https://playwright.dev/docs/intro)
* [Playwright VM Setup Guide](https://playwright.dev/docs/ci-intro)

## Demo

The included demo application (`main.py`) demonstrates how to use the CUA framework:

1. Start the demo:
```bash
python main.py
```

2. Enter your instructions when prompted, or use the `--instructions` parameter to provide them directly.

3. Watch as the AI model:
   - Captures and analyzes your screen
   - Performs mouse and keyboard actions
   - Requests consent for safety-critical operations
   - Provides reasoning for its actions

## Resources

* [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)
* [Azure OpenAI Documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
* [PyAutoGUI Documentation](https://pyautogui.readthedocs.io/)
