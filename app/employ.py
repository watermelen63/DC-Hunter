import json
import os

import discord

TRAITS = [
    "perfectionist",
    "helper",
    "achiever",
    "individualist",
    "investigator",
    "loyalist",
    "enthusiast",
    "challenger",
    "peacemaker",
]

DEFINE_TRAITS_FILE = "data/define_traits.json"
USER_TRAITS_FILE = "data/user_traits.json"


def _load_define_traits():
    if os.path.exists(DEFINE_TRAITS_FILE):
        try:
            with open(DEFINE_TRAITS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _load_user_traits():
    if os.path.exists(USER_TRAITS_FILE):
        try:
            with open(USER_TRAITS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def setup(bot: discord.Bot):
    if getattr(bot, "_employ_setup_done", False):
        return
    bot._employ_setup_done = True

    @bot.slash_command(name="traits", description="查看九型人格特質簡介")
    async def traits(ctx: discord.ApplicationContext):
        define_traits = _load_define_traits()
        if not define_traits:
            await ctx.respond("目前沒有特質說明。")
            return

        embed = discord.Embed(title="九型人格特質簡介", color=discord.Color.blue())
        for key, value in define_traits.items():
            title = key.capitalize()
            embed.add_field(name=title, value=value[:1024], inline=False)

        await ctx.respond(embed=embed)

    @bot.slash_command(name="find_employ", description="選擇特質並找出對應的用戶")
    async def find_employ(
        ctx: discord.ApplicationContext,
        trait: discord.Option(
            str,
            "選擇你要找的特質",
            choices=TRAITS,
        ),
    ):
        trait = trait.lower().strip()

        traits_data = _load_user_traits()
        users = traits_data.get(trait, [])

        if not users:
            await ctx.respond(f"目前沒有 {trait} 的用戶資料。")
            return

        names = []
        for item in users:
            user_id = item.get("user_id")
            user_name = item.get("user_name")
            if user_name:
                names.append(user_name)
            elif user_id:
                names.append(f"<@{user_id}>")

        if not names:
            await ctx.respond(f"目前沒有 {trait} 的用戶資料。")
            return

        await ctx.respond(f"**{trait.capitalize()}** 的用戶：\n" + "\n".join(names))
