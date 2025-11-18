import disnake

HEXTECH_COLOR = 0x00B3FF  # Azul Arcano / Hextech
BORDER_GIF = "https://giffiles.alphacoders.com/528/52897.gif"
AURI_GIF = "https://giffiles.alphacoders.com/529/52955.gif"  # Ahri Fox-Fire
LUX_GIF = "https://tenor.com/view/bom-dia-viata-gif-24217246"    # Lux Light

def hextech_embed(title: str = "", description: str = "", image: str = None):
    embed = disnake.Embed(
        title=f"✨ {title}",
        description=description,
        color=HEXTECH_COLOR
    )
    embed.set_thumbnail(url=BORDER_GIF)
    if image:
        embed.set_image(url=image)
    embed.set_footer(text="League of Legends • Sistema Hextech")
    return embed
