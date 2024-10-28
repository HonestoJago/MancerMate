# cogs/events.py

import discord
from discord.ext import commands
from discord.ui import View, Button, Select
import logging

logger = logging.getLogger('discord')

class TemperatureSelect(Select):
    def __init__(self, user_id, original_message):
        options = [
            discord.SelectOption(
                label="Low Creativity (0.7)",
                description="More focused and deterministic responses",
                value="0.7"
            ),
            discord.SelectOption(
                label="Medium Creativity (1.0)",
                description="Balanced responses",
                value="1.0"
            ),
            discord.SelectOption(
                label="High Creativity (1.3)",
                description="More varied and creative responses",
                value="1.3"
            ),
            discord.SelectOption(
                label="Maximum Creativity (1.5)",
                description="Most unpredictable responses",
                value="1.5"
            )
        ]
        super().__init__(
            placeholder="Select temperature for this reroll...",
            min_values=1,
            max_values=1,
            options=options
        )
        self.user_id = user_id
        self.original_message = original_message

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("You cannot use this control.", ephemeral=True)
            return

        temperature = float(self.values[0])
        await interaction.response.defer()

        # Get necessary managers
        conversation_manager = interaction.client.conversation_manager
        response_message_id = conversation_manager.get_response_message_id(self.user_id)

        # Get the channel and message to be replaced
        channel = interaction.channel
        try:
            ai_message = await channel.fetch_message(response_message_id)
        except discord.NotFound:
            await interaction.followup.send("Original message not found.", ephemeral=True)
            return

        # Show typing indicator while generating response
        async with channel.typing():
            # Generate new response with custom temperature
            ai_client = interaction.client.ai_client
            new_response = await ai_client.chat_with_model(
                self.user_id,
                self.original_message,
                conversation_manager,
                username=interaction.user.name,
                reroll=True,
                temperature=temperature
            )

        if isinstance(new_response, str):
            # Delete old message and send new one
            await ai_message.delete()
            
            view = View()
            view.add_item(ReRollButton(user_id=self.user_id))
            view.add_item(ContinueButton(user_id=self.user_id))
            view.add_item(ClearHistoryButton(user_id=self.user_id))

            new_message = await channel.send(
                new_response.encode('utf-8', errors='ignore').decode('utf-8'),
                view=view
            )
            conversation_manager.save_response_message_id(self.user_id, new_message.id)
            conversation_manager.update_last_response(self.user_id, new_response)

            await interaction.followup.send(
                f"Response re-rolled with temperature {temperature}",
                ephemeral=True
            )

class TemperatureView(View):
    def __init__(self, user_id, original_message):
        super().__init__()
        self.add_item(TemperatureSelect(user_id, original_message))

class ReRollButton(Button):
    def __init__(self, user_id):
        super().__init__(label="Re-roll", style=discord.ButtonStyle.primary)
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("You cannot use this button.", ephemeral=True)
            return

        # Get the original message
        conversation_manager = interaction.client.conversation_manager
        original_message = conversation_manager.get_original_message(self.user_id)

        # Show temperature selector
        view = TemperatureView(self.user_id, original_message)
        await interaction.response.send_message(
            "Choose the creativity level for this reroll:",
            view=view,
            ephemeral=True
        )

class ContinueButton(Button):
    def __init__(self, user_id):
        # Change secondary to success for green color
        super().__init__(label="Continue", style=discord.ButtonStyle.success)
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("You cannot use this button.", ephemeral=True)
            return

        await interaction.response.defer()
        
        # Get last response
        conversation_manager = interaction.client.conversation_manager
        last_response = conversation_manager.get_last_response(self.user_id)
        
        if not last_response:
            await interaction.followup.send("There's no previous response to continue from.", ephemeral=True)
            return

        # Add typing indicator
        async with interaction.channel.typing():
            # Generate continuation
            continuation = await interaction.client.ai_client.chat_with_model(
                self.user_id,
                "Please continue from where you left off, but finish quickly.",
                conversation_manager,
                username=interaction.user.name
            )

            if isinstance(continuation, str):
                # Create view with buttons
                view = View()
                view.add_item(ReRollButton(user_id=self.user_id))
                view.add_item(ContinueButton(user_id=self.user_id))
                view.add_item(ClearHistoryButton(user_id=self.user_id))
                
                # Update conversation history with the continuation
                conversation_manager.update_last_response(self.user_id, last_response + "\n\n" + continuation)
                
                await interaction.followup.send(continuation, view=view)
                logger.info("Continued response via button.", 
                           extra={'user_id': self.user_id, 'command': 'continue_button'})
            else:
                await interaction.followup.send(continuation, ephemeral=True)

