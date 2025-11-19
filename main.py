import disnake
from disnake.ext import commands
import os

# ----------------------------
# CARREGAR TOKEN
# ----------------------------
# Tenta carregar .env para desenvolvimento local
# Em produção (Render), usa variáveis de ambiente diretamente
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv não instalado (normal em produção)

TOKEN = os.getenv("DISCORD_TOKEN")

if TOKEN is None:
    raise ValueError("❌ ERRO: DISCORD_TOKEN não encontrado nas variáveis de ambiente!")

# ----------------------------
# INTENTS
# ----------------------------
intents = disnake.Intents.default()
intents.members = True
intents.messages = True
intents.guilds = True
intents.voice_states = True
intents.message_content = True

# ----------------------------
# CONFIGURAÇÃO DE SEGURANÇA
# ----------------------------
# 🔥 OBRIGATÓRIO: ID DO SEU SERVIDOR 🔥
ALLOWED_GUILD_ID = 1263584915908333599

# ----------------------------
# BOT
# ----------------------------
bot = commands.Bot(
    intents=intents,
    command_prefix="!",
    help_command=None
)

# ----------------------------
# LISTA DE COGS
# ----------------------------
initial_cogs = [
    "cogs.welcome",
    "cogs.moderation",
    "cogs.xp",
    "cogs.custom_queue"
]

# ----------------------------
# EVENTO DE READY
# ----------------------------
@bot.event
async def on_ready():
    print(f"✅ Bot pronto — {bot.user} (ID: {bot.user.id})")

# ----------------------------
# GUARDA DE SEGURANÇA
# ----------------------------
@bot.event
async def on_guild_join(guild: disnake.Guild):
    if guild.id != ALLOWED_GUILD_ID:
        print(f"⚠️ ALERTA: Saindo do servidor não autorizado: {guild.name} ({guild.id})")
        await guild.leave()
        try:
            await guild.owner.send(
                f"❌ O bot **{bot.user.name}** é privado e não pode ser adicionado ao servidor **{guild.name}**."
            )
        except:
            pass

# ----------------------------
# CARREGAR COGS + INICIAR BOT
# ----------------------------
if __name__ == "__main__":
    for cog in initial_cogs:
        try:
            bot.load_extension(cog)
            print(f"[OK] Loaded {cog}")
        except Exception as e:
            print(f"[ERRO] Falha ao carregar {cog}: {e}")

    bot.run(TOKEN)