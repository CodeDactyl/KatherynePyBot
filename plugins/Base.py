import os

import discord
from discord.ext import commands

MESSAGE_SHUTDOWN = "Shutting Down"
ERROR_USER_UNAUTHORISED = "User is unauthorised"


class BaseCog(commands.Cog):
    def __init__(self, bot: discord.ext.commands.bot):
        self.bot = bot

    @discord.app_commands.command(name="ping", description="Ping Command")
    async def ping(self, interaction: discord.Interaction) -> None:
        message = "Pong"
        await interaction.response.send_message(content=message, ephemeral=True)

    @discord.app_commands.command(name="stop", description="Shutdown Command")
    async def stop(self, interaction: discord.Interaction) -> None:
        if str(interaction.user.id) != os.getenv('DISCORD_BOT_OWNER_ID'):
            await interaction.response.send_message(content=ERROR_USER_UNAUTHORISED, ephemeral=True)
        else:
            await interaction.response.send_message(content=MESSAGE_SHUTDOWN, ephemeral=True)
            await self.bot.close()
            exit()

    @discord.app_commands.command(name="sync", description="Syncs the command tree", )
    async def sync(self, interaction: discord.Interaction) -> None:
        if str(interaction.user.id) != os.getenv('DISCORD_BOT_OWNER_ID'):
            await interaction.response.send_message(content=ERROR_USER_UNAUTHORISED, ephemeral=True)
        else:
            await interaction.response.defer(ephemeral=True, thinking=True)
            result = await self.bot.tree.sync()
            await interaction.followup.send(result)
