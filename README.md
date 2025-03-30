# Computer Use Assistant (CUA)

> **Important:** You must apply for access to use the Computer Use model. [Apply here](https://aka.ms/oai/cuaaccess)

Welcome to the Computer Use Assistant (CUA) sample repository! This project demonstrates how to create an AI assistant that can interact with your computer's graphical interface using natural language commands. Think of it as having a helpful assistant that can understand what's on your screen and perform actions just like you would.

## What Can It Do?

- 🗣️ Understand natural language instructions to control your computer
- 👀 See and analyze what's on your screen
- 🖱️ Control mouse and keyboard actions safely
- 🔒 Built-in safety checks and user consent mechanisms
- 🌐 Works with both OpenAI and Azure OpenAI
- 💻 Cross-platform support (Windows, macOS, Linux)
- 🎯 Automatically adjusts for different screen resolutions

## Quick Start Guide

### Before You Begin

1. Make sure you have:
   - Python 3.7 or newer installed (Check with `python --version` or `python3 --version`)
   - Access to the "computer-use-preview" model ([apply here](https://aka.ms/oai/cuaaccess))
   - Either an OpenAI API key or Azure OpenAI credentials

### Setting Up Your Environment

1. **Get the Code:**
   ```bash
   git clone https://github.com/your-username/computer-use-model.git
   cd computer-use-model/computer-use
   ```

2. **Create Your Virtual Environment:**
   ```bash
   # Create a new virtual environment
   python -m venv .venv

   # Activate it:
   # On macOS/Linux:
   source .venv/bin/activate
   # On Windows (Command Prompt):
   .venv\Scripts\activate.bat
   # On Windows (PowerShell):
   .venv\Scripts\Activate.ps1
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

   The project now includes Playwright for advanced browser automation! It will be installed automatically with the dependencies.

### Configure Your API Access

1. **Set Up Your Environment File:**
   ```bash
   # Create your .env file from the example
   cp .env.example .env
   ```

2. **Edit Your `.env` File:**
   
   For Azure OpenAI:
   ```env
   AZURE_OPENAI_ENDPOINT="https://your-instance.openai.azure.com/"
   AZURE_OPENAI_API_KEY="your-azure-api-key"
   ```

   For OpenAI:
   ```env
   OPENAI_API_KEY="your-openai-api-key"
   ```

### Running Your First Command

1. **Basic Usage:**
   ```bash
   python main.py --instructions "Open the Calculator app"
   ```

2. **Using OpenAI Instead of Azure:**
   ```bash
   python main.py --endpoint openai --instructions "Open Notepad and type 'Hello World'"
   ```

### Special Notes for macOS Users

On macOS, you'll need to grant accessibility permissions:
1. Go to `System Settings > Privacy & Security > Accessibility`
2. Add and enable your terminal app (Terminal.app, VS Code, etc.)
3. You may need to restart your terminal after granting permissions

## Advanced Features

### Browser Automation with Playwright

The project now includes Playwright for powerful browser automation capabilities! This enables:
- Reliable web testing and automation
- Cross-browser support (Chromium, Firefox, WebKit)
- Mobile browser emulation
- Network interception and mocking

To use Playwright features:
1. Playwright is automatically installed with the project dependencies
2. Browser binaries are also automatically installed
3. Example tests are available in the `tests` directory

Run Playwright tests:
```bash
npx playwright test
```

View test results:
```bash
npx playwright show-report
```

### Command Line Options

- `--instructions`: What you want the AI to do (default: "Open web browser and go to microsoft.com")
- `--model`: AI model to use (default: "computer-use-preview")
- `--endpoint`: Choose `azure` or `openai` (default: "azure")
- `--autoplay`: Set to `false` to confirm each action (default: true)
- `--environment`: Your operating system (detected automatically)
- `--vm-address`: For remote/VM control (advanced usage)

## Safety and Security

- The AI will ask for confirmation before performing critical actions
- Your API keys are kept secure in the `.env` file (never commit this file!)
- The system includes built-in safety checks
- You can use `--autoplay false` for maximum control

## Troubleshooting Tips

1. **API Key Issues:**
   - Double-check your `.env` file configuration
   - Verify you have the correct permissions for the model

2. **Permission Errors:**
   - Make sure you've granted accessibility permissions (especially on macOS)
   - Try running your terminal/IDE with administrator privileges

3. **Screen Control Issues:**
   - Verify your screen resolution is properly detected
   - Check if your terminal has the necessary permissions

4. **Browser Automation Issues:**
   - Run `npx playwright install` to ensure browsers are properly installed
   - Check Playwright's debug logs with `PWDEBUG=1` environment variable

## Getting Help

- Check the [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)
- Visit [Azure OpenAI Documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- Explore [Playwright Documentation](https://playwright.dev/docs/intro) for browser automation
- Review [PyAutoGUI Documentation](https://pyautogui.readthedocs.io/) for screen control
- File an issue on our GitHub repository

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.
