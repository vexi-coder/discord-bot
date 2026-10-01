main.pyimport discord
from discord.ext import commands
from discord.ui import Button, View
import json
import os
import random

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ---------- CONFIG (CHANGE THESE) ----------
WELCOME_CHANNEL_ID = 0          # put your welcome channel id
VERIFY_CHANNEL_ID = 0           # channel where verify button will be
VERIFIED_ROLE_ID = 0            # role people get after verifying
LEVEL_UP_CHANNEL_ID = 0         # 0 = same channel the message was sent in

TOKEN = "YOUR_BOT_TOKEN_HERE"
# ------------------------------------------

# create levels file if it doesn't exist
if not os.path.exists("levels.json"):
    with open("levels.json", "w") as f:
        json.dump({}, f)

def load_levels():
    with open("levels.json", "r") as f:
        return json.load(f)

def save_levels(data):
    with open("levels.json", "w") as f:
        json.dump(data, f, indent=4)

def get_level(xp):
    return int((xp ** 0.5) / 2)

class VerifyView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Verify", style=discord.ButtonStyle.green, custom_id="verify_button")
    async def verify(self, interaction: discord.Interaction, button: Button):
        role = interaction.guild.get_role(VERIFIED_ROLE_ID)
        if role is None:
            await interaction.response.send_message("Verified role not found.", ephemeral=True)
            return
        if role in interaction.user.roles:
            await interaction.response.send_message("You are already verified!", ephemeral=True)
            return
        await interaction.user.add_roles(role)
        await interaction.response.send_message("✅ You are now verified!", ephemeral=True)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    bot.add_view(VerifyView())

@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="Welcome!",
            description=f"Hey {member.mention}, welcome to the server!\nPlease verify to unlock the channels.",
            color=discord.Color.blurple()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await channel.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    data = load_levels()
    user_id = str(message.author.id)
    guild_id = str(message.guild.id)

    if guild_id not in data:
        data[guild_id] = {}
    if user_id not in data[guild_id]:
        data[guild_id][user_id] = {"xp": 0, "level": 0}

    data[guild_id][user_id]["xp"] += random.randint(15, 25)
    new_level = get_level(data[guild_id][user_id]["xp"])

    if new_level > data[guild_id][user_id]["level"]:
        data[guild_id][user_id]["level"] = new_level
        channel = bot.get_channel(LEVEL_UP_CHANNEL_ID) if LEVEL_UP_CHANNEL_ID else message.channel
        await channel.send(f"🎉 {message.author.mention} just reached **Level {new_level}**!")

    save_levels(data)
    await bot.process_commands(message)

@bot.command()
async def rank(ctx, member: discord.Member = None):
    member = member or ctx.author
    data = load_levels()
    guild_id = str(ctx.guild.id)
    user_id = str(member.id)

    if guild_id not in data or user_id not in data[guild_id]:
        await ctx.send(f"{member.display_name} has no rank yet.")
        return

    xp = data[guild_id][user_id]["xp"]
    level = data[guild_id][user_id]["level"]
    await ctx.send(f"**{member.display_name}** — Level **{level}** | XP: **{xp}**")

@bot.command()
@commands.has_permissions(administrator=True)
async def setupverify(ctx):
    embed = discord.Embed(
        title="Verification",
        description="Click the button below to verify and get access to the server.",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed, view=VerifyView())
    await ctx.message.delete()

bot.run(TOKEN)
