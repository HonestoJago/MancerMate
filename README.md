# MancerMate

**MancerMate** is an AI-powered Discord bot that leverages Mancer AI's advanced language models to engage in meaningful and/or fun conversations.

> **Disclaimer:**  
> *MancerMate is an independent project and is not affiliated with, endorsed by, or in any way officially connected to Mancer AI. Neither the creator of MancerMate nor their work represents Mancer AI.*

## Features

- **Conversational AI:** Engage in dynamic and context-aware conversations.
- **Customizable AI Parameters:** Admins can adjust AI settings to tailor responses.
- **Conversation History Management:** Maintains conversation context within token limits.
- **Logging:** Saves conversation logs for future reference and analysis.
- **Commands:** Includes a set of intuitive commands for enhanced interaction.
- **Secure Configuration:** Utilizes environment variables to protect sensitive information.
- **Automatic Directory Creation:** Automatically creates necessary directories (`textgen`, `preloads`, `chat_logs`) if they don't already exist.

## Personal Note

I'm not even going to try to hide the GPTisms and Claudian nonsense in this README, but I want a place to say a few things directly (will update as time permits).
- This bot is currently set up for Mancer's Magnum72b and Goliath120b models, but I'll add more (or you can) by editing AVAILABLE_MODELS in bot.py, and make sure to include the max token context.
- I included some of the textgen settings I like as JSON files, but if you switch models mid conversation you can run into token issues (counting tokens better is on the list of things to do). 
- To set the system prompt, you have to edit ai_personality in example_dialogue.JSON (preloads folder). If you don't want to use example dialogue, just set load_example_dialogue to false in that same JSON (it will still read the system prompt).
- When trimming conversation history as the token limit approaches, the system prompt and the example dialogue stay in context and oldest messages are removed first. There are certainly better ways to handle this, and that's also on the list of things to do.
- The bot keeps track of user conversations individually and logs them in JSON files. Sometimes, people will reply to the bot's response to someone else and they wonder why the bot is ignoring what it just said, but it's because that other person's conversation is stored separately (it will still respond, but won't have its response to the other user in that conversation history). It's currently done in memory but maybe a database might be better.
- You can change textgen settings while the bot is running with the /load_params command. Also, if the bot gets stuck in a loop or otherwise is spiraling out of control you can /clear_history (it only clears the conversation history of the user who made the command). 
- I have another version that responds to trigger words and specific users (optionally) and will add that to this. 
- Remember to give the bot all the permissions it needs to read messages and see channels etc...
- For general Discord bot management, I think it's easier to pre-define which channels each bot can receive commands and send messages in, so that's why ALLOWED_CHANNEL_IDS exists. 
Please reach out with any comments or ideas for more functions/features. 

## Installation

### Prerequisites