class ClearHistoryButton(Button):
    def __init__(self, user_id):
        super().__init__(label="Clear History", style=discord.ButtonStyle.danger)
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("You cannot use this button.", ephemeral=True)
            return

        # Create confirmation view
        view = ConfirmClearView(self.user_id)
        await interaction.response.send_message(
            "Are you sure you want to clear your conversation history?", 
            view=view, 
            ephemeral=True
        )

class ConfirmClearView(View):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("You cannot use this button.", ephemeral=True)
            return

        conversation_manager = interaction.client.conversation_manager
        conversation_manager.clear_history(self.user_id)
        
        # Disable the buttons after use
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(
            content="Your conversation history has been cleared.", 
            view=self
        )
        logger.info("Cleared conversation history via button.", 
                   extra={'user_id': self.user_id, 'command': 'clear_history_button'})

    @discord.ui.button(label="No", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("You cannot use this button.", ephemeral=True)
            return

        # Disable the buttons after use
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(
            content="History clear cancelled.", 
            view=self
        )

class BotEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_allowed_channel(self, channel_id: int) -> bool:
        from config.settings import ALLOWED_CHANNEL_IDS
        return channel_id in ALLOWED_CHANNEL_IDS

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user or message.author.bot:
            return

        if not self.is_allowed_channel(message.channel.id) and not isinstance(message.channel, discord.DMChannel):
            return

        try:
            # Check for direct mentions, replies, or DMs
            is_mentioned = self.bot.user.mentioned_in(message)
            is_reply_to_bot = message.reference and message.reference.resolved and message.reference.resolved.author == self.bot.user
            is_dm = isinstance(message.channel, discord.DMChannel)

            if is_mentioned or is_reply_to_bot or is_dm:
                # Process mentions in the message
                processed_content = message.content
                mentioned_users = []
                for mention in message.mentions:
                    processed_content = processed_content.replace(f'<@{mention.id}>', f'@{mention.name}')
                    mentioned_users.append(mention.name)

                async with message.channel.typing():
                    response = await self.bot.ai_client.chat_with_model(
                        message.author.id,
                        processed_content,
                        self.bot.conversation_manager,
                        username=message.author.name
                    )

                if isinstance(response, str):
                    # Truncate response if needed
                    if len(response) > 1900:
                        response = response[:1900] + "..."

                    # Save the original message for re-roll
                    self.bot.conversation_manager.save_original_message(message.author.id, processed_content)

                    # Create a view with the re-roll button
                    view = View()
                    view.add_item(ReRollButton(user_id=message.author.id))
                    view.add_item(ContinueButton(user_id=message.author.id))
                    view.add_item(ClearHistoryButton(user_id=message.author.id))

                    # Send the AI response and save the message ID
                    ai_response_message = await message.reply(
                        response.encode('utf-8', errors='ignore').decode('utf-8'), 
                        view=view
                    )
                    self.bot.conversation_manager.save_response_message_id(message.author.id, ai_response_message.id)
                else:
                    # If response is not a string, it's likely an error message
                    await message.reply(response, ephemeral=True)

        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            logger.error(error_msg, extra={'user_id': message.author.id, 'command': 'on_message'})
            await message.channel.send(f"An error occurred while processing your message: {str(e)}")



