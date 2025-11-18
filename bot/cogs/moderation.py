# cogs/moderation.py
import disnake
from disnake.ext import commands
import asyncio
from config import MUTE_ROLE_NAME, DEFAULT_MUTE_SECONDS, LOGS_CHANNEL_ID

# GIFs e estética
HEXTECH_BORDER = "https://giffiles.alphacoders.com/528/52897.gif"
LUX_BAN_GIF = "https://images-ext-1.discordapp.net/external/-bxKV7nwkzFk0h18VO16m41nPcnTrKyRhbGaRKgT_PI/https/i.pinimg.com/originals/d3/97/fa/d397faf0fec8ddd29c45bf847cbb7c41.gif"
AHRI_MUTE_GIF = "https://images-ext-1.discordapp.net/external/-bxKV7nwkzFk0h18VO16m41nPcnTrKyRhbGaRKgT_PI/https/i.pinimg.com/originals/d3/97/fa/d397faf0fec8ddd29c45bf847cbb7c41.gif"
LOCK_GIF = "https://images-ext-1.discordapp.net/external/-bxKV7nwkzFk0h18VO16m41nPcnTrKyRhbGaRKgT_PI/https/i.pinimg.com/originals/d3/97/fa/d397faf0fec8ddd29c45bf847cbb7c41.gif"
UNLOCK_GIF = "https://images-ext-1.discordapp.net/external/-bxKV7nwkzFk0h18VO16m41nPcnTrKyRhbGaRKgT_PI/https/i.pinimg.com/originals/d3/97/fa/d397faf0fec8ddd29c45bf847cbb7c41.gif"

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.unmute_tasks = {}

    # --------------------------
    # LOG HEXTECH
    # --------------------------
    async def hextech_log(self, guild, title, user, reason, gif):
        channel = guild.get_channel(LOGS_CHANNEL_ID)
        if not channel:
            return

        embed = disnake.Embed(
            title=f"⚔ {title}",
            description=f"👤 **Usuário:** {user.mention}\n📜 **Motivo:** `{reason}`",
            color=0x00B3FF
        )
        embed.set_thumbnail(url=HEXTECH_BORDER)
        embed.set_image(url=gif)
        embed.set_footer(text="League of Legends — Moderação Hextech")

        await channel.send(embed=embed)

    # --------------------------
    # MUTE
    # --------------------------
    async def ensure_mute_role(self, guild):
        role = disnake.utils.get(guild.roles, name=MUTE_ROLE_NAME)
        if role:
            return role

        role = await guild.create_role(name=MUTE_ROLE_NAME)
        for ch in guild.text_channels:
            try:
                await ch.set_permissions(role, send_messages=False, add_reactions=False)
            except:
                pass
        return role

    @commands.slash_command(
        name="mute",
        description="Mutar um usuário (chat/voz).",
        default_member_permissions=disnake.Permissions(moderate_members=True)
    )
    async def mute(self, inter,
                   member: disnake.Member,
                   minutes: int = 5,
                   reason: str = "Sem motivo",
                   scope: str = commands.Param(choices=["chat", "voice", "both"], default="chat")
    ):
        await inter.response.defer()
        guild = inter.guild

        seconds = minutes * 60 if minutes > 0 else DEFAULT_MUTE_SECONDS
        mute_role = await self.ensure_mute_role(guild)

        if scope in ("chat", "both"):
            await member.add_roles(mute_role)

        if scope in ("voice", "both"):
            try:
                await member.edit(mute=True)
            except:
                pass

        await inter.followup.send(f"🔇 {member.mention} foi **mutado** por `{reason}`.")
        await self.hextech_log(guild, "MUTE Aplicado", member, reason, AHRI_MUTE_GIF)

        if minutes > 0:
            async def unmute_later():
                await asyncio.sleep(seconds)
                try:
                    await member.remove_roles(mute_role)
                except:
                    pass
                try:
                    await member.edit(mute=False)
                except:
                    pass
                await self.hextech_log(guild, "Unmute Automático", member, "Tempo expirado", AHRI_MUTE_GIF)

            t = asyncio.create_task(unmute_later())
            self.unmute_tasks.setdefault(guild.id, {})[member.id] = t

    # --------------------------
    # UNMUTE
    # --------------------------
    @commands.slash_command(
        name="unmute",
        description="Desmutar um usuário.",
        default_member_permissions=disnake.Permissions(moderate_members=True)
    )
    async def unmute(self, inter, member: disnake.Member):
        await inter.response.defer()
        guild = inter.guild

        mute_role = disnake.utils.get(guild.roles, name=MUTE_ROLE_NAME)
        if mute_role:
            try:
                await member.remove_roles(mute_role)
            except:
                pass

        try:
            await member.edit(mute=False)
        except:
            pass

        await inter.followup.send(f"🔊 {member.mention} desmutado.")
        await self.hextech_log(guild, "Unmute Manual", member, "Desmutado pelo staff", AHRI_MUTE_GIF)

        if guild.id in self.unmute_tasks and member.id in self.unmute_tasks[guild.id]:
            task = self.unmute_tasks[guild.id].pop(member.id)
            task.cancel()

    # --------------------------
    # BAN
    # --------------------------
    @commands.slash_command(
        name="ban",
        description="Banir um usuário.",
        default_member_permissions=disnake.Permissions(ban_members=True)
    )
    async def ban(self, inter, member: disnake.Member, reason: str = "Sem motivo"):
        await inter.response.defer()
        await inter.guild.ban(member, reason=reason)

        await inter.followup.send(f"🔨 {member.mention} foi **banido**.")
        await self.hextech_log(inter.guild, "Ban", member, reason, LUX_BAN_GIF)

    # --------------------------
    # UNBAN
    # --------------------------
    @commands.slash_command(
        name="unban",
        description="Desbanir um usuário.",
        default_member_permissions=disnake.Permissions(ban_members=True)
    )
    async def unban(self, inter, user_id: int):
        await inter.response.defer()

        user = await self.bot.fetch_user(user_id)
        await inter.guild.unban(user)

        await inter.followup.send(f"🔓 {user} desbanido.")
        await self.hextech_log(inter.guild, "Unban", user, "Removido da lista de ban", LUX_BAN_GIF)

    # --------------------------
    # LOCK
    # --------------------------
    @commands.slash_command(
        name="lock",
        description="Trava todos os canais.",
        default_member_permissions=disnake.Permissions(administrator=True)
    )
    async def lock(self, inter, reason: str = "Anti-raid"):
        await inter.response.defer()

        for ch in inter.guild.text_channels:
            try:
                await ch.set_permissions(inter.guild.default_role, send_messages=False)
            except:
                pass

        await inter.followup.send("🔒 Servidor travado.")
        await self.hextech_log(inter.guild, "LOCK", inter.author, reason, LOCK_GIF)

    # --------------------------
    # UNLOCK
    # --------------------------
    @commands.slash_command(
        name="unlock",
        description="Destrava o servidor.",
        default_member_permissions=disnake.Permissions(administrator=True)
    )
    async def unlock(self, inter, reason: str = "Unlock"):
        await inter.response.defer()

        for ch in inter.guild.text_channels:
            try:
                await ch.set_permissions(inter.guild.default_role, send_messages=None)
            except:
                pass

        await inter.followup.send("🔓 Servidor destravado.")
        await self.hextech_log(inter.guild, "UNLOCK", inter.author, reason, UNLOCK_GIF)

def setup(bot):
    bot.add_cog(Moderation(bot))
    
    # CLEAR (Comando de Limpeza)
    # --------------------------
    @commands.slash_command(name="clear", description="Apaga mensagens do chat.")
    @commands.has_permissions(manage_messages=True)
    async def clear(self, inter, quantidade: int = 10):
        # O defer é importante para comandos que levam tempo
        await inter.response.defer(ephemeral=True)

        if quantidade < 1 or quantidade > 500:
            return await inter.followup.send("❌ Escolha um valor entre **1 e 500** mensagens.", ephemeral=True)

        # Usamos purge para apagar as mensagens
        deleted = await inter.channel.purge(limit=quantidade)

        # Feedback efêmero (só você vê)
        await inter.followup.send(
            f"🧹 Foram apagadas **{len(deleted)}** mensagens.",
            ephemeral=True
        )
        
        # Opcional: Adicionar Log de Auditoria
        await self.hextech_log(
            inter.guild, 
            "CLEAR Executado", 
            inter.author, 
            f"Apagou {len(deleted)} mensagens no canal {inter.channel.mention}", 
            LOCK_GIF # Você pode criar um GIF específico para 'Clear'
        )


def setup(bot):
    bot.add_cog(Moderation(bot))
