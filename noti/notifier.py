import asyncio
import websockets
import discord
from discord.ext import commands
import aiohttp
import re

# ⚙️ Configuración
DISCORD_TOKEN = "examplede token"   # 🔑 Token de tu bot (Discord Developer Portal)
CHANNEL_ID = example  # ID del canal donde quieres las notificaciones
WEBSOCKET_URL = "ws://127.0.0.1:example"  # Debe coincidir con roblox.py (WEBSOCKET_PORT)

# 🚀 Inicializar bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# 🛠️ Regex para extraer placeId y jobId de mensajes tipo TeleportService
TELEPORT_REGEX = re.compile(
    r"TeleportToPlaceInstance\((\d+),\"([a-f0-9\-]+)\"",
    re.IGNORECASE
)

async def get_game_name(place_id: int) -> str:
    """Consulta el nombre del juego en la API de Roblox"""
    url = f"https://games.roblox.com/v1/games/multiget-place-details?placeIds={place_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data and len(data) > 0:
                    return data[0].get("name", "Juego desconocido")
    return "Juego desconocido"

async def listen_ws():
    """Escucha mensajes del websocket de roblox.py y los reenvía a Discord"""
    await bot.wait_until_ready()
    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print("❌ No se encontro el canal, revisa CHANNEL_ID")
        return

    async with websockets.connect(WEBSOCKET_URL) as ws:
        print(f"✅ Conectado al websocket {WEBSOCKET_URL}")
        while True:
            try:
                msg = await ws.recv()
                print(f"📩 Recibido: {msg}")

                embed = None

                # 🔎 Si el mensaje es TeleportService (contiene placeId + jobId)
                match = TELEPORT_REGEX.search(msg)
                if match:
                    place_id = int(match.group(1))
                    job_id = match.group(2)

                    game_name = await get_game_name(place_id)

                    embed = discord.Embed(
                        title=f"🌌 Servidor encontrado en {game_name}",
                        description=f"**Place ID:** `{place_id}`\n**Job ID:** `{job_id}`",
                        color=discord.Color.red()
                    )

                # 🔎 Si el mensaje es un JobId crudo (corto)
                elif len(msg) < 100:
                    embed = discord.Embed(
                        title="🌌 Servidor 10M+ encontrado",
                        description=f"**Job ID:** `{msg}`",
                        color=discord.Color.orange()
                    )

                # 🔎 Si es un script largo normal
                else:
                    embed = discord.Embed(
                        title="🌀 Servidor normal encontrado",
                        description=f"```lua\n{msg}\n```",
                        color=discord.Color.green()
                    )

                if embed:
                    await channel.send(embed=embed)
                    print(f"✅ Enviado a Discord: {embed.title}")
                else:
                    print("⚠️ Mensaje recibido pero no reconocido")

            except Exception as e:
                print(f"⚠️ Error en WS: {e}")
                await asyncio.sleep(3)

@bot.event
async def on_ready():
    print(f"🤖 Bot conectado como {bot.user}")
    bot.loop.create_task(listen_ws())

# 🔥 Iniciar bot
bot.run(DISCORD_TOKEN)
