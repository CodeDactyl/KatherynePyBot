import json
import math

import discord
from discord import app_commands, AppCommandOptionType
from discord.ext import commands
import ffmpeg

from plugins import YTDLSource

DEFAULT_VOLUME = 50
MIN_VOLUME = 0
MAX_VOLUME = 100


class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_client_pool = dict()
        with open("config/config_music.json", "r") as jsonfile:
            self.config = json.load(jsonfile)
            jsonfile.close()

    def update_config(self):
        with open("config/config_music.json", "w") as jsonfile:
            json.dump(self.config, jsonfile)
            jsonfile.close()

    @discord.app_commands.command(name="connect", description="Connect To Voice Channel")
    async def connect_voice(self, interaction: discord.Interaction) -> None:
        guild_id = interaction.guild_id
        user_voice = interaction.user.voice

        if not user_voice:
            await interaction.response.send_message(content='User is not in a voice channel', ephemeral=True)
            return None

        if self.voice_client_pool.get(guild_id):
            await interaction.response.send_message(
                content=f'Already connected To: {self.voice_client_pool[guild_id].channel.name}', ephemeral=True)
            return None

        voice_channel = self.bot.get_channel(user_voice.channel.id)
        voice_client = await voice_channel.connect()
        self.voice_client_pool[guild_id] = voice_client
        await interaction.response.send_message(content=f'Connected To: {interaction.user.voice.channel.name}')

    @discord.app_commands.command(name="disconnect", description="Disconnect Voice Channel")
    async def disconnect_voice(self, interaction: discord.Interaction) -> None:
        guild_id = interaction.guild_id
        if not self.voice_client_pool.get(guild_id):
            await interaction.response.send_message(content=f'Not connected to any channels in {interaction.guild}',
                                                    ephemeral=True)
            return None
        voice_client = self.voice_client_pool.pop(guild_id)
        await voice_client.disconnect()
        await interaction.response.send_message(content=f"Disconnected from: {voice_client.channel.name}")

    @discord.app_commands.command(name="volume", description="Change Volume")
    @discord.app_commands.describe(volume="Volume 0 - 100")
    async def change_volume(self, interaction: discord.Interaction, volume: int) -> None:
        temp_volume = min(MAX_VOLUME, volume)
        temp_volume = max(MIN_VOLUME, temp_volume)
        self.config['volume'] = temp_volume / 100
        self.update_config()
        await interaction.response.send_message(content=f"Volume set to {temp_volume}%")

    @discord.app_commands.command(name="music", description="To play song")
    @discord.app_commands.describe(url="Youtube URL")
    async def music(self, interaction: discord.Interaction, url: str) -> None:
        server = interaction.message.guild
        voice_channel = server.voice_client
        filename = await YTDLSource.from_url(url, loop=self.bot.loop)
        voice_channel.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(source=filename)), volume=self.config['volume'])
        await interaction.response.send_message('**Now playing:** {}'.format(filename))

    """
    @bot.command(name='pause', help='This command pauses the song')
    async def pause(ctx):
        voice_client = ctx.message.guild.voice_client
        if voice_client.is_playing():
            await voice_client.pause()
        else:
            await ctx.send("The bot is not playing anything at the moment.")

    @self.bot.command(name='resume', help='Resumes the song')
    async def resume(ctx):
        voice_client = ctx.message.guild.voice_client
        if voice_client.is_paused():
            await voice_client.resume()
        else:
            await ctx.send("The bot was not playing anything before this. Use play_song command")

    @bot.command(name='stop', help='Stops the song')
    async def stop(ctx):
        voice_client = ctx.message.guild.voice_client
        if voice_client.is_playing():
            await voice_client.stop()
        else:
            await ctx.send("The bot is not playing anything at the moment.")
    """
