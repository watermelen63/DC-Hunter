import discord
import os
import asyncio
import logging
import ollama
import json
import random
import chat
import analysis
import employ
from dotenv import load_dotenv

app = discord.Bot(intents = discord.Intents.all())

load_dotenv()
DC_HUNTER_TOKEN = os.getenv("DC_HUNTER_TOKEN")

@app.event
async def on_ready():
	print(f"{app.user} is now running!")

if __name__ == "__main__":
    app.run(DC_HUNTER_TOKEN)