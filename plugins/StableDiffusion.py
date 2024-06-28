import os
import discord
from discord.ext import commands, tasks
from diffusers import StableDiffusionPipeline
from diffusers import DiffusionPipeline
import torch
import uuid
import asyncio
import time
import dotenv
import concurrent.futures

MESSAGE_GENERATE_PROMPT = "Prompt: {}"
MESSAGE_CUDA_STATUS = "Cuda Enabled: {}"
SMALL_AI_MODEL_ID = "OFA-Sys/small-stable-diffusion-v0"
MEDIUM_AI_MODEL_ID = "runwayml/stable-diffusion-v1-5"
LARGE_AI_MODEL_ID = "stabilityai/stable-diffusion-xl-base-1.0"
AI_OFFLOAD = False
LOCAL_STORAGE_AI_OUTPUT = "local_storage/ai_output/"
MESSAGE_DEQUEUE_ITEM = "ID: {} removed from queue. ({})"

def generate_image(pipeline, prompt):
    images = pipeline(prompt=prompt).images[0]
    image_name = str(uuid.uuid1())+".png"
    image_path = LOCAL_STORAGE_AI_OUTPUT + image_name
    images.save(image_path)
    return image_path

class StableDiffusionCog(commands.Cog):
    def __init__(self, bot: discord.ext.commands.bot):
        self.bot = bot
        self.index = 0
        self.queue = []
        self.ai_lock = asyncio.Lock()
        self.ai_task_running = False
        print("VRAM: " + str(torch.cuda.get_device_properties(0).total_memory))
        pipe = DiffusionPipeline.from_pretrained(MEDIUM_AI_MODEL_ID, torch_dtype=torch.float32, use_safetensors=True, safety_checker = None, requires_safety_checker = False)
        pipe.to("cuda")
        self.pipe = pipe
        self.aiconsumer.start()

    @discord.app_commands.command(name="pipeline_a", description="Change AI pipeline stabilityai/stable-diffusion-xl-base-1.0")
    async def pipelineA(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=False, thinking=True)
        del self.pipe
        torch.cuda.empty_cache()
        if os.getenv("AI_FP_16") == "UNAVAILABLE":
            pipe = DiffusionPipeline.from_pretrained(LARGE_AI_MODEL_ID, torch_dtype=torch.float32, use_safetensors=True, safety_checker = None, requires_safety_checker = False)
        else:
            pipe = DiffusionPipeline.from_pretrained(LARGE_AI_MODEL_ID, torch_dtype=torch.float16, use_safetensors=True, variant="fp16", safety_checker = None, requires_safety_checker = False)
        if torch.cuda.get_device_properties(0).total_memory > 6225002496:
            pipe.to("cuda")
        else:
            pipe.enable_model_cpu_offload()
        await interaction.followup.send(content="Pipeline changed")

    @discord.app_commands.command(name="pipeline_b", description="Change AI pipeline runwayml/stable-diffusion-v1-5")
    async def pipelineB(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=False, thinking=True)
        del self.pipe
        torch.cuda.empty_cache()
        if os.getenv("AI_FP_16") == "UNAVAILABLE":
            pipe = DiffusionPipeline.from_pretrained(SMALL_AI_MODEL_ID, torch_dtype=torch.float32, use_safetensors=True, safety_checker = None, requires_safety_checker = False)
        else:
            pipe = DiffusionPipeline.from_pretrained(SMALL_AI_MODEL_ID, torch_dtype=torch.float16, use_safetensors=True, variant="fp16", safety_checker = None, requires_safety_checker = False)
        if torch.cuda.get_device_properties(0).total_memory > 0:
            pipe.to("cuda")
        else:
            pipe.enable_model_cpu_offload()
        await interaction.followup.send(content="Pipeline changed")

    @discord.app_commands.command(name="pipeline_c", description="Change AI pipeline OFA-Sys/small-stable-diffusion-v0")
    async def pipelineC(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=False, thinking=True)
        del self.pipe
        torch.cuda.empty_cache()
        if os.getenv("AI_FP_16") == "UNAVAILABLE":
            pipe = DiffusionPipeline.from_pretrained(LARGE_AI_MODEL_ID, torch_dtype=torch.float32, use_safetensors=True, safety_checker = None, requires_safety_checker = False)
        else:
            pipe = DiffusionPipeline.from_pretrained(LARGE_AI_MODEL_ID, torch_dtype=torch.float16, use_safetensors=True, variant="fp16", safety_checker = None, requires_safety_checker = False)
        if torch.cuda.get_device_properties(0).total_memory > 6225002496:
            pipe.to("cuda")
        else:
            pipe.enable_model_cpu_offload()
        await interaction.followup.send(content="Pipeline changed")

    @discord.app_commands.command(name="cuda", description="CUDA Command")
    async def cuda(self, interaction: discord.Interaction) -> None:
        message = MESSAGE_CUDA_STATUS.format(torch.cuda.is_available())
        await interaction.response.send_message(content=message, ephemeral=True)
    
    @discord.app_commands.command(name="generate", description="AI Prompt Generation Command")
    async def generate(self, interaction: discord.Interaction, user_prompt: str) -> None:
        await interaction.response.defer(ephemeral=False, thinking=True)
        if str(interaction.guild_id) == "367619323294121986":
            await interaction.followup.send(content="FUNCTION DISABLED HERE")
        else:
            self.queue.append((interaction, user_prompt))

    @discord.app_commands.command(name="aidequeue", description="aidequeue")
    async def aidequeue(self, interaction: discord.Interaction, id_queue: int) -> None:
        if len(self.queue) > id_queue and id_queue < 0:
            q_interaction, msg = self.queue.pop(id_queue)
            message = MESSAGE_DEQUEUE_ITEM.format(id_queue, msg)
            await q_interaction.followup.send(content=message)
        else:
            message = "Invalid Operation"
        await interaction.response.send_message(content=message, ephemeral=True)
    
    @tasks.loop(seconds=4.0)
    async def aiconsumer(self):
        if not self.ai_task_running:
            async with self.ai_lock:
                if self.queue:
                    self.ai_task_running = True
            if self.queue:
                interaction, prompt = self.queue.pop(0)
                #file_image = await asyncio.gather(asyncio.to_thread(generate_image(pipeline=self.pipe, prompt=prompt)))
                with concurrent.futures.ProcessPoolExecutor() as executor:
                    future_file_image = executor.submit(generate_image, self.pipe, prompt)
                print(future_file_image.result())
                #file_image = generate_image(pipeline=self.pipe, prompt=prompt)
                reply = MESSAGE_GENERATE_PROMPT.format(prompt)
                #await interaction.followup.send(content=reply, file=discord.File(file_image))
                await interaction.followup.send(content=reply, file=discord.File(future_file_image.result()))
                async with self.ai_lock:
                    self.ai_task_running = False