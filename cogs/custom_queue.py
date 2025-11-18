import disnake
from disnake.ext import commands
import random
import json
import os
import datetime

# ---------------------------------------------------------
# CONFIGURAÇÕES HEXTECH & DADOS
# ---------------------------------------------------------
QUEUE_DATA = {}  # Fila temporária (limpa após o bot reiniciar)
CONFIG_FILE = "data/config.json" # Configurações persistentes (canais, host_id, etc.)
PLAYER_POINTS_FILE = "data/player_points.json"

# Cores e Imagens
HEX_BLUE = 0x0ACDFF
HEX_GOLD = 0xC8AA6E
IMG_HEXTECH_CHEST = "https://cdna.artstation.com/p/assets/images/images/008/744/838/original/seth-trevains-fiddlesticks-idle.gif?1515017080"
IMG_VICTORY = "https://images-ext-1.discordapp.net/external/GLGq51Wycupgn-KnW3viKLb-y0u13woRsaiV4k_SQE0/https/media.tenor.com/_kWcrV2RAHUAAAPo/league-of.mp4"

# Configuração das Rotas
LANE_CONFIG = {
    "TOP": {"icon": "<:top11:1440426442990157844>", "name": "Top", "style": disnake.ButtonStyle.secondary},
    "JG":  {"icon": "<:jungle:1440426678353395794>", "name": "Jungle", "style": disnake.ButtonStyle.success},
    "MID": {"icon": "<:mid:1440426486359265380>", "name": "Mid", "style": disnake.ButtonStyle.blurple},
    "ADC": {"icon": "<:adc:1440426631612338206>", "name": "ADC", "style": disnake.ButtonStyle.danger},
    "SUP": {"icon": "<:suporte:1440426943261573141>", "name": "Sup", "style": disnake.ButtonStyle.primary}
}

# Garante que os arquivos existam
os.makedirs("data", exist_ok=True)
if not os.path.exists(PLAYER_POINTS_FILE):
    with open(PLAYER_POINTS_FILE, "w") as f:
        json.dump({}, f, indent=2)
if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "w") as f:
        json.dump({}, f, indent=2)

# --------------------------
# Funções de I/O
# --------------------------
def load_points():
    with open(PLAYER_POINTS_FILE, "r") as f:
        return json.load(f)

def save_points(data):
    with open(PLAYER_POINTS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)

# --------------------------
# Funções Auxiliares de Atualização
# --------------------------
async def send_log(guild, embed):
    """Envia logs para o canal privado definido na configuração."""
    config = load_config()
    guild_config = config.get(str(guild.id), {})
    log_id = guild_config.get("log_channel_id")
    
    if log_id:
        channel = guild.get_channel(log_id)
        if channel:
            await channel.send(embed=embed)

def get_config_for_guild(guild_id):
    """Obtém a configuração específica para o servidor."""
    return load_config().get(str(guild_id), {})

def save_config_for_guild(guild_id, key, value):
    """Salva uma chave de configuração para o servidor."""
    config = load_config()
    guild_id_str = str(guild_id)
    if guild_id_str not in config:
        config[guild_id_str] = {}
    config[guild_id_str][key] = value
    save_config(config)

# --- Embed de Registro ---
def generate_register_embed(guild_id):
    """Gera o embed de registro, listando os jogadores permitidos."""
    config = get_config_for_guild(guild_id)
    host_id = config.get("host_id")
    q = QUEUE_DATA.get(host_id)
    
    embed = disnake.Embed(
        title="📝 REGISTRO OBRIGATÓRIO — PRÉ-JOGO",
        description="Clique em **Registrar-se** para obter permissão para entrar nas filas customizadas.\n\n"
                    "⚠ **REQUISITO:** Você deve estar em um canal de voz para se registrar.",
        color=HEX_BLUE,
        timestamp=datetime.datetime.now()
    )
    embed.set_thumbnail(url=IMG_HEXTECH_CHEST)

    if q and q["registered_ids"]:
        member_mentions = [f"<@{uid}>" for uid in q["registered_ids"]]
        embed.add_field(
            name=f"👥 Registrados ({len(q['registered_ids'])})",
            value="\n".join(member_mentions)
        )
    else:
        embed.add_field(name="👥 Registrados", value="Nenhum jogador registrado ainda.")
    
    return embed

