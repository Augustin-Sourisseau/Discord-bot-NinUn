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

def get_user_profile(donnees, user_id):
    user_id = str(user_id)

    if "users" not in donnees:
        donnees["users"] = {}

    if user_id not in donnees["users"]:
        donnees["users"][user_id] = {
            "streak": 0,
            "record": 0,
            "successes": 0,
            "breaks": 0
        }

    return donnees["users"][user_id]

@bot.event
async def on_message(message):
    global last_send_time, pending_update

    if message.author.bot:
        return

    # ===== Autoriser les commandes partout =====
    if message.content.startswith(bot.command_prefix):
        await bot.process_commands(message)
        return

    # ===== Salon réservé à la streak =====
    if message.channel.id != int(os.getenv('CHANNEL_ID')):
        return

    with open('sauvegarde.json', 'r', encoding='utf-8') as fichier:
        donnees = json.load(fichier)

    # ===== PROFIL UTILISATEUR =====
    profil = get_user_profile(donnees, message.author.id)

    # ===== STATS GLOBALES =====
    streak = donnees["all"]["streak"]
    record = donnees["all"]["record"]

    current_time = time.time()

    if MESSAGE_CIBLE in message.content:

        # Global
        streak += 1
        if streak > record:
            record = streak

        # User
        profil["streak"] += 1
        profil["successes"] += 1

        if profil["streak"] > profil["record"]:
            profil["record"] = profil["streak"]

        pending_update = True

    else:

        # Si quelqu’un casse la streak
        if streak != 0:
            await message.channel.send(
                f"❌ {message.author.mention} a cassé la streak !\n"
                f"🔥 Score final : {streak}\n"
                f"🏆 Record : {record}"
            )

        # Reset global
        streak = 0
        pending_update = False

        # Stats user
        profil["breaks"] += 1
        profil["streak"] = 0

    # ===== COOLDOWN =====
    if pending_update and (current_time - last_send_time >= COOLDOWN):

        await message.channel.send(
            f"🔥 Streak actuel : {streak}\n"
            f"🏆 Record : {record}"
        )

        last_send_time = current_time
        pending_update = False

    # ===== SAUVEGARDE =====
    donnees["all"]["streak"] = streak
    donnees["all"]["record"] = record

    with open('sauvegarde.json', 'w', encoding='utf-8') as fichier:
        json.dump(donnees, fichier, indent=4, ensure_ascii=False)

    await bot.process_commands(message)


#commande pour voir son profil

@bot.command()
async def profil(ctx, membre: discord.Member = None):

    if membre is None:
        membre = ctx.author

    with open('sauvegarde.json', 'r', encoding='utf-8') as fichier:
        donnees = json.load(fichier)

    profil = get_user_profile(donnees, membre.id)

    embed = discord.Embed(
        title=f"Profil de {membre.name}",
        color=discord.Color.orange()
    )

    embed.add_field(
        name="🔥 Streak actuelle",
        value=profil["streak"],
        inline=False
    )

    embed.add_field(
        name="🏆 Record personnel",
        value=profil["record"],
        inline=False
    )

    embed.add_field(
        name="✅ GIFs réussis",
        value=profil["successes"],
        inline=False
    )

    embed.add_field(
        name="❌ Streaks cassées",
        value=profil["breaks"],
        inline=False
    )

    await ctx.send(embed=embed)


#commande de classement du record streak personnel

@bot.command()
async def record(ctx):

    with open('sauvegarde.json', 'r', encoding='utf-8') as fichier:
        donnees = json.load(fichier)

    users = donnees.get("users", {})

    # Tri par record décroissant
    classement = sorted(
        users.items(),
        key=lambda x: x[1]["record"],
        reverse=True
    )

    embed = discord.Embed(
        title="🏆 Classement des records",
        color=discord.Color.gold()
    )

    description = ""

    for i, (user_id, stats) in enumerate(classement[:10], start=1):

        user = bot.get_user(int(user_id))

        if user is None:
            user = await bot.fetch_user(int(user_id))

        description += (
            f"**{i}. {user.name}** — "
            f"{stats['record']} 🔥\n"
        )

    if description == "":
        description = "Aucune donnée."

    embed.description = description

    await ctx.send(embed=embed)


#commande classement briseur de streak

@bot.command()
async def casseurs(ctx):

    with open('sauvegarde.json', 'r', encoding='utf-8') as fichier:
        donnees = json.load(fichier)

    users = donnees.get("users", {})

    # Tri par nombre de streaks cassées
    classement = sorted(
        users.items(),
        key=lambda x: x[1]["breaks"],
        reverse=True
    )

    embed = discord.Embed(
        title="💀 Classement des casseurs de streak",
        color=discord.Color.red()
    )

    description = ""

    for i, (user_id, stats) in enumerate(classement[:10], start=1):

        user = bot.get_user(int(user_id))

        if user is None:
            user = await bot.fetch_user(int(user_id))

        description += (
            f"**{i}. {user.name}** — "
            f"{stats['breaks']} 💥\n"
        )

    if description == "":
        description = "Aucune donnée."

    embed.description = description

    await ctx.send(embed=embed)

bot.run(os.getenv('DISCORD_TOKEN'))