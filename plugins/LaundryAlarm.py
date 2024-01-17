import asyncio
import random
import time
import json
from datetime import datetime, timedelta

import discord
from discord.ext import commands, tasks

CONFIG_FILE = "config/config_laundry.json"
CHANNEL_ID_BOT_SPAM = 367639155456475136
LAUNDRY_ALARM_TARGET = 367619323294121991
LAUNDRY_ALARM_FILE = "local_storage/mp3/dougdoug_laundry_alarm.mp3"
LAUNDRY_ALARM_MIN_TARGET = 4
LAUNDRY_ALARM_ARMING_USERS = 5
LAUNDRY_ALARM_ARMING_MESSAGE = "{} Is Arming Laundry Alarm: {}/{}"
LAUNDRY_ALARM_RANDOM_LOWER_BOUND = 0
LAUNDRY_ALARM_RANDOM_UPPER_BOUND = 525600


class LaundryAlarmCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open(CONFIG_FILE, "r") as jsonfile:
            self.config = json.load(jsonfile)
            jsonfile.close()
        self.laundry_bomb.start()

    def update_config(self):
        with open(CONFIG_FILE, "w") as jsonfile:
            json.dump(self.config, jsonfile)
            jsonfile.close()

    @discord.app_commands.command(name="arm_laundry", description="Arms Laundry Alarm")
    async def arm_laundry_alarm(self, interaction: discord.Interaction):
        if not self.config.get('LAUNDRY_ALARM_ARMED_USERS'):
            self.config['LAUNDRY_ALARM_ARMED_USERS'] = {}
            self.update_config()
        if self.config['LAUNDRY_ALARM_ARMED_USERS'].get(interaction.user.id):
            await interaction.response.send_message("User Has Already Armed The Laundry Alarm")
        else:
            self.config['LAUNDRY_ALARM_ARMED_USERS'][interaction.user.id] = datetime.now().isoformat()
            self.update_config()
            message = LAUNDRY_ALARM_ARMING_MESSAGE.format(interaction.user.name,
                                                          len(list(self.config['LAUNDRY_ALARM_ARMED_USERS'].keys())),
                                                          LAUNDRY_ALARM_ARMING_USERS)
            await interaction.response.send_message(message, ephemeral=False)

            if len(list(self.config['LAUNDRY_ALARM_ARMED_USERS'].keys())) >= LAUNDRY_ALARM_ARMING_USERS:
                await interaction.channel.send("Laundry Alarm Has Been Armed", tts=True)
                self.config['laundry_alarm_armed'] = True
                arming_time = datetime.now()
                self.config['laundry_alarm_armed_time'] = arming_time.isoformat()
                self.update_config()

    @tasks.loop(seconds=60.0)
    async def laundry_bomb(self):
        if self.config.get('laundry_alarm_armed') is None:
            self.config['laundry_alarm_armed'] = False
            self.update_config()
            return

        if not self.config['laundry_alarm_armed']:
            return

        # Figure out detonation time
        arming_time = datetime.fromisoformat(self.config['laundry_alarm_armed_time'])
        random.seed(hash(arming_time))
        detonation_delay = random.randint(LAUNDRY_ALARM_RANDOM_LOWER_BOUND, LAUNDRY_ALARM_RANDOM_UPPER_BOUND)

        if datetime.now() < arming_time + timedelta(seconds=detonation_delay):
            return

        channel = self.bot.get_channel(LAUNDRY_ALARM_TARGET)

        if not channel:
            return

        if len(channel.members) >= LAUNDRY_ALARM_MIN_TARGET:
            voice_client = await channel.connect()
            voice_client.play(
                discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(LAUNDRY_ALARM_FILE), volume=1.0))
            while voice_client.is_playing():
                await asyncio.sleep(.1)
            await voice_client.disconnect()

            # Post Detonation
            text_channel = self.bot.get_channel(CHANNEL_ID_BOT_SPAM)
            await text_channel.send("Laundry Alarm Detonated At {}".format(datetime.now()))
            self.config['laundry_alarm_armed'] = False
            self.config['LAUNDRY_ALARM_ARMED_USERS'] = {}
            self.config['laundry_alarm_armed_time'] = None
            self.update_config()
