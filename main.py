"""
Python Setup
"""
import os

from dotenv import load_dotenv
import discord
from discord.ext import commands
import logging

from plugins.Base import BaseCog
from plugins.LaundryAlarm import LaundryAlarmCog
from plugins.StableDiffusion import StableDiffusionCog
# from plugins.Music import MusicCog

load_dotenv()

"""
CONSTANTS
"""
COMMAND_DEBUG = "$debug"
COMMAND_SHUTDOWN = "$shutdown"
COMMAND_SYNC = "$sync"
COMMAND_G_SYNC = "$gsync"

MESSAGE_SHUTDOWN = "Shutting Down"
MESSAGE_SYNC_BEGIN = "Syncing Command Tree..."
MESSAGE_SYNC_COMPLETE = "Sync Complete"
MESSAGE_USER_UNAUTHORISED = "User is unauthorised"

GUILD_ID="367619323294121986"

"""
Discord Bot Setup
"""
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='a')

BOT_TOKEN = os.getenv('DISCORD_TOKEN')
BOT_OWNER_ID = os.getenv('DISCORD_BOT_OWNER_ID')

intents = discord.Intents.default()
intents.message_content = True

activity = discord.CustomActivity(name='Taking Over The World', emoji=None)

bot = commands.Bot(command_prefix='$', intents=intents, activity=activity)


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if isinstance(message.channel, discord.DMChannel):
        if message.author.id != int(os.getenv('DISCORD_BOT_OWNER_ID')):
            await message.channel.send(MESSAGE_USER_UNAUTHORISED)
            return
        if message.content == COMMAND_DEBUG:
            await message.channel.send("DEBUG_PLACE_HOLDER")
        if message.content == COMMAND_SYNC:
            await message.channel.send(MESSAGE_SYNC_BEGIN)
            await bot.tree.sync()
            await message.channel.send(MESSAGE_SYNC_COMPLETE)
        if message.content == COMMAND_G_SYNC:
            await message.channel.send(MESSAGE_SYNC_BEGIN)
            await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
            await message.channel.send(MESSAGE_SYNC_COMPLETE)
        if message.content == COMMAND_SHUTDOWN:
            await message.channel.send(MESSAGE_SHUTDOWN)
            await bot.close()

    # Command Processing
    await bot.process_commands(message)


@bot.event
async def on_ready():
    print(f'{bot.user} Initialising')
    await bot.add_cog(BaseCog(bot))
    # await bot.add_cog(MusicCog(bot))
    # await bot.add_cog(LaundryAlarmCog(bot))
    await bot.add_cog(StableDiffusionCog(bot))
    # await bot.tree.sync()
    print(f'{bot.user} Initialised')


bot.run(BOT_TOKEN, log_handler=handler)
