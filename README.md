# MancerMate

**MancerMate** is an AI-powered Discord bot that leverages Mancer AI's advanced language models to engage in meaningful and/or fun conversations.

> **Disclaimer:**  
> *MancerMate is an independent project and is not affiliated with, endorsed by, or in any way officially connected to Mancer AI. Neither the creator of MancerMate nor their work represents Mancer AI.*

## Features

### Core Features
- **Advanced Conversational AI:** Engage in dynamic, context-aware conversations using Mancer's powerful language models
- **Multi-Model Support:** Compatible with Magnum-72b, Magnum-72b-v4, and Goliath-120b models
- **Interactive UI:** Includes buttons for re-rolling responses, continuing conversations, and clearing history
- **Customizable Temperature:** Choose creativity levels when re-rolling responses
- **Conversation Management:** Individual conversation tracking and automatic context management
- **Secure Configuration:** Environment variables for sensitive information
- **Comprehensive Logging:** Detailed logging system with custom formatting

### Commands
- `/help` - Display available commands
- `/clear_history` - Clear your conversation history
- `/get_params` - View current AI parameters (Admin)
- `/load_params` - Load AI parameters from JSON (Admin)
- `/continue` - Continue from the last response
- `/show_history` - View and optionally save your conversation history

### UI Features
- **Re-roll Button:** Generate alternative responses with adjustable creativity
- **Continue Button:** Extend the current response
- **Clear History Button:** Quick access to history clearing
- **Temperature Selection:** Choose from multiple creativity levels when re-rolling

## Installation

### Prerequisites

- Python 3.8+
- Discord Account and Bot Token
- [Mancer AI API Key](https://mancer.tech/)

### Setup Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/HonestoJago/MancerMate.git
   cd MancerMate
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   ```

3. **Activate Virtual Environment**
   - Windows CMD: `venv\Scripts\activate.bat`
   - Windows PowerShell: `venv\Scripts\Activate.ps1`
   - Unix/MacOS: `source venv/bin/activate`

4. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure Environment**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your:
   - Mancer AI API key
   - Discord bot token
   - Allowed channel IDs

6. **Launch the Bot**
   ```bash
   python bot.py
   ```

## Configuration

### Environment Variables
Configure in `.env`:
- `API_KEY`: Your Mancer AI API key
- `DISCORD_TOKEN`: Discord bot token
- `ALLOWED_CHANNEL_IDS`: Comma-separated channel IDs

### AI Parameters
- Located in `textgen/*.json`
- Customize temperature, top_p, and other generation parameters
- Load different parameter sets with `/load_params`

### System Prompt
- Edit `preloads/example_dialogue.json`
- Modify `ai_personality` to change the bot's personality
- Example dialogue can be enabled/disabled via `load_example_dialogue`

## Advanced Features

### Re-rolling Responses
- Click the "Re-roll" button on any bot response
- Choose from multiple creativity levels:
  - Low (0.7): More focused responses
  - Medium (1.0): Balanced creativity
  - High (1.3): More varied responses
  - Maximum (1.5): Most creative/unpredictable

### Conversation Management
- Individual conversation tracking per user
- Automatic token limit management
- History can be viewed and saved with `/show_history`
- Clear history via button or command

### Logging System
- Comprehensive logging with custom formatting
- Tracks user IDs and commands
- Detailed API error handling and reporting

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see [LICENSE.txt](LICENSE.txt) for details.

## Acknowledgments

- [Mancer AI](https://mancer.tech/) for their powerful language models
- The Discord.py community
- All contributors and users of MancerMate

---

For support, feature requests, or bug reports, please open an issue on GitHub.
