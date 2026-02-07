import discord
from discord import app_commands
from discord.app_commands import Choice

bot = discord.Bot(intents = discord.Intents.all())

@app_commands.command(name = "choose", description = "你需要什麼性格的人")
@app_commands.describe(personality = "選擇個性")
@app_commands.choices(
    personality = [
        Choice(name = "型", value = "    "),
        Choice(name = "型", value = "    "),
        Choice(name = "型", value = "    "),
        Choice(name = "型", value = "    "),
        Choice(name = "型", value = "    "),
        Choice(name = "型", value = "    "),
        Choice(name = "型", value = "    "),
        Choice(name = "型", value = "    "),
        Choice(name = "型", value = "    "),
        Choice(name = "型", value = "    "),
    ]
)
async def choose(self, interaction=discord.Interaction):
    
    
    await interaction.response.send_message(f"你想要找的人有這些：  ")
