import json
import discord
from discord import app_commands, Choice

with open("data/define_traits.json", "r", encoding="utf-8") as f:
    DEFINE_TRAITS = json.load(f)

bot = discord.Bot(intents=discord.Intents.all())


@bot.slash_command(name = "查看人格定義", description = "輸入此指令後，DC_Hunter會輸出那九種人格的定義")
async def check_traits(ctx):
    # 因為內容太長，我們建立多個 Embed 來避免超過 Discord 限制
    embeds = []
    
    # 將九種人格分成幾個 Embed 發送（例如每 3 個一組，或是一個大 Embed 包含全部）
    main_embed = discord.Embed(title="📜 九型人格完整定義總覽", color=discord.Color.blue())
    
    for key, value in DEFINE_TRAITS.items():
        main_embed.add_field(
            name=f"【{key.capitalize()}】",
            value=value[:1024], # 確保不超過單個 field 限制
            inline=False
        )
    
    await ctx.respond(embed=main_embed)
    #await 

@app_commands.command(name = "choose", description = "你需要什麼性格的人")
@app_commands.describe(personality = "選擇個性")
@app_commands.choices(
    personality = [
        Choice(name = "完美主義者", value = "perfectionist"),
        Choice(name = "助人者", value = "helper"),
        Choice(name = "成就者", value = "achiever"),
        Choice(name = "個人主義者", value = "individualist"),
        Choice(name = "探索者", value = "investigator"),
        Choice(name = "忠誠者", value = "loyalist"),
        Choice(name = "樂觀者", value = "enthusiast"),
        Choice(name = "挑戰者", value = "challenger"),
        Choice(name = "和平主義者", value = "peacemaker"),
    ]
)
async def choose(self, interaction=discord.Interaction):
    
    
    await interaction.response.send_message(f"你想要找的人有這些：")
