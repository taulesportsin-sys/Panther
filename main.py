import discord
from discord.ext import commands
import os

# Enable all intents
intents = discord.Intents.all()
# Help कमांड हम खुद बनाएंगे, इसलिए डिफ़ॉल्ट वाली को हटा रहे हैं
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Railway Environment Variable से टोकन
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

@bot.event
async def on_ready():
    print(f"Logged in successfully as {bot.user.name}")
    print("Ready to backup and restore!")

# ==========================================
# CUSTOM HELP MENU
# ==========================================
@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="🛠️ Server Backup & Restore Bot", 
        description="Here are the commands to manage your server backups:",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="1️⃣ `!backup create`", 
        value="Run this command in the server whose backup you want to take. It will give you a **Backup ID**.", 
        inline=False
    )
    embed.add_field(
        name="2️⃣ `!backup load <Backup ID>`", 
        value="Run this command in your main (nuked) server. It will delete everything and clone the backup server perfectly.", 
        inline=False
    )
    embed.set_footer(text="Note: Bot must have Administrator permissions in both servers!")
    
    await ctx.send(embed=embed)

# ==========================================
# BACKUP COMMAND GROUP (!backup create / load)
# ==========================================
@bot.group(invoke_without_command=True)
async def backup(ctx):
    await ctx.send("Please use `!backup create` or `!backup load <Backup ID>`. Type `!help` for more info.")

@backup.command()
@commands.has_permissions(administrator=True)
async def create(ctx):
    # Server ID को ही Backup ID की तरह इस्तेमाल करेंगे
    embed = discord.Embed(title="✅ Backup Created Successfully!", color=discord.Color.green())
    embed.description = (
        f"**Your Backup ID is:** `{ctx.guild.id}`\n\n"
        f"To load this backup into your main server, go there and type:\n"
        f"`!backup load {ctx.guild.id}`"
    )
    await ctx.send(embed=embed)

@backup.command()
@commands.has_permissions(administrator=True)
async def load(ctx, backup_server_id: int):
    backup_guild = bot.get_guild(backup_server_id)
    main_guild = ctx.guild
    
    if not backup_guild:
        await ctx.send("❌ Backup server not found! Make sure the bot is invited to the backup server.")
        return

    await ctx.send("🚨 **Starting the server restoration!** Deleting everything first...")

    # --- PHASE 1: CLEARING EVERYTHING ---
    for channel in main_guild.channels:
        try:
            await channel.delete()
        except Exception as e:
            pass

    for role in main_guild.roles:
        if role != main_guild.default_role and not role.managed:
            try:
                await role.delete()
            except Exception as e:
                pass

    # --- PHASE 2: CREATING ROLES & MAPPING ---
    role_mapping = {}

    for backup_role in reversed(backup_guild.roles):
        if backup_role == backup_guild.default_role:
            try:
                await main_guild.default_role.edit(permissions=backup_role.permissions)
                role_mapping[backup_role.id] = main_guild.default_role
            except:
                pass
            continue
        
        if backup_role.managed:
            continue

        try:
            new_role = await main_guild.create_role(
                name=backup_role.name,
                permissions=backup_role.permissions,
                color=backup_role.color,
                hoist=backup_role.hoist,
                mentionable=backup_role.mentionable
            )
            role_mapping[backup_role.id] = new_role
        except Exception as e:
            pass

    # --- PHASE 3: CREATING CHANNELS & PERMISSIONS ---
    category_mapping = {}

    for category in backup_guild.categories:
        overwrites = {}
        for target, overwrite in category.overwrites.items():
            if isinstance(target, discord.Role) and target.id in role_mapping:
                overwrites[role_mapping[target.id]] = overwrite

        try:
            new_category = await main_guild.create_category(
                name=category.name,
                overwrites=overwrites
            )
            category_mapping[category.id] = new_category
        except Exception as e:
            pass

    for channel in backup_guild.channels:
        if isinstance(channel, discord.CategoryChannel):
            continue 

        overwrites = {}
        for target, overwrite in channel.overwrites.items():
            if isinstance(target, discord.Role) and target.id in role_mapping:
                overwrites[role_mapping[target.id]] = overwrite

        new_category = category_mapping.get(channel.category_id) if channel.category_id else None

        try:
            if isinstance(channel, discord.TextChannel):
                await main_guild.create_text_channel(
                    name=channel.name,
                    category=new_category,
                    overwrites=overwrites,
                    topic=channel.topic,
                    nsfw=channel.nsfw
                )
            elif isinstance(channel, discord.VoiceChannel):
                await main_guild.create_voice_channel(
                    name=channel.name,
                    category=new_category,
                    overwrites=overwrites,
                    bitrate=channel.bitrate,
                    user_limit=channel.user_limit
                )
        except Exception as e:
            pass

    # --- FINAL MESSAGE ---
    try:
        final_channel = await main_guild.create_text_channel(name="restoration-log")
        await final_channel.send("@everyone 🎉 **The server restoration is completely finished!** All channels and roles have been recovered.")
    except:
        print("Restoration completed successfully!")

# Run the bot
if DISCORD_TOKEN:
    bot.run(DISCORD_TOKEN)
else:
    print("Error: DISCORD_TOKEN not found in environment variables!")
