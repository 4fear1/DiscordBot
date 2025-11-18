import disnake
from disnake.ext import commands
import os
from dotenv import load_dotenv  # <-- ADICIONADO

# ----------------------------
# CARREGAR VARIÁVEIS DO .env
# ----------------------------
load_dotenv()  
TOKEN = os.getenv("DISCORD_TOKEN")  # <-- LENDO TOKEN DO .env

if TOKEN is None:
    raise ValueError("❌ ERRO: Nenhum TOKEN encontrado no arquivo .env!")



# ----------------------------
# INTENTS
# ----------------------------
intents = disnake.Intents.default()
intents.members = True
intents.messages = True
intents.guilds = True
intents.voice_states = True
intents.message_content = True  # necessário para XP e logs


# ----------------------------
# CONFIGURAÇÃO DE SEGURANÇA
# ----------------------------
# 🔥🔥 OBRIGATÓRIO: SUBSTITUA PELO ID DO SEU SERVIDOR 🔥🔥
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
    print(f"Bot pronto — logado como {bot.user} (ID: {bot.user.id})")


# ----------------------------
# GUARDA DE SEGURANÇA (Guild Join Guardrail)
# ----------------------------
@bot.event
async def on_guild_join(guild: disnake.Guild):
    # Verifica se o ID do servidor é o permitido
    if guild.id != ALLOWED_GUILD_ID:

        print(f"ALERTA: Saindo do servidor não autorizado: {guild.name} ({guild.id})")

        await guild.leave()

        try:
            await guild.owner.send(
                f"❌ Olá! O bot **{bot.user.name}** é privado e não pode ser adicionado ao servidor **{guild.name}**."
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