async def update_persistent_register_message(bot, guild_id):
    """Atualiza o embed persistente de registro no canal."""
    config = get_config_for_guild(guild_id)
    register_channel_id = config.get("register_channel_id")
    register_message_id = config.get("register_message_id")
    
    if not register_channel_id or not register_message_id:
        return

    try:
        channel = await bot.fetch_channel(register_channel_id)
        message = await channel.fetch_message(register_message_id)
        embed = generate_register_embed(guild_id)
        # Re-adiciona a view para persistência
        view = RegisterView(config.get("host_id"), guild_id) 
        await message.edit(embed=embed, view=view)
    except Exception as e:
        print(f"Erro ao atualizar mensagem de registro persistente: {e}")

# --- Embed da Fila ---
def generate_queue_embed(guild_id):
    """Gera o embed visual da fila atualizando os nomes."""
    config = get_config_for_guild(guild_id)
    host_id = config.get("host_id")
    q = QUEUE_DATA.get(host_id)
    
    # ... (restante da função generate_queue_embed permanece a mesma)
    if not q:
        embed = disnake.Embed(
            title="💠 HEXTECH MATCHMAKING SYSTEM",
            description="Sistema de Fila Inativo. Um Administrador deve usar `/setar_fila` para iniciar.",
            color=disnake.Color.red(),
        )
        embed.set_thumbnail(url=IMG_HEXTECH_CHEST)
        return embed

    # Se a fila está ativa:
    embed = disnake.Embed(
        title="💠 HEXTECH MATCHMAKING SYSTEM - Fila Ativa",
        description=f"Host: <@{host_id}>\nStatus: **Escolha sua Rota!**",
        color=HEX_BLUE,
        timestamp=datetime.datetime.now()
    )
    embed.set_thumbnail(url=IMG_HEXTECH_CHEST)
    embed.set_footer(text="Powered by Piltover Technology")

    total_players = 0
    
    for lane_code, data in LANE_CONFIG.items():
        players = q["lanes"][lane_code]
        total_players += len(players)
        
        player_list = "\n".join([f"> {data['icon']} {p.mention}" for p in players]) if players else "*Vazio*"
        slot_info = f"{len(players)}/2"
        
        embed.add_field(
            name=f"{data['icon']} {lane_code} [{slot_info}]",
            value=player_list,
            inline=True
        )

    embed.add_field(name="⠀", value="⠀", inline=False) # Espaçador
    embed.add_field(name="👥 Total na Sala", value=f"**{total_players}/10 Jogadores**", inline=False)
    
    return embed

async def update_persistent_queue_message(bot, guild_id):
    """Atualiza o embed persistente da fila no canal."""
    config = get_config_for_guild(guild_id)
    
    queue_channel_id = config.get("queue_channel_id")
    queue_message_id = config.get("queue_message_id")
    host_id = config.get("host_id")
    
    if not queue_channel_id or not queue_message_id or not host_id:
        return

    try:
        channel = await bot.fetch_channel(queue_channel_id)
        message = await channel.fetch_message(queue_message_id)
        
        embed = generate_queue_embed(guild_id)
        view = LaneButtons(host_id, guild_id)
        
        await message.edit(embed=embed, view=view)
    except Exception as e:
        print(f"Erro ao atualizar mensagem persistente: {e}")
        save_config_for_guild(guild_id, "queue_message_id", None)


async def update_persistent_rank_message(bot, guild_id):
    """Atualiza o embed persistente do ranking no canal."""
    # ... (função update_persistent_rank_message permanece a mesma)
    config = get_config_for_guild(guild_id)
    rank_channel_id = config.get("rank_channel_id")
    rank_message_id = config.get("rank_message_id")
    
    if not rank_channel_id or not rank_message_id:
        return

    pts = load_points()
    sorted_pts = sorted(pts.items(), key=lambda x: x[1], reverse=True)

    embed = disnake.Embed(
        title="🏆 RANKING HEXTECH GLOBAL",
        color=HEX_GOLD,
        timestamp=datetime.datetime.now()
    )
    embed.set_thumbnail(url=IMG_VICTORY)
    
    desc = ""
    guild = bot.get_guild(guild_id)
    
    if guild:
        for i, (uid, p) in enumerate(sorted_pts[:20], start=1):
            user = guild.get_member(int(uid))
            name = user.display_name if user else f"ID: {uid}"
            desc += f"`#{i}` **{name}** — {p} LP\n"
    
    embed.description = desc or "Nenhum jogador possui pontos ainda. Que comece a competição!"

    try:
        channel = await bot.fetch_channel(rank_channel_id)
        message = await channel.fetch_message(rank_message_id)
        await message.edit(embed=embed)
    except Exception as e:
        print(f"Erro ao atualizar ranking persistente: {e}")
        save_config_for_guild(guild_id, "rank_message_id", None)
        save_config_for_guild(guild_id, "rank_channel_id", None)

