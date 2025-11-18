# config.py — personalize aqui
TOKEN = "MTQzNjc3Mzg2MTY1OTI0NjY3Mg.GP_BRa.bnHNtJCLWACBQpChrflD34x7GbRsAIq3F8yqos"

# Nome do role usado para mutar no chat
MUTE_ROLE_NAME = "Muted"

# Tempo padrão (segundos) se o usuário não passar tempo
DEFAULT_MUTE_SECONDS = 300

# Lista de GIFs (temática League of Legends) — substitua por seus links preferidos
WELCOME_GIFS = [
    "https://images-ext-1.discordapp.net/external/-bxKV7nwkzFk0h18VO16m41nPcnTrKyRhbGaRKgT_PI/https/i.pinimg.com/originals/d3/97/fa/d397faf0fec8ddd29c45bf847cbb7c41.gif",
    "https://images-ext-1.discordapp.net/external/YveUKc4EqQNIpl_idknsZ1--aucKMSxI8fMVHZbeXQw/https/media.tenor.com/hICggDqh-_wAAAPo/bom-dia-viata.mp4",
    
]

# Mensagem e título do embed de boas-vindas
WELCOME_TITLE = "Seja bem-vindo a Summoner's Rift!"
WELCOME_DESCRIPTION = "Prepare-se para TILTAR, curta a cidade e siga as regras."

# XP settings
XP_PER_MESSAGE = 10
XP_COOLDOWN_SECONDS = 60  # cooldown para ganhar XP por usuário

# Mapeamento de níveis -> role name (quando usuário alcançar Nível X ganha role)
LEVEL_ROLES = {
    0: "Novato",
    10: "Veterano",
    20: "Elite"
}

# Logs channel ID (opcional): se quiser logs em canal específico, coloque o ID
LOGS_CHANNEL_ID = 1263615863177875498  # ex: 123456789012345678
WELCOME_CHANNEL_ID = 1440381497738661950        # canal onde manda mensagem de boas-vindas
AUTOROLE_ID = 1263608456267432021              # cargo que será dado ao entrar
