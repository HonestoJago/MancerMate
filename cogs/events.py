import discord
from discord.ext import commands
import logging

logger = logging.getLogger('discord')

class BotEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_allowed_channel(self, channel_id: int) -> bool:
        from config.settings import ALLOWED_CHANNEL_IDS
        return channel_id in ALLOWED_CHANNEL_IDS

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
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

                if response:
                    # Truncate response if needed
                    if len(response) > 1900:
                        response = response[:1900] + "..."
                    
                    await message.reply(response.encode('utf-8', errors='ignore').decode('utf-8'))
                else:
                    logger.error("Empty response received from AI client", 
                                extra={'user_id': message.author.id, 'command': 'on_message'})
                    await message.reply("I received an empty response from the AI service. Please try again.")

        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            logger.error(error_msg, extra={'user_id': message.author.id, 'command': 'on_message'})
            await message.channel.send(f"An error occurred while processing your message: {str(e)}")
