import discord
from discord.ext import commands
import os  # Railway (Environment Variables) से डेटा उठाने के लिए

# Enable all intents so the bot can read roles, channels, and members
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# --- Railway से ऑटोमैटिक टोकन उठाने के लिए ---
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

@bot.event
async def on_ready():
    print(f"Logged in successfully as {bot.user.name}")
    print("Ready to restore servers!")

@bot.command()
@commands.has_permissions(administrator=True)
async def restore(ctx, backup_server_id: int):
    # Fetch the backup server using the ID provided in the command
    backup_guild = bot.get_guild(backup_server_id)
    main_guild = ctx.guild
    
    if not backup_guild:
        await ctx.send("Backup server not found! Make sure the bot is invited to the backup server.")
        return

    await ctx.send("🚨 Starting the server restoration! Deleting everything first...")

    # ==========================================
    # PHASE 1: CLEARING EVERYTHING
    # ==========================================
    
    # 1. Delete all channels and categories
    for channel in main_guild.channels:
        try:
            await channel.delete()
        except Exception as e:
            print(f"Skipped channel {channel.name}: {e}")

    # 2. Delete all roles
    # Note: We cannot delete @everyone, and we shouldn't delete the bot's own integration roles.
    for role in main_guild.roles:
        if role != main_guild.default_role and not role.managed:
            try:
                await role.delete()
            except Exception as e:
                print(f"Skipped role {role.name} (Bot role is likely lower than this role)")

    # ==========================================
    # PHASE 2: CREATING ROLES & MAPPING
    # ==========================================
    
    role_mapping = {}

    print("Creating Roles...")
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
            print(f"Could not create role {backup_role.name}: {e}")

    # ==========================================
    # PHASE 3: CREATING CHANNELS & PERMISSIONS
    # ==========================================
    
    category_mapping = {}

    print("Creating Categories...")
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
            print(f"Error creating category {category.name}")

    print("Creating Channels...")
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
            print(f"Error creating channel {channel.name}")

    try:
        final_channel = await main_guild.create_text_channel(name="restoration-log")
        await final_channel.send("@everyone The server restoration is completely finished! 🎉")
    except:
        print("Restoration completed successfully!")

# Run the bot
if DISCORD_TOKEN:
    bot.run(DISCORD_TOKEN)
else:
    print("Error: DISCORD_TOKEN not found in environment variables!")
