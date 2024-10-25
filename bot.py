import discord
from discord.ext import commands
from config.settings import DISCORD_TOKEN, API_KEY, ALLOWED_CHANNEL_IDS
from utils.logger import setup_logger
from services.ai_client import AIClient
from services.conversation_manager import ConversationManager
from cogs.commands import BotCommands
from cogs.events import BotEvents

class MancerMate(commands.Bot):
    def __init__(self):
        # Set up intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guild_messages = True
        
        super().__init__(command_prefix='!', intents=intents)
        
        # Initialize services
        self.ai_client = AIClient()
        self.conversation_manager = ConversationManager()
        
        # Set up logger
        self.logger = setup_logger()

        # Add global check for regular commands
        self.add_check(self.globally_allowed_channel)

    def globally_allowed_channel(self, ctx):
        """Global check for regular commands"""
        if not ctx.channel.id in ALLOWED_CHANNEL_IDS and not isinstance(ctx.channel, discord.DMChannel):
            return False
        return True

    async def setup_hook(self):
        """Initialize async components and load cogs"""
        await self.ai_client.initialize()
        await self.add_cog(BotCommands(self))
        await self.add_cog(BotEvents(self))
        
        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} command(s)")
        except Exception as e:
            print(f"Failed to sync commands: {e}")

    async def on_ready(self):
        """Called when the bot is ready"""
        print(f'{self.user} has connected to Discord!')
        print(f'Connected to {len(self.guilds)} guilds:')
        for guild in self.guilds:
            print(f' - {guild.name} (id: {guild.id})')

    async def close(self):
        """Clean up resources when shutting down"""
        await self.ai_client.close()
        await super().close()

def main():
    # Validate required environment variables
    if not API_KEY or not DISCORD_TOKEN:
        raise ValueError("API_KEY and DISCORD_TOKEN must be set in the .env file")

    # Create and run bot
    bot = MancerMate()
    bot.run(DISCORD_TOKEN)

if __name__ == "__main__":
    main()
