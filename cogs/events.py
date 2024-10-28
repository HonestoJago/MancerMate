# cogs/events.py

import discord
from discord.ext import commands
from discord.ui import View, Button
import logging

logger = logging.getLogger('discord')

class ReRollButton(Button):
    def __init__(self, user_id):
        super().__init__(label="Re-roll", style=discord.ButtonStyle.primary)
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        # Ensure only the original user can click the button
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("You cannot use this button.", ephemeral=True)
            return

        # Access the ConversationManager via interaction.client
        conversation_manager = interaction.client.conversation_manager
        user_id = self.user_id

        # Remove reroll limit check and counter
        conversation_manager.increment_reroll(user_id)  # Keep this just for logging purposes

        await interaction.response.defer()

        # Retrieve the original message
        original_message = conversation_manager.get_original_message(user_id)
        if not original_message:
            await interaction.followup.send("Original message not found.", ephemeral=True)
            return

        # Retrieve the AI response message ID
        response_message_id = conversation_manager.get_response_message_id(user_id)
        if not response_message_id:
            await interaction.followup.send("Original AI response not found.", ephemeral=True)
            return

        # Fetch the original AI message
        channel = interaction.channel
        try:
            ai_message = await channel.fetch_message(response_message_id)
        except discord.NotFound:
            await interaction.followup.send("Original AI response message not found or has been deleted.", ephemeral=True)
            return
        except discord.Forbidden:
            await interaction.followup.send("I don't have permission to delete the original AI response.", ephemeral=True)
            return
        except discord.HTTPException:
            await interaction.followup.send("Failed to fetch the original AI response message.", ephemeral=True)
            return

        # Generate a new response using the original message
        ai_client = interaction.client.ai_client
        new_response = await ai_client.chat_with_model(
            user_id,
            original_message,
            conversation_manager,
            username=interaction.user.name,
            reroll=True  # Indicate that this is a reroll
        )

        if isinstance(new_response, str):
            # Truncate if necessary
            if len(new_response) > 1900:
                new_response = new_response[:1900] + "..."

            # Delete the original AI message
            try:
                await ai_message.delete()
            except discord.Forbidden:
                await interaction.followup.send("I don't have permission to delete the original AI response.", ephemeral=True)
                return
            except discord.HTTPException:
                await interaction.followup.send("Failed to delete the original AI response message.", ephemeral=True)
                return

            # Send the new AI response with a new re-roll button
            view = View()
            new_button = ReRollButton(user_id=user_id)
            view.add_item(new_button)

            new_ai_response_message = await channel.send(
                new_response.encode('utf-8', errors='ignore').decode('utf-8'),
                view=view
            )
            conversation_manager.save_response_message_id(user_id, new_ai_response_message.id)

            # Update conversation history with the new response
            conversation_manager.update_last_response(user_id, new_response)

            # Reset parameters to their previous state
            conversation_manager.reset_reroll_parameters(user_id)

            # Inform the user
            await interaction.followup.send("Your response has been re-rolled.", ephemeral=True)
            logger.info("Re-rolled response.", extra={'user_id': user_id, 'command': 'reroll'})
        else:
            # If new_response is not a string, it's likely an error message
            await interaction.followup.send(new_response, ephemeral=True)

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
                    button = ReRollButton(user_id=message.author.id)
                    view.add_item(button)

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



