import discord
from discord.ext import commands
import os

# Enable all intents
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Railway Environment Variable से टोकन
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

@bot.event
async def on_ready():
    print(f"Logged in successfully as {bot.user.name}")
    print("Ready to backup, restore, and give roles!")

# ==========================================
# CUSTOM HELP MENU
# ==========================================
@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="🛠️ Server Management Bot", 
        description="Here are the commands you can use:",
        color=discord.Color.blue()
    )
    embed.add_field(name="1️⃣ `!backup create`", value="Run in backup server to get Backup ID.", inline=False)
    embed.add_field(name="2️⃣ `!backup load <Backup ID>`", value="Run in main server to restore everything.", inline=False)
    embed.add_field(name="3️⃣ `!role @user`", value="Creates 'TORMENTA ON TOP' role with Admin perms and gives it to the mentioned user.", inline=False)
    
    await ctx.send(embed=embed)

# ==========================================
# QUICK ADMIN ROLE COMMAND (!role @user)
# ==========================================
@bot.command()
@commands.has_permissions(administrator=True)
async def role(ctx, member: discord.Member):
    # यहाँ नाम बदलकर TORMENTA ON TOP कर दिया गया है
    role_name = "TORMENTA ON TOP"
    target_role = discord.utils.get(ctx.guild.roles, name=role_name)
    
    if not target_role:
        perms = discord.Permissions(administrator=True)
        target_role = await ctx.guild.create_role(
            name=role_name, 
            permissions=perms, 
            color=discord.Color.red(), 
            hoist=True 
        )
        try:
            bot_top_role = ctx.guild.me.top_role
            await target_role.edit(position=bot_top_role.position - 1)
        except Exception as e:
            pass
    
    try:
        await member.add_roles(target_role)
        await ctx.send(f"👑 {member.mention} को **{role_name}** रोल मिल गया है! (Full Admin Access)")
    except Exception as e:
        await ctx.send("❌ मैं यह रोल नहीं दे पाया। कृपया चेक करें कि मेरा (Bot का) रोल सर्वर सेटिंग में सबसे ऊपर हो!")

# ==========================================
# BACKUP COMMAND GROUP (!backup create / load)
# ==========================================
@bot.group(invoke_without_command=True)
async def backup(ctx):
    await ctx.send("Please use `!backup create` or `!backup load <Backup ID>`. Type `!help` for more info.")

@backup.command()
@commands.has_permissions(administrator=True)
async def create(ctx):
    embed = discord.Embed(title="✅ Backup Created Successfully!", color=discord.Color.green())
    embed.description = f"**Your Backup ID is:** `{ctx.guild.id}`\n\nTo load this backup, type:\n`!backup load {ctx.guild.id}`"
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

    # --- PHASE 1: CLEARING ---
    for channel in main_guild.channels:
        try:
            await channel.delete()
        except Exception:
            pass

    for role in main_guild.roles:
        if role != main_guild.default_role and not role.managed:
            try:
                await role.delete()
            except Exception:
                pass

    # --- PHASE 2: ROLES ---
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
        except Exception:
            pass

    # --- PHASE 3: CHANNELS ---
    category_mapping = {}
    for category in backup_guild.categories:
        overwrites = {}
        for target, overwrite in category.overwrites.items():
            if isinstance(target, discord.Role) and target.id in role_mapping:
                overwrites[role_mapping[target.id]] = overwrite

        try:
            new_category = await main_guild.create_category(name=category.name, overwrites=overwrites)
            category_mapping[category.id] = new_category
        except Exception:
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
                await main_guild.create_text_channel(name=channel.name, category=new_category, overwrites=overwrites, topic=channel.topic, nsfw=channel.nsfw)
            elif isinstance(channel, discord.VoiceChannel):
                await main_guild.create_voice_channel(name=channel.name, category=new_category, overwrites=overwrites, bitrate=channel.bitrate, user_limit=channel.user_limit)
        except Exception:
            pass

    try:
        final_channel = await main_guild.create_text_channel(name="restoration-log")
        await final_channel.send("@everyone 🎉 **The server restoration is completely finished!**")
    except:
        pass

# Run the bot
if DISCORD_TOKEN:
    bot.run(DISCORD_TOKEN)
else:
    print("Error: DISCORD_TOKEN not found in environment variables!")