# --------------------------
# View de Registro
# --------------------------
class RegisterView(disnake.ui.View):
    def __init__(self, host_id, guild_id):
        super().__init__(timeout=None)
        self.host_id = host_id
        self.guild_id = guild_id
        self.add_item(self.RegisterButton())
    
    class RegisterButton(disnake.ui.Button):
        def __init__(self):
            super().__init__(label="REGISTRAR-SE", style=disnake.ButtonStyle.primary, emoji="✅", custom_id="register_user")
        
        async def callback(self, inter: disnake.MessageInteraction):
            q = QUEUE_DATA.get(self.view.host_id)
            if not q: 
                return await inter.response.send_message("A fila foi desativada.", ephemeral=True)

            # 1. Checa requisito de Voz
            if not inter.author.voice:
                return await inter.response.send_message("❌ Você deve estar em um canal de voz para se registrar!", ephemeral=True)

            # 2. Registra o ID
            if inter.author.id not in q["registered_ids"]:
                q["registered_ids"].add(inter.author.id)
                message = "✅ Registro concluído! Agora você pode escolher sua rota na fila."
            else:
                message = "⚠ Você já está registrado."

            await inter.response.send_message(message, ephemeral=True)
            
            # 3. Atualiza o Embed de Registro
            await update_persistent_register_message(inter.bot, inter.guild.id)