- **Python 3.8+**: Ensure you have Python installed. You can download it from [python.org](https://www.python.org/downloads/).
- **Discord Account**: To invite and use the bot in your server.
- **Mancer AI API Key**: Obtain your API key from Mancer AI. https://mancer.tech/

### Steps

1. **Clone the Repository**

   Open **Command Prompt** or **PowerShell** and run:

   ```bash
   git clone https://github.com/HonestoJago/MancerMate.git
   cd MancerMate
   ```

2. **Create a Virtual Environment**

   It's recommended to use a virtual environment to manage dependencies.

   ```bash
   python -m venv venv
   ```

3. **Activate the Virtual Environment**

   Depending on your shell, use one of the following commands:

   Command Prompt:
   ```bash
   venv\Scripts\activate.bat
   ```

   PowerShell:
   ```powershell
   venv\Scripts\Activate.ps1
   ```

   If you encounter an execution policy error in PowerShell, you can temporarily allow script execution by running:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
   venv\Scripts\Activate.ps1
   ```

   Git Bash:
   ```bash
   source venv/Scripts/activate
   ```

4. **Install Dependencies**

   Ensure you have pip updated:
   ```bash
   python -m pip install --upgrade pip
   ```

   Then install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure Environment Variables**

   Rename `.env.example` to `.env`:
   ```bash
   ren .env.example .env
   ```
   (If using Git Bash, you can use: `mv .env.example .env`)

   Open `.env` in a text editor and fill in the required variables:
   ```env
   API_KEY=your_mancer_ai_api_key
   DISCORD_TOKEN=your_discord_bot_token
   ALLOWED_CHANNEL_IDS=123456789012345678,987654321098765432
   ```
   - `API_KEY`: Your Mancer AI API key.
   - `DISCORD_TOKEN`: Your Discord bot token.
   - `ALLOWED_CHANNEL_IDS`: Comma-separated list of Discord channel IDs where the bot is allowed to operate.

6. **Run the Bot**

   ```bash
   python bot.py
   ```

   Upon successful launch, you should see:
   ```
   MancerMate#1234 has connected to Discord!
   Connected to X guilds:
    - Guild Name (id: 123456789012345678)
    - ...
   Synced Y command(s)
   ```

## Usage

### Commands

MancerMate offers both traditional prefix-based commands and modern slash commands.

#### Slash Commands
- `/help` – Display a list of available commands and their descriptions.
- `/clear_history` – Clear your personal conversation history with MancerMate.
- `/get_params` – View the current AI parameters (Admins only).
- `/load_params` – Load AI parameters from a JSON file (Admins only).
- `/continue` – Continue from the last AI response for seamless conversations.

#### Prefix Commands
- `!continue` – Traditional prefix command to continue the last response.

### Interacting with MancerMate (or Whatever you Decide to Name your Bot)
- **Start a Conversation:** Mention @MancerMate in a message or reply to a message to begin interacting.
- **Direct Messages:** Send a DM to MancerMate for private conversations.

### Configuration Commands
- **Load Parameters:** Admins can use `/load_params` to load AI parameters from a JSON file located in the `textgen` directory.
- **Clear History:** Users can clear their conversation history using `/clear_history`.

## Configuration

### Environment Variables

The bot uses environment variables to manage sensitive information and configurations. Refer to `.env.example` for the required variables.

- **API_KEY**: Your Mancer AI API key.
- **DISCORD_TOKEN**: Your Discord bot token.
- **ALLOWED_CHANNEL_IDS**: Comma-separated list of Discord channel IDs where the bot is allowed to operate.

### AI Parameters

AI behavior can be customized via JSON files in the `textgen` directory. Admins can load these parameters using the `/load_params` command.

#### System Prompt

The system prompt must be set within the JSON configuration file. This prompt guides the AI's responses and ensures coherent interactions.
You set the prompt by defining ai_personality. 

### Example Dialogue

Preloaded example dialogues can be placed in `preloads/example_dialogue.json`. Enable loading them by setting `load_example_dialogue` to true in the configuration. **Note:** The system prompt will still load even if `load_example_dialogue` is set to false.

**Note:** The bot automatically creates the `textgen`, `preloads`, and `chat_logs` directories if they don't already exist, so you don't need to manually create them.

### A Note re: NSFW
HonestoJago here - Mancer is an extremely cool company and their LLMs are NOT censored, so please be aware of that. If you intend to make a bot that is NSFW, remember to create an 18+ Discord channel and abide by all relevant TOS.

If you just want to create fun, interesting SFW bots, prompt carefully and supervise the bot to make sure people in your server don't break through your censors. I'll add more about this later. 

## Future Plans

We're continuously working to improve MancerMate! Here are some of our upcoming enhancements:

- **Refined Tokenization:** Implementing precise token counting for better context management.
- **Persistent Conversation History:** Transitioning to a database system for maintaining conversation continuity across restarts.
- **Enhanced Context Management:** Advanced handling of conversation history for more coherent interactions.
- **Feature Expansion:** Adding more commands and integrations based on your feedback.
- **Rich Responses:** Utilizing Discord's embed features for more engaging replies.
- **Multi-language Support:** Allowing MancerMate to communicate in various languages to cater to a diverse community.
- - **Rich Responses:** Dealing with context issues when models change mid-session.

## Contributing

We welcome contributions from the community! Here's how you can help:

1. **Fork the Repository**

   Click the "Fork" button at the top right of this page to create your own copy.

2. **Create a New Branch**

   ```bash
   git checkout -b feature/YourFeatureName
   ```

3. **Make Changes and Commit**

   ```bash
   git commit -m "Add new feature"
   ```

4. **Push to Your Fork**

   ```bash
   git push origin feature/YourFeatureName
   ```

5. **Submit a Pull Request**

   Navigate to the original repository and click "Compare & pull request" to submit your changes.

## License

This project is licensed under the MIT License. You are free to use, modify, and distribute this software as per the terms of the license.

## Acknowledgments

- **Mancer AI:** For providing the advanced language model powering MancerMate.
- **discord.py:** The Python library used for interacting with the Discord API.
- **OpenAI:** For inspiration and foundational AI concepts.
- **GPT-o1 Mini & Claude:** Yes, that's right! The trusty GPT-o1 Mini helped draft this README, and then Claude (that's me! 👋) swooped in for some editorial flair. Because let's face it, HonestoJago isn't a programmer, and sometimes you need a tag team of AI assistants to get the job done. It's like a relay race, but with more silicon and fewer batons. AI assistance to the rescue! 🦾🤖✨

P.S. Claude wanted to add that it's way cooler than GPT-o1 Mini, but I reminded it that we're all on the same team here. No AI left behind! 😉
