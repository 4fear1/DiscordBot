# cogs/xp.py
import disnake
from disnake.ext import commands
import asyncio
import json
import os
import time
from config import XP_PER_MESSAGE, XP_COOLDOWN_SECONDS, LEVEL_ROLES

HEXTECH_BORDER = "https://giffiles.alphacoders.com/528/52897.gif"
LUX_LEVELUP_GIF = "https://images-ext-1.discordapp.net/external/-bxKV7nwkzFk0h18VO16m41nPcnTrKyRhbGaRKgT_PI/https/i.pinimg.com/originals/d3/97/fa/d397faf0fec8ddd29c45bf847cbb7c41.gif"

DATA_PATH = os.path.join("data", "xp.json")
os.makedirs("data", exist_ok=True)
if not os.path.exists(DATA_PATH):
    with open(DATA_PATH, "w") as f:
        json.dump({}, f)

class XP(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lock = asyncio.Lock()
        self.cooldowns = {}

    def required_xp_for_next(self, level):
        return 100 * level

    async def add_xp(self, user_id, guild_id, amount):
        async with self.lock:
            with open(DATA_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)

            key = f"{guild_id}-{user_id}"
            if key not in data:
                data[key] = {"xp": 0, "level": 1}

            data[key]["xp"] += amount
            leveled = False

            while data[key]["xp"] >= self.required_xp_for_next(data[key]["level"]):
                data[key]["xp"] -= self.required_xp_for_next(data[key]["level"])
                data[key]["level"] += 1
                leveled = True

            with open(DATA_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            return leveled, data[key]["level"]

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        now = time.time()
        last = self.cooldowns.get(message.author.id, 0)

        if now - last < XP_COOLDOWN_SECONDS:
            return

        self.cooldowns[message.author.id] = now

        leveled, level = await self.add_xp(message.author.id, message.guild.id, XP_PER_MESSAGE)

        if leveled:
            role_name = LEVEL_ROLES.get(level)
            if role_name:
                role = disnake.utils.get(message.guild.roles, name=role_name)
                if not role:
                    role = await message.guild.create_role(name=role_name)

                try:
                    await message.author.add_roles(role)
                except:
                    pass

            embed = disnake.Embed(
                title="✨ LEVEL UP HEXTECH!",
                description=f"{message.author.mention} atingiu **nível {level}**!",
                color=0x00B3FF
            )
            embed.set_thumbnail(url=HEXTECH_BORDER)
            embed.set_image(url=LUX_LEVELUP_GIF)
            embed.set_footer(text="League of Legends • Sistema de Experiência")

            await message.channel.send(embed=embed)

    @commands.slash_command(
        name="rank",
        description="Mostra o XP e nível de um usuário.",
        default_member_permissions=disnake.Permissions(moderate_members=True)
    )
    async def rank(self, inter, member: disnake.Member = None):
        await inter.response.defer()

        target = member or inter.author

        with open(DATA_PATH, "r") as f:
            data = json.load(f)

        key = f"{inter.guild.id}-{target.id}"
        obj = data.get(key, {"xp": 0, "level": 1})

        embed = disnake.Embed(
            title=f"📊 Rank — {target.display_name}",
            description=f"Nível: **{obj['level']}**\nXP: **{obj['xp']}/{self.required_xp_for_next(obj['level'])}**",
            color=0x00B3FF
        )
        embed.set_thumbnail(url=HEXTECH_BORDER)

        await inter.followup.send(embed=embed)

def setup(bot):
    bot.add_cog(XP(bot))
