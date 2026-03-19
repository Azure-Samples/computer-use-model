# GPT-5.4 Computer Use

A sample application that uses GPT-5.4 Computer Use to control a computer through natural language instructions. It captures screenshots, analyzes the GUI, and performs mouse and keyboard actions to complete tasks — with support for safety checks, user consent, and both OpenAI and Azure OpenAI endpoints.

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

* Python 3.10 or higher
* Operating System: Windows, macOS, or Linux
* OpenAI API key or Azure OpenAI credentials

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Azure-Samples/computer-use
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
export AZURE_OPENAI_ENDPOINT="azure-endpoint"
export AZURE_OPENAI_API_KEY="azure-api-key"

# OpenAI
export OPENAI_API_KEY="openai-api-key"
```
**For Windows:**
```powershell
# Azure OpenAI
setx AZURE_OPENAI_ENDPOINT "azure-endpoint"
setx AZURE_OPENAI_API_KEY "azure-api-key"

# OpenAI
setx OPENAI_API_KEY "openai-api-key"
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
* `--model`: The AI model to use (default: "gpt-5.4")
* `--endpoint`: The API endpoint to use ("azure" or "openai", default: "azure")

### VM/Remote Control

For scenarios requiring remote computer control or VM automation, we recommend using Playwright. Playwright provides robust browser automation capabilities and is well-suited for VM-based testing and automation scenarios.

For more information on VM automation with Playwright, please refer to:
* [Playwright Documentation](https://playwright.dev/docs/intro)
* [Playwright VM Setup Guide](https://playwright.dev/docs/ci-intro)

## Resources

* [OpenAI API Computer Use Documentation](https://developers.openai.com/api/docs/guides/tools-computer-use)
* [Azure OpenAI Documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
* [PyAutoGUI Documentation](https://pyautogui.readthedocs.io/)