# --------------------------
# View da Fila
# --------------------------
class LaneButtons(disnake.ui.View):
    def __init__(self, host_id, guild_id):
        super().__init__(timeout=None) 
        self.host_id = host_id
        self.guild_id = guild_id
        
        self.update_lane_buttons()
        self.add_item(self.LeaveQueueButton())
        self.add_item(self.StartMatchButton())

    def update_lane_buttons(self):
        q = QUEUE_DATA.get(self.host_id)
        if not q: return

        for lane_code, data in LANE_CONFIG.items():
            existing_button = disnake.utils.get(self.children, custom_id=f"lane_{lane_code}")
            
            if existing_button:
                self.remove_item(existing_button)
            
            count = len(q["lanes"][lane_code])
            btn = disnake.ui.Button(
                label=f"{lane_code} ({count}/2)",
                emoji=data["icon"],
                style=data["style"],
                custom_id=f"lane_{lane_code}",
                row=0 if lane_code in ["TOP", "JG", "MID"] else 1
            )
            btn.callback = self.create_lane_callback(lane_code)
            self.add_item(btn)


    def create_lane_callback(self, lane):
        async def callback(inter: disnake.MessageInteraction):
            q = QUEUE_DATA.get(self.host_id) 
            if not q: return await inter.response.send_message("A fila foi desativada.", ephemeral=True)
            
            # --- NOVA VALIDAÇÃO DE REGISTRO E VOZ ---
            if inter.author.id not in q["registered_ids"]:
                 return await inter.response.send_message("❌ Você não está registrado. Use o botão de registro!", ephemeral=True)
            
            if not inter.author.voice:
                 return await inter.response.send_message("❌ Você deve estar em um canal de voz para selecionar sua rota!", ephemeral=True)
            # ----------------------------------------

            changed = False
            
            # 1. Tenta sair de rotas anteriores (Mover)
            for l in LANE_CONFIG:
                if inter.author in q["lanes"][l]:
                    q["lanes"][l].remove(inter.author)
                    changed = True
                    break 
            
            # 2. Tenta entrar na nova rota
            if len(q["lanes"][lane]) < 2:
                q["lanes"][lane].append(inter.author)
                changed = True
            else:
                return await inter.response.send_message(f"❌ A rota **{lane}** já está cheia.", ephemeral=True)
            
            # 3. Atualiza o Embed Persistente
            if changed:
                await inter.response.defer()
                await update_persistent_queue_message(inter.bot, self.guild_id)
        return callback

    class LeaveQueueButton(disnake.ui.Button):
        def __init__(self):
            super().__init__(label="SAIR DA FILA", style=disnake.ButtonStyle.danger, emoji="🏃", row=2)
        
        async def callback(self, inter: disnake.MessageInteraction):
            q = QUEUE_DATA.get(self.view.host_id) 
            if not q: return await inter.response.send_message("A fila foi desativada.", ephemeral=True)

            removed = False
            for l in LANE_CONFIG:
                if inter.author in q["lanes"][l]:
                    q["lanes"][l].remove(inter.author)
                    removed = True
                    break
            
            if removed:
                await inter.response.send_message("✅ Você saiu da fila.", ephemeral=True)
                await update_persistent_queue_message(inter.bot, self.view.guild_id) 
            else:
                await inter.response.send_message("⚠ Você não estava em nenhuma rota.", ephemeral=True)


    class StartMatchButton(disnake.ui.Button):
        def __init__(self):
            super().__init__(label="INICIAR PARTIDA", style=disnake.ButtonStyle.success, emoji="⚔️", row=2)

        async def callback(self, inter: disnake.MessageInteraction):
            host_id = self.view.host_id 
            if inter.author.id != host_id:
                return await inter.response.send_message("❌ Apenas o Host pode iniciar.", ephemeral=True)
            
            q = QUEUE_DATA[host_id]
            config = get_config_for_guild(inter.guild.id)
            
            # Variáveis de Configuração (5v5 Padrão)
            PLAYERS_NEEDED = 10 
            TEAM_SPLIT = 5          
            
            all_players = []
            for l in q["lanes"]: all_players.extend(q["lanes"][l])
            
            if len(all_players) != PLAYERS_NEEDED:
                return await inter.response.send_message(f"❌ Faltam **{PLAYERS_NEEDED - len(all_players)}** jogadores.", ephemeral=True)
            
            # -----------------------------------------------------------------
            # NOVO READY CHECK: TODOS OS JOGADORES TÊM QUE ESTAR EM UMA CALL AGORA
            # -----------------------------------------------------------------
            not_in_voice = [p.mention for p in all_players if not p.voice]
            if not_in_voice:
                return await inter.response.send_message(
                    f"❌ **Ready Check Falhou!** Todos os {PLAYERS_NEEDED} jogadores devem estar em um canal de voz para iniciar a partida. Ausentes: {', '.join(not_in_voice)}", 
                    ephemeral=True
                )
            # -----------------------------------------------------------------

            blue_channel = inter.guild.get_channel(config.get("team_blue_id"))
            red_channel = inter.guild.get_channel(config.get("team_red_id"))
            if not blue_channel or not red_channel:
                 return await inter.response.send_message("❌ Canais de voz não definidos. Use `/setar_canais_voz`.", ephemeral=True)
            
            # 2. Sorteio e Capitães
            random.shuffle(all_players)
            
            team1 = all_players[:TEAM_SPLIT]
            team2 = all_players[TEAM_SPLIT:]
            
            captain_blue = team1[0]
            captain_red = team2[0]

            q["team1"] = team1
            q["team2"] = team2
            q["captain_blue_id"] = captain_blue.id
            q["captain_red_id"] = captain_red.id
            q["origin_channel"] = inter.author.voice.channel if inter.author.voice else None

            # 3. Mover Players
            for p in team1: 
                if p.voice: await p.move_to(blue_channel)
            for p in team2: 
                if p.voice: await p.move_to(red_channel)

            # 4. Envio do Embed de Partida (e Log)
            embed = disnake.Embed(title="⚔️ SUMMONER'S RIFT - PARTIDA INICIADA", color=HEX_GOLD)
            embed.add_field(name="🔵 Blue Team", value=f"Capitão: {captain_blue.mention}\n" + "\n".join([p.mention for p in team1]))
            embed.add_field(name="🔴 Red Team", value=f"Capitão: {captain_red.mention}\n" + "\n".join([p.mention for p in team2]))
            embed.set_footer(text="O resultado deve ser inserido com /resultado pelo Host após o término.")
            
            await inter.response.edit_message(content=f"**Partida Iniciada!** Os capitães estão prontos.\n\nTime Azul: {captain_blue.mention}\nTime Vermelho: {captain_red.mention}", embed=None, view=None)

            # Log Premium de Início
            log_embed = disnake.Embed(title="📜 LOG: Partida Iniciada", color=disnake.Color.green())
            log_embed.add_field(name="Capitães", value=f"Azul: {captain_blue.mention}\nVermelho: {captain_red.mention}")
            log_embed.timestamp = datetime.datetime.now()
            await send_log(inter.guild, log_embed)


