import discord
import os
import json
import time
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

MESSAGE_CIBLE = "https://cdn.discordapp.com/attachments/1464271289308025050/1471507852131700827/9BF75FB6-2C3B-42AB-B76D-E5573BBBB2D9.gif"

last_send_time = 0
COOLDOWN = 2  # secondes

pending_update = False  # savoir si on doit envoyer un message

@bot.event
async def on_ready():
    print(f"Connecté en tant que {bot.user}")

@bot.event
async def on_message(message):
    global last_send_time, pending_update
    with open('sauvegarde.json', 'r', encoding='utf-8') as fichier:
        donnees = json.load(fichier)
    streak = donnees["all"]["streak"]
    record = donnees["all"]["record"]
    if message.author.bot:
        return

    if message.channel.id != int(os.getenv('CHANNEL_ID')):
        return

    if MESSAGE_CIBLE in message.content:
        streak += 1

        if streak > record:
            record = streak

        

        pending_update = True  # on marque qu’il faut update

    else:
        if streak != 0:
            await message.channel.send(
                f"❌ Streak cassé ! Score final : {streak}\n🏆 Record : {record}"
            )

        streak = 0
        pending_update = False

    # Gestion cooldown envoi
    current_time = time.time()

    if pending_update and (current_time - last_send_time >= COOLDOWN):
        await message.channel.send(
            f"🔥 Streak actuel : {streak}\n🏆 Record : {record}"
        )
        last_send_time = current_time
        pending_update = False
    donnees["all"]["streak"] = streak
    donnees["all"]["record"] = record
    with open('sauvegarde.json', 'w', encoding='utf-8') as fichier:
        json.dump(donnees, fichier, indent=4, ensure_ascii=False)
    await bot.process_commands(message)

bot.run(os.getenv('DISCORD_TOKEN'))