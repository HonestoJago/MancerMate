import discord
from discord.ext import commands
from discord import app_commands
import json
import asyncio
import aiohttp
from collections import defaultdict
import logging
import os
import traceback
import re
from dotenv import load_dotenv

# -*- coding: utf-8 -*-

# Set up logging with a custom formatter to handle missing fields
class CustomFormatter(logging.Formatter):
    def format(self, record):
        if not hasattr(record, 'user_id'):
            record.user_id = 'N/A'
        if not hasattr(record, 'command'):
            record.command = 'N/A'
        return super().format(record)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler(filename='bot.log', encoding='utf-8', mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('discord')

# Set the custom formatter
formatter = CustomFormatter(
    fmt='%(asctime)s:%(levelname)s:%(name)s:[UserID:%(user_id)s][Command:%(command)s]: %(message)s'
)
for handler in logger.handlers:
    handler.setFormatter(formatter)

# Load environment variables
load_dotenv()

API_KEY = os.getenv("API_KEY")
API_URL = "https://neuro.mancer.tech/oai/v1/chat/completions"
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Load channel IDs from .env file
ALLOWED_CHANNEL_IDS = set(map(int, os.getenv("ALLOWED_CHANNEL_IDS", "").split(",")))

DEFAULT_AI_PARAMS = {
    "response_config": None,
    "model": "magnum-72b",
    "temperature": 1,
    "min_p": 0.1,
    "top_p": 1,
    "repetition_penalty": 1.05,
    "max_tokens": 200,
    "n": 1,
    "min_tokens": 0,
    "dynatemp_mode": 0,
    "dynatemp_min": 0,
    "dynatemp_max": 2,
    "dynatemp_exponent": 1,
    "presence_penalty": 0,
    "frequency_penalty": 0,
    "top_k": 0,
    "epsilon_cutoff": 0,
    "top_a": 0,
    "typical_p": 1,
    "eta_cutoff": 0,
    "tfs": 1,
    "smoothing_factor": 0,
    "smoothing_curve": 1,
    "mirostat_mode": 0,
    "mirostat_tau": 5,
    "mirostat_eta": 0.1,
    "sampler_priority": [
        "temperature",
        "dynatemp_mode",
        "top_k",
        "top_p",
        "typical_p",
        "epsilon_cutoff",
        "eta_cutoff",
        "tfs",
        "top_a",
        "min_p",
        "mirostat_mode"
    ],
    "logit_bias": None,
    "ignore_eos": False,
    "stop": [],
    "custom_token_bans": [],
    "stream": False,
    "custom_timeout": None,
    "allow_logging": None,
    "logprobs": False,
    "top_logprobs": None
}

AVAILABLE_MODELS = {
    "magnum-72b": 16384,
    "goliath-120b": 6144
}

def is_allowed_channel(channel_id: int) -> bool:
    return channel_id in ALLOWED_CHANNEL_IDS

# Use the current model's context limit
current_token_limit = AVAILABLE_MODELS[DEFAULT_AI_PARAMS["model"]]

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.guild_messages = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Initialize conversation tracking and storage
conversations = defaultdict(list)
last_responses = {}
conversation_counters = defaultdict(int)
new_conversation_started = defaultdict(lambda: True)
new_conversation_needed = defaultdict(bool)

# Create directories if they don't exist
TEXTGEN_DIR = "textgen"
PRELOADS_DIR = "preloads"
CHAT_LOGS_DIR = "chat_logs"

for directory in [TEXTGEN_DIR, PRELOADS_DIR, CHAT_LOGS_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

def load_dialogue_from_json(file_name):
    file_path = os.path.join(PRELOADS_DIR, file_name)
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        if not isinstance(data, dict) or 'config' not in data:
            raise ValueError("Invalid JSON structure. Expected 'config' key.")

        config = data.get('config', {})
        ai_personality = data.get('ai_personality', "")
        dialogue = data.get('dialogue', [])

        if not isinstance(config, dict) or 'load_example_dialogue' not in config:
            raise ValueError("Invalid config structure. Expected 'load_example_dialogue' key.")

        if not isinstance(dialogue, list) or not all(isinstance(item, dict) and 'role' in item and 'content' in item for item in dialogue):
            raise ValueError("Invalid dialogue format")

        return config, ai_personality, dialogue
    except FileNotFoundError:
        logger.error(f"File '{file_path}' not found.", extra={'user_id': 'N/A', 'command': 'load_dialogue_from_json'})
        return {'load_example_dialogue': False}, "", []
    except json.JSONDecodeError:
        logger.error(f"'{file_path}' is not a valid JSON file.", extra={'user_id': 'N/A', 'command': 'load_dialogue_from_json'})
        return {'load_example_dialogue': False}, "", []
    except ValueError as e:
        logger.error(str(e), extra={'user_id': 'N/A', 'command': 'load_dialogue_from_json'})
        return {'load_example_dialogue': False}, "", []
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}", extra={'user_id': 'N/A', 'command': 'load_dialogue_from_json'})
        return {'load_example_dialogue': False}, "", []

# Load example dialogue and AI personality if available
DIALOGUE_FILE = 'example_dialogue.json'
config, AI_PERSONALITY, example_dialogue = load_dialogue_from_json(DIALOGUE_FILE)
LOAD_EXAMPLE_DIALOGUE = config.get('load_example_dialogue', False)

def estimate_tokens(message: str) -> int:
    return len(message) // 4  # Rough estimation

def manage_conversation_length(user_id: int):
    history = conversations[user_id]
    total_tokens = sum(estimate_tokens(msg["content"]) for msg in history)

    # Ensure the system message and pre-loaded conversation are not trimmed
    preloaded_length = len(example_dialogue) + 1 if LOAD_EXAMPLE_DIALOGUE else 1  # +1 for the system message

    while total_tokens > current_token_limit and len(history) > preloaded_length:
        total_tokens -= estimate_tokens(history.pop(preloaded_length)["content"])

def get_next_log_number(user_id: int) -> int:
    pattern = re.compile(f"{user_id}_(\\d+)\\.json")
    max_number = 0
    for filename in os.listdir(CHAT_LOGS_DIR):
        match = pattern.match(filename)
        if match:
            number = int(match.group(1))
            max_number = max(max_number, number)
    return max_number + 1  # This will always return at least 1

def save_conversation_log(user_id: int):
    log_number = get_next_log_number(user_id)
    log_file = os.path.join(CHAT_LOGS_DIR, f"{user_id}_{log_number}.json")
    try:
        with open(log_file, 'w', encoding='utf-8') as file:
            json.dump(conversations[user_id], file, indent=2, ensure_ascii=False)
        logger.info(f"Conversation log saved: {log_file}", extra={'user_id': user_id, 'command': 'save_conversation_log'})
    except Exception as e:
        logger.error(f"Error saving conversation log: {str(e)}", extra={'user_id': user_id, 'command': 'save_conversation_log'})

# Initialize aiohttp_session as None
aiohttp_session = None

@bot.event
async def on_ready():
    global aiohttp_session
    if aiohttp_session is None:
        aiohttp_session = aiohttp.ClientSession()
    global new_conversation_needed
    new_conversation_needed.clear()  # Reset the flags on bot restart
    print(f'{bot.user} has connected to Discord!')
    print(f'Connected to {len(bot.guilds)} guilds:')
    for guild in bot.guilds:
        print(f' - {guild.name} (id: {guild.id})')

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

async def chat_with_model(user_id, new_message, username=None, **kwargs):
    # Ensure aiohttp_session is initialized
    global aiohttp_session
    if aiohttp_session is None:
        aiohttp_session = aiohttp.ClientSession()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    params = DEFAULT_AI_PARAMS.copy()
    params.update(kwargs)

    # Dynamically set the max_tokens from DEFAULT_AI_PARAMS
    DEFAULT_MAX_TOKENS = 200
    max_tokens = DEFAULT_AI_PARAMS.get('max_tokens', DEFAULT_MAX_TOKENS)

    # Adjust max tokens to ensure we don't exceed limits
    params['max_tokens'] = min(params.get('max_tokens', max_tokens), max_tokens)

    # Get user conversation history
    history = conversations[user_id]

    if not history:
        # Add system message for personality (ensures it's the first message)
        system_message = AI_PERSONALITY or "You are a helpful assistant."
        if username:
            system_message += f"\nYou are talking to a Discord user named {username}."
        history.append({"role": "system", "content": system_message})

        # Load pre-loaded conversation from JSON only if LOAD_EXAMPLE_DIALOGUE is True
        if LOAD_EXAMPLE_DIALOGUE:
            history.extend(example_dialogue)

    # Add user message with username if available
    user_message = f"{username}: {new_message}" if username else new_message
    history.append({"role": "user", "content": user_message})

    # Manage token context limit
    manage_conversation_length(user_id)

    # Prepare data to send to API
    data = {
        "messages": history,
        **params
    }

    try:
        async with aiohttp_session.post(API_URL, headers=headers, json=data) as response:
            if response.status == 200:
                response_json = await response.json()
                ai_response = response_json["choices"][0]["message"]["content"]

                # Add assistant's response to history
                history.append({"role": "assistant", "content": ai_response})

                # Save conversation locally
                save_conversation_log(user_id)

                # Trim the conversation if it exceeds current_token_limit
                manage_conversation_length(user_id)

                # Store the last response
                last_responses[user_id] = ai_response

                return ai_response
            else:
                error_text = await response.text()
                error_message = f"API Error {response.status}: {error_text}"
                logger.error(error_message, extra={'user_id': user_id, 'command': 'chat_with_model'})
                return "I'm sorry, but I couldn't process your request at this time."
    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        logger.error(error_message, extra={'user_id': user_id, 'command': 'chat_with_model'})
        return "I'm sorry, but an unexpected error occurred while processing your request."

def truncate_response(response, max_chars=1900):
    if len(response) <= max_chars:
        return response
    return response[:max_chars] + "..."

# Global check for regular commands
@bot.check
def globally_allowed_channel(ctx):
    if not is_allowed_channel(ctx.channel.id) and not isinstance(ctx.channel, discord.DMChannel):
        return False
    return True

# Custom check for slash commands
def is_in_allowed_channel():
    async def predicate(interaction: discord.Interaction):
        if not is_allowed_channel(interaction.channel_id) and not isinstance(interaction.channel, discord.DMChannel):
            await interaction.response.send_message("This command can only be used in the designated channels.", ephemeral=True)
            return False
        return True
    return app_commands.check(predicate)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if not is_allowed_channel(message.channel.id) and not isinstance(message.channel, discord.DMChannel):
        return

    try:
        # Check for direct mentions, replies, or DMs
        is_mentioned = bot.user.mentioned_in(message)
        is_reply_to_bot = message.reference and message.reference.resolved and message.reference.resolved.author == bot.user
        is_dm = isinstance(message.channel, discord.DMChannel)

        if is_mentioned or is_reply_to_bot or is_dm:
            # Process mentions in the message
            processed_content = message.content
            mentioned_users = []
            for mention in message.mentions:
                processed_content = processed_content.replace(f'<@{mention.id}>', f'@{mention.name}')
                mentioned_users.append(mention.name)

            async with message.channel.typing():
                response = await chat_with_model(
                    message.author.id,
                    processed_content,
                    username=message.author.name,
                    mentioned_users=mentioned_users
                )

            if response:
                truncated_response = truncate_response(response)
                if truncated_response:
                    await message.reply(truncated_response.encode('utf-8', errors='ignore').decode('utf-8'))
                else:
                    await message.reply("I'm sorry, but I couldn't generate a valid response.")
            else:
                await message.reply("I'm sorry, but I couldn't generate a response.")

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", extra={'user_id': message.author.id, 'command': 'on_message'})
        await message.channel.send("An unexpected error occurred. Please try again later.")

    # Process other commands
    await bot.process_commands(message)

@bot.tree.command(name="load_params", description="Load AI parameters from a file")
@app_commands.describe(
    file_name="Name of the JSON file containing parameters",
    public="Make the response visible to everyone"
)
@app_commands.checks.has_permissions(administrator=True)
@is_in_allowed_channel()
async def slash_load_params(interaction: discord.Interaction, file_name: str, public: bool = False):
    try:
        file_path = os.path.join(TEXTGEN_DIR, file_name)
        with open(file_path, 'r', encoding='utf-8') as file:
            new_params = json.load(file)

        global DEFAULT_AI_PARAMS
        DEFAULT_AI_PARAMS.update(new_params)

        response = f"Parameters successfully loaded from {file_name}."

        # Update the current_token_limit if the model has changed
        global current_token_limit
        if "model" in new_params and new_params["model"] in AVAILABLE_MODELS:
            current_token_limit = AVAILABLE_MODELS[new_params["model"]]
            response += f"\nToken limit updated to {current_token_limit} for model {new_params['model']}."

    except FileNotFoundError:
        response = f"Error: File '{file_name}' not found in the {TEXTGEN_DIR} directory."
        logger.error(response, extra={'user_id': interaction.user.id, 'command': 'load_params'})
    except json.JSONDecodeError:
        response = f"Error: '{file_name}' is not a valid JSON file."
        logger.error(response, extra={'user_id': interaction.user.id, 'command': 'load_params'})
    except Exception as e:
        response = f"An error occurred: {str(e)}"
        logger.error(response, extra={'user_id': interaction.user.id, 'command': 'load_params'})

    await interaction.response.send_message(response, ephemeral=not public)

@bot.tree.command(name="clear_history", description="Clear your conversation history with the bot")
@is_in_allowed_channel()
async def slash_clear_history(interaction: discord.Interaction):
    try:
        await interaction.response.defer(ephemeral=True)

        user_id = interaction.user.id

        # Set the flag to create a new log file on next conversation
        new_conversation_needed[user_id] = True

        conversations[user_id] = []  # Clear the entire conversation history

        response = f"{interaction.user.name}, your conversation history has been cleared."
        await interaction.followup.send(response, ephemeral=True)

        logger.info("Cleared conversation history.", extra={'user_id': user_id, 'command': 'clear_history'})

    except Exception as e:
        error_message = "An error occurred while clearing your history. Please try again later."
        logger.error(f"Error clearing history: {str(e)}", extra={'user_id': interaction.user.id, 'command': 'clear_history'})
        await interaction.followup.send(error_message, ephemeral=True)

@bot.tree.command(name="get_params", description="Get current AI parameters")
@app_commands.describe(public="Make the response visible to everyone")
@is_in_allowed_channel()
async def slash_get_params(interaction: discord.Interaction, public: bool = False):
    params_str = "\n".join([f"{k}: {v}" for k, v in DEFAULT_AI_PARAMS.items()])
    response = f"Current parameters:\n```\n{params_str}\n```"

    await interaction.response.send_message(response, ephemeral=not public)

    logger.info("Displayed AI parameters.", extra={'user_id': interaction.user.id, 'command': 'get_params'})

@bot.tree.command(name="help", description="List available commands")
@is_in_allowed_channel()
async def slash_help(interaction: discord.Interaction):
    help_text = """
**Available Commands:**
- `/clear_history`: Clear your conversation history with the bot.
- `/get_params`: Get current AI parameters.
- `/continue`: Continue the last response.
- `/load_params`: Load AI parameters from a file (Admin only).
- `/help`: Show this help message.

**How to Interact with the Bot:**
- Mention the bot in a message or reply to the bot's message to start a conversation.
- You can also send a direct message to the bot.
"""
    await interaction.response.send_message(help_text, ephemeral=True)

    logger.info("Displayed help message.", extra={'user_id': interaction.user.id, 'command': 'help'})

@bot.command(name='continue')
async def continue_response(ctx):
    if not is_allowed_channel(ctx.channel.id) and not isinstance(ctx.channel, discord.DMChannel):
        await ctx.send("This command can only be used in the designated channels.")
        return

    user_id = ctx.author.id
    if user_id in last_responses:
        full_response = last_responses[user_id]
        async with ctx.typing():
            continuation_prompt = f"Please continue: '{full_response}'"
            continuation = await chat_with_model(user_id, continuation_prompt, username=ctx.author.name)
            await ctx.send(truncate_response(continuation))

        logger.info("Continued last response.", extra={'user_id': user_id, 'command': 'continue'})
    else:
        await ctx.send("There's no previous response to continue.")

@bot.tree.command(name="continue", description="Continue the last response")
@is_in_allowed_channel()
async def slash_continue(interaction: discord.Interaction):
    user_id = interaction.user.id
    if user_id in last_responses:
        full_response = last_responses[user_id]
        await interaction.response.defer()
        continuation_prompt = f"Please continue: '{full_response}'"
        continuation = await chat_with_model(user_id, continuation_prompt, username=interaction.user.name)
        await interaction.followup.send(truncate_response(continuation))

        logger.info("Continued last response.", extra={'user_id': user_id, 'command': 'continue'})
    else:
        await interaction.response.send_message("There's no previous response to continue.", ephemeral=True)

if not API_KEY or not DISCORD_TOKEN:
    raise ValueError("API_KEY and DISCORD_TOKEN must be set in the .env file")

# Close the aiohttp session when the bot closes
@bot.event
async def on_close():
    global aiohttp_session
    if aiohttp_session is not None:
        await aiohttp_session.close()

bot.run(DISCORD_TOKEN)