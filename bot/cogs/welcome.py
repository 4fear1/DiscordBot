import disnake
from disnake.ext import commands
from config import WELCOME_CHANNEL_ID, AUTOROLE_ID

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Quando alguém entrar no servidor
    @commands.Cog.listener()
    async def on_member_join(self, member: disnake.Member):

        guild = member.guild

        # ================
        # AUTO ROLE
        # ================
        if AUTOROLE_ID:
            role = guild.get_role(AUTOROLE_ID)
            if role:
                try:
                    await member.add_roles(role, reason="Autorole de entrada")
                except:
                    pass

        # ================
        # BOAS VINDAS
        # ================
        if WELCOME_CHANNEL_ID:
            channel = guild.get_channel(WELCOME_CHANNEL_ID)
            if channel:

                embed = disnake.Embed(
                    title="🎉 Bem-vindo ao servidor!",
                    description=(
                        f"Olá {member.mention}! ✨\n\n"
                        "Estamos felizes em ter você aqui!\n"
                        "Sinta-se à vontade para conversar e interagir. ❤️"
                    ),
                    color=0x7289DA,
                )

                embed.set_thumbnail(url=member.display_avatar.url)

                # GIF estético LoL
                embed.set_image(
                    url="https://tenor.com/view/sona-dj-league-of-legends-gif-13251587"  # Você pode trocar por GIF temático de LOL
                )

                embed.set_footer(text=f"Entrou em: {guild.name}")

                await channel.send(embed=embed)

def setup(bot):
    bot.add_cog(Welcome(bot))
