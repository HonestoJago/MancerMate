import json
import os
import discord
from discord import app_commands
from discord.ext import commands
import logging
from config.settings import TEXTGEN_DIR, DEFAULT_AI_PARAMS, AVAILABLE_MODELS

logger = logging.getLogger('discord')

def is_in_allowed_channel():
    async def predicate(interaction: discord.Interaction):
        from config.settings import ALLOWED_CHANNEL_IDS
        if not interaction.channel_id in ALLOWED_CHANNEL_IDS and not isinstance(interaction.channel, discord.DMChannel):
            await interaction.response.send_message("This command can only be used in the designated channels.", ephemeral=True)
            return False
        return True
    return app_commands.check(predicate)

class BotCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="load_params", description="Load AI parameters from a file")
    @app_commands.describe(
        file_name="Name of the JSON file containing parameters",
        public="Make the response visible to everyone"
    )
    @app_commands.checks.has_permissions(administrator=True)
    @is_in_allowed_channel()
    async def slash_load_params(self, interaction: discord.Interaction, file_name: str, public: bool = False):
        try:
            file_path = os.path.join(TEXTGEN_DIR, file_name)
            with open(file_path, 'r', encoding='utf-8') as file:
                new_params = json.load(file)

            global DEFAULT_AI_PARAMS
            DEFAULT_AI_PARAMS.update(new_params)

            response = f"Parameters successfully loaded from {file_name}."

            # Update the current_token_limit if the model has changed
            if "model" in new_params and new_params["model"] in AVAILABLE_MODELS:
                self.bot.conversation_manager.current_token_limit = AVAILABLE_MODELS[new_params["model"]]
                response += f"\nToken limit updated to {self.bot.conversation_manager.current_token_limit} for model {new_params['model']}."

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

    @app_commands.command(name="clear_history", description="Clear your conversation history with the bot")
    @is_in_allowed_channel()
    async def slash_clear_history(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            user_id = interaction.user.id
            self.bot.conversation_manager.clear_history(user_id)
            response = f"{interaction.user.name}, your conversation history has been cleared."
            await interaction.followup.send(response, ephemeral=True)
            logger.info("Cleared conversation history.", extra={'user_id': user_id, 'command': 'clear_history'})

        except Exception as e:
            error_message = "An error occurred while clearing your history. Please try again later."
            logger.error(f"Error clearing history: {str(e)}", extra={'user_id': interaction.user.id, 'command': 'clear_history'})
            await interaction.followup.send(error_message, ephemeral=True)

    @app_commands.command(name="get_params", description="Get current AI parameters")
    @app_commands.describe(public="Make the response visible to everyone")
    @is_in_allowed_channel()
    async def slash_get_params(self, interaction: discord.Interaction, public: bool = False):
        params_str = "\n".join([f"{k}: {v}" for k, v in DEFAULT_AI_PARAMS.items()])
        response = f"Current parameters:\n```\n{params_str}\n```"
        await interaction.response.send_message(response, ephemeral=not public)
        logger.info("Displayed AI parameters.", extra={'user_id': interaction.user.id, 'command': 'get_params'})

    @app_commands.command(name="help", description="List available commands")
    @is_in_allowed_channel()
    async def slash_help(self, interaction: discord.Interaction):
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

    @app_commands.command(name="continue", description="Continue the last response")
    @is_in_allowed_channel()
    async def slash_continue(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        last_response = self.bot.conversation_manager.get_last_response(user_id)
        
        if last_response:
            await interaction.response.defer()
            continuation_prompt = "Please continue from where you left off, but finish quickly."
            continuation = await self.bot.ai_client.chat_with_model(
                user_id, 
                continuation_prompt, 
                self.bot.conversation_manager,
                username=interaction.user.name
            )
            
            # Truncate response if needed
            if len(continuation) > 1900:
                continuation = continuation[:1900] + "..."
                
            await interaction.followup.send(continuation)
            logger.info("Continued last response.", extra={'user_id': user_id, 'command': 'continue'})
        else:
            await interaction.response.send_message("There's no previous response to continue.", ephemeral=True)