# --------------------------
# View de Confirmação de Vitória (Sem Alterações)
# --------------------------
class CaptainResultButtons(disnake.ui.View):
    def __init__(self, winner_team, game_host_id):
        super().__init__(timeout=300)
        self.winner_team = winner_team
        self.game_host_id = game_host_id 
        
        self.add_item(self.ConfirmButton(winner_team))

    class ConfirmButton(disnake.ui.Button):
        def __init__(self, winner_team):
            style = disnake.ButtonStyle.primary if winner_team == "Blue" else disnake.ButtonStyle.danger
            super().__init__(
                label=f"CONFIRMAR VITÓRIA DO TIME {winner_team.upper()}", 
                style=style, 
                custom_id=f"conf_win:{winner_team}"
            )
            self.winner_team = winner_team
            self.confirmed_captains = set()

        async def callback(self, inter: disnake.MessageInteraction):
            q = QUEUE_DATA.get(self.view.game_host_id)
            if not q: return await inter.response.send_message("Partida encerrada ou dados perdidos.", ephemeral=True)
            
            is_captain_blue = inter.author.id == q.get("captain_blue_id")
            is_captain_red = inter.author.id == q.get("captain_red_id")
            
            if not is_captain_blue and not is_captain_red:
                return await inter.response.send_message("❌ Apenas os capitães podem confirmar o resultado.", ephemeral=True)
            
            if inter.author.id in self.confirmed_captains:
                return await inter.response.send_message("⚠ Você já confirmou este resultado.", ephemeral=True)

            self.confirmed_captains.add(inter.author.id)
            
            if len(self.confirmed_captains) < 2:
                await inter.response.send_message(f"✅ Confirmação de {inter.author.mention} recebida. Aguardando o segundo Capitão...", ephemeral=True)
                
            else:
                await inter.response.defer()

                is_blue_win = (self.winner_team == "Blue")
                winners = q["team1"] if is_blue_win else q["team2"]
                losers = q["team2"] if is_blue_win else q["team1"]

                pts = load_points()
                for p in winners:
                    pts[str(p.id)] = pts.get(str(p.id), 0) + 10
                save_points(pts)

                if q["origin_channel"]:
                    for p in winners + losers:
                        if p.voice: await p.move_to(q["origin_channel"])

                del QUEUE_DATA[self.view.game_host_id]
                
                await update_persistent_queue_message(inter.bot, inter.guild.id)
                await update_persistent_rank_message(inter.bot, inter.guild.id)
                
                final_embed = disnake.Embed(title=f"🏆 VITÓRIA CONFIRMADA: Time {self.winner_team}", color=HEX_GOLD)
                final_embed.description = "**GG WP!** Pontos aplicados. A fila está ativa novamente."
                await inter.edit_original_response(embed=final_embed, view=None)

                log_embed = disnake.Embed(title="📜 LOG: Partida Finalizada", color=HEX_GOLD)
                log_embed.add_field(name="Vencedor", value=self.winner_team)
                log_embed.timestamp = datetime.datetime.now()
                await send_log(inter.guild, log_embed)


# ---------------------------------------------------------
# COG - Gerenciador de Fila e Comandos Admin
# ---------------------------------------------------------

class CustomQueueManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.restore_persistent_queue())

    async def restore_persistent_queue(self):
        await self.bot.wait_until_ready()
        
        config = load_config()
        for guild_id_str, cfg in config.items():
            guild_id = int(guild_id_str)
            host_id = cfg.get("host_id")
            
            # 1. Restaura Fila
            if cfg.get("queue_message_id") and host_id:
                try:
                    self.bot.add_view(LaneButtons(host_id, guild_id))
                except Exception as e:
                    print(f"Aviso de restauração da Fila: {e}")
            
            # 2. Restaura Registro
            if cfg.get("register_message_id") and host_id:
                 try:
                    self.bot.add_view(RegisterView(host_id, guild_id))
                 except Exception as e:
                    print(f"Aviso de restauração do Registro: {e}")

    # ---------------- ADMIN COMMANDS ----------------

    @commands.slash_command(name="setar_registro", description="[ADMIN] Define o Embed persistente de Registro obrigatório.")
    @commands.has_permissions(administrator=True)
    async def setar_registro(self, inter):
        config = get_config_for_guild(inter.guild.id)
        host_id = config.get("host_id")
        
        if not host_id:
            return await inter.response.send_message("❌ Defina a fila principal com `/setar_fila` primeiro!", ephemeral=True)
        
        # Cria o estado inicial do registro, se não existir
        if host_id not in QUEUE_DATA:
            QUEUE_DATA[host_id] = {"lanes": {l: [] for l in LANE_CONFIG}, "registered_ids": set()}
        
        # Garante que o set de registrados exista, mesmo se a fila já estiver criada
        if "registered_ids" not in QUEUE_DATA[host_id]:
             QUEUE_DATA[host_id]["registered_ids"] = set()
        
        embed = generate_register_embed(inter.guild.id)
        view = RegisterView(host_id, inter.guild.id)
        
        response = await inter.channel.send(embed=embed, view=view)

        save_config_for_guild(inter.guild.id, "register_channel_id", inter.channel.id)
        save_config_for_guild(inter.guild.id, "register_message_id", response.id)

        await inter.response.send_message("✅ Embed de Registro configurado e ativo!", ephemeral=True)


    @commands.slash_command(name="setar_fila", description="[ADMIN] Cria/Ativa a fila de customs neste canal. (Host: Você)")
    @commands.has_permissions(administrator=True)
    async def set_queue_channel(self, inter):
        config = get_config_for_guild(inter.guild.id)
        host_id = inter.author.id
        
        # 1. Limpa a fila antiga se houver
        if config.get("queue_message_id"):
            try:
                old_host_id = config["host_id"]
                if old_host_id in QUEUE_DATA: del QUEUE_DATA[old_host_id]
                
                old_channel = await self.bot.fetch_channel(config["queue_channel_id"])
                old_message = await old_channel.fetch_message(config["queue_message_id"])
                await old_message.edit(content="❌ **Fila substituída/reiniciada.**", embed=None, view=None)
            except:
                pass 

        # 2. Cria o novo estado inicial da fila
        # Mantém o set de registrados se já houver
        registered_ids = QUEUE_DATA.get(host_id, {}).get("registered_ids", set())
        
        QUEUE_DATA[host_id] = {
            "lanes": {l: [] for l in LANE_CONFIG},
            "registered_ids": registered_ids # Persiste o registro na memória
        }
        save_config_for_guild(inter.guild.id, "host_id", host_id)

        # 3. Envia a nova mensagem persistente
        embed = generate_queue_embed(inter.guild.id)
        view = LaneButtons(host_id, inter.guild.id)
        
        response = await inter.channel.send(embed=embed, view=view)

        # 4. Salva os IDs
        save_config_for_guild(inter.guild.id, "queue_channel_id", inter.channel.id)
        save_config_for_guild(inter.guild.id, "queue_message_id", response.id)

        await inter.response.send_message("✅ Fila Hextech configurada e ativada neste canal!", ephemeral=True)
    
    @commands.slash_command(name="remover_fila", description="[ADMIN] Remove a fila persistente.")
    @commands.has_permissions(administrator=True)
    async def remover_fila(self, inter):
        config = get_config_for_guild(inter.guild.id)
        
        if not config.get("queue_message_id"):
             return await inter.response.send_message("⚠ Nenhuma fila ativa para remover.", ephemeral=True)

        try:
            channel = await self.bot.fetch_channel(config["queue_channel_id"])
            message = await channel.fetch_message(config["queue_message_id"])
            await message.edit(content="❌ **Fila Hextech Desativada por um Administrador.**", embed=None, view=None)
        except:
            pass 

        # Limpa os dados persistentes
        host_id = config.get("host_id")
        save_config_for_guild(inter.guild.id, "queue_channel_id", None)
        save_config_for_guild(inter.guild.id, "queue_message_id", None)
        
        # Mantém o host_id na config, mas limpa a fila de memória
        if host_id in QUEUE_DATA: 
            QUEUE_DATA[host_id]["lanes"] = {l: [] for l in LANE_CONFIG} # Zera lanes, mantendo registrados
        
        await inter.response.send_message("✅ Fila removida com sucesso.", ephemeral=True)

    @commands.slash_command(name="setar_canais_voz", description="[ADMIN] Define os canais de voz para as teams.")
    @commands.has_permissions(administrator=True)
    async def set_voice_channels(self, inter,
                                 blue_channel: disnake.VoiceChannel,
                                 red_channel: disnake.VoiceChannel):
        
        save_config_for_guild(inter.guild.id, "team_blue_id", blue_channel.id)
        save_config_for_guild(inter.guild.id, "team_red_id", red_channel.id)
        
        await inter.response.send_message(
            f"✅ Canais de Voz definidos:\n"
            f"🔵 Time Azul: {blue_channel.mention}\n"
            f"🔴 Time Vermelho: {red_channel.mention}",
            ephemeral=True
        )

    @commands.slash_command(name="setar_log", description="[ADMIN] Define o canal para logs premium.")
    @commands.has_permissions(administrator=True)
    async def set_log_channel(self, inter, log_channel: disnake.TextChannel):
        save_config_for_guild(inter.guild.id, "log_channel_id", log_channel.id)
        await inter.response.send_message(f"✅ Canal de logs definido para: {log_channel.mention}", ephemeral=True)
    
    @commands.slash_command(name="setar_ranking", description="[ADMIN] Cria e define o Embed persistente do Ranking neste canal.")
    @commands.has_permissions(administrator=True)
    async def setar_ranking_channel(self, inter):
        config = get_config_for_guild(inter.guild.id)
        
        initial_embed = disnake.Embed(
            title="⏳ CARREGANDO RANKING HEXTECH...",
            description="Processando dados da liga. Aguarde a primeira atualização.",
            color=HEX_BLUE
        )
        response = await inter.channel.send(embed=initial_embed)
        
        save_config_for_guild(inter.guild.id, "rank_channel_id", inter.channel.id)
        save_config_for_guild(inter.guild.id, "rank_message_id", response.id)

        await update_persistent_rank_message(self.bot, inter.guild.id)

        await inter.response.send_message("✅ Ranking Hextech configurado neste canal e atualizado.", ephemeral=True)

    @commands.slash_command(name="resetar_ranking", description="[ADMIN] Zera todos os pontos do ranking e atualiza o Embed.")
    @commands.has_permissions(administrator=True)
    async def resetar_ranking(self, inter):
        save_points({})
        
        await update_persistent_rank_message(self.bot, inter.guild.id)
        
        log_embed = disnake.Embed(title="📜 LOG: Ranking Resetado", description=f"O ranking foi zerado por {inter.author.mention}.", color=disnake.Color.red())
        await send_log(inter.guild, log_embed)
        
        await inter.response.send_message("✅ Ranking zerado com sucesso e Embed atualizado.", ephemeral=True)


    # ---------------- GAME MANAGEMENT ----------------

    @commands.slash_command(name="resultado", description="[HOST] Inicia o processo de confirmação de vitória.")
    async def resultado(self, inter,
                        vencedor: str = commands.Param(choices=["Blue", "Red"])):
        
        config = get_config_for_guild(inter.guild.id)
        game_host_id = config.get("host_id")
        
        if inter.author.id != game_host_id:
            return await inter.response.send_message("❌ Apenas o host atual pode definir o resultado.", ephemeral=True)

        q = QUEUE_DATA.get(game_host_id)
        if not q or not q.get("team1"):
             return await inter.response.send_message("⚠ Nenhuma partida ativa para registrar resultado.", ephemeral=True)

        captain_blue_id = q.get("captain_blue_id")
        captain_red_id = q.get("captain_red_id")

        embed = disnake.Embed(
            title="CONFIRMAÇÃO DE VITÓRIA",
            description=f"O Host ({inter.author.mention}) declarou a vitória do Time **{vencedor}**.\n\n"
                        f"**Capitães** ({inter.guild.get_member(captain_blue_id).mention} e {inter.guild.get_member(captain_red_id).mention}), "
                        "**ambos** devem clicar no botão abaixo para validar a pontuação.",
            color=HEX_GOLD
        )
        
        view = CaptainResultButtons(vencedor, game_host_id)
        await inter.response.send_message(embed=embed, view=view)


def setup(bot):
    bot.add_cog(CustomQueueManager(bot))