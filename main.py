import discord
from discord.ext import commands, tasks
import datetime
import os

# ==========================================
# ⚙️ BOT SETUP & INTENTS
# ==========================================
intents = discord.Intents.all()
# Disabled default help command to use our custom embed one
bot = commands.Bot(command_prefix='$', intents=intents, help_command=None)

# Blacklist Words for Auto-Mod
BLACKLIST_WORDS = ["scammer", "स्कैमर", "gaali1", "gaali2"] 

# Embed Helper Function to keep messages looking clean
def create_embed(title, description, color=discord.Color.dark_theme()):
    return discord.Embed(title=title, description=description, color=color)

@bot.event
async def on_ready():
    print(f'✅ Bot is ready! Logged in as {bot.user}')
    daily_tasks.start() # Starts the background tasks (like the 12 PM check)

# ==========================================
# 🛡️ AUTO-MODERATION (7-Day Timeout System)
# ==========================================
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Check if user has the Top Role (Panther Owner) so admins don't get muted
    has_admin = any(role.name == "Panther Owner" for role in message.author.roles)
    
    if not has_admin:
        msg_content = message.content.lower()
        if any(word in msg_content for word in BLACKLIST_WORDS):
            await message.delete()
            
            # 7 Days Timeout (168 hours)
            duration = datetime.timedelta(days=7)
            try:
                await message.author.timeout(duration, reason="Using abusive words or scammer tag")
                embed = create_embed("⚠️ Auto-Mod Action", f"**{message.author.mention}** has been timed out for 7 days for using prohibited words.")
                await message.channel.send(embed=embed)
            except discord.Forbidden:
                pass # Ignore if bot lacks permission to timeout someone higher than it

    # Process commands normally if no bad words are found
    await bot.process_commands(message)

# ==========================================
# 🛠️ ROLE CREATION (Run this first!)
# ==========================================
@bot.command()
@commands.has_permissions(administrator=True)
async def createroles(ctx):
    roles_to_create = ["Panther Owner", "Panther Charmer"]
    created = []
    
    for role_name in roles_to_create:
        existing_role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not existing_role:
            # Creating role without any specific color (default color)
            await ctx.guild.create_role(name=role_name, color=discord.Color.default(), reason="Panther Bot Setup")
            created.append(role_name)
            
    if created:
        embed = create_embed("✅ Roles Created", f"Successfully created: **{', '.join(created)}**")
    else:
        embed = create_embed("⚠️ Info", "Roles already exist in the server.")
    await ctx.send(embed=embed)

# ==========================================
# 👑 OWNER COMMANDS (Panther Owner Only)
# ==========================================
@bot.command()
@commands.has_role("Panther Owner")
async def addstaff(ctx, member: discord.Member, role: discord.Role):
    await member.add_roles(role)
    embed = create_embed("🎉 New Staff Added!", f"**{member.mention}** has been given the **{role.mention}** role.")
    await ctx.send(embed=embed)

@bot.command()
@commands.has_role("Panther Owner")
async def promote(ctx, member: discord.Member, role: discord.Role):
    await member.add_roles(role)
    embed = create_embed("🎊 Staff Promoted!", f"Congratulations **{member.mention}**! You have been promoted to **{role.mention}**.")
    await ctx.send(embed=embed)

@bot.command()
@commands.has_role("Panther Owner")
async def demote(ctx, member: discord.Member, role: discord.Role):
    await member.remove_roles(role)
    embed = create_embed("📉 Staff Demoted", f"**{member.mention}** has been removed from **{role.mention}**.")
    await ctx.send(embed=embed)

@bot.command()
@commands.has_role("Panther Owner")
async def serverinfo(ctx):
    guild = ctx.guild
    desc = f"**Total Members:** {guild.member_count}\n**Boosts:** {guild.premium_subscription_count}"
    embed = create_embed(f"📊 {guild.name} - Server Info", desc)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_role("Panther Owner")
async def say(ctx, channel: discord.TextChannel, *, message: str):
    embed = create_embed("📢 Announcement", message)
    await channel.send(embed=embed)
    await ctx.send("✅ Message sent!", delete_after=3)

@bot.command()
@commands.has_role("Panther Owner")
async def dm(ctx, user: discord.Member, *, message: str):
    embed = create_embed("📩 Message from Server Staff", message)
    try:
        await user.send(embed=embed)
        await ctx.send("✅ DM sent!", delete_after=3)
    except:
        await ctx.send("❌ Cannot send DM to this user.")

# ==========================================
# 👥 STAFF COMMANDS (Panther Charmer & Owner)
# ==========================================
@bot.command()
@commands.has_any_role("Panther Owner", "Panther Charmer")
async def vc(ctx, start_time: str, end_time: str):
    embed = create_embed("✅ VC Time Logged", f"**{ctx.author.mention}**, your VC shift from **{start_time}** to **{end_time}** has been saved.")
    await ctx.send(embed=embed)

@bot.command()
@commands.has_any_role("Panther Owner", "Panther Charmer")
async def active(ctx):
    embed = create_embed("📝 Attendance Logged", f"**{ctx.author.mention}** has marked their daily attendance.")
    await ctx.send(embed=embed)

@bot.command()
@commands.has_any_role("Panther Owner", "Panther Charmer")
async def loa(ctx, days: str, *, reason: str):
    embed = create_embed("✈️ Leave of Absence", f"**{ctx.author.mention}** is on leave for **{days}**.\n**Reason:** {reason}")
    await ctx.send(embed=embed)

@bot.command()
@commands.has_any_role("Panther Owner", "Panther Charmer")
async def done(ctx):
    embed = create_embed("✅ Task Completed", f"**{ctx.author.mention}** has successfully completed their assigned task.")
    await ctx.send(embed=embed)

# ==========================================
# 🆘 CUSTOM HELP MENU (Embed Format)
# ==========================================
@bot.command(name="help")
async def custom_help(ctx):
    embed = discord.Embed(
        title="🛠️ Panther Bot - Help Menu", 
        description="Here is the list of all available commands for this server:", 
        color=discord.Color.dark_theme()
    )
    
    embed.add_field(
        name="👑 Owner Commands (Panther Owner)", 
        value="**$addstaff @user @role** - Add new staff\n**$promote @user @role** - Promote staff\n**$demote @user @role** - Demote staff\n**$serverinfo** - Show server details\n**$say #channel [msg]** - Send embed message\n**$dm @user [msg]** - Send DM via bot", 
        inline=False
    )
    
    embed.add_field(
        name="👥 Staff Commands (Panther Charmer)", 
        value="**$vc [start] [end]** - Log your VC time\n**$active** - Mark daily attendance\n**$loa [days] [reason]** - Request leave of absence\n**$done** - Mark assigned task as done", 
        inline=False
    )
    
    embed.add_field(
        name="⚙️ Setup Commands (Admin)", 
        value="**$createroles** - Auto-create necessary roles for the bot", 
        inline=False
    )
    
    avatar_url = ctx.author.display_avatar.url if ctx.author.display_avatar else None
    embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=avatar_url)
    
    await ctx.send(embed=embed)

# ==========================================
# 🚀 AUTOMATED TASKS
# ==========================================
@tasks.loop(minutes=1)
async def daily_tasks():
    now = datetime.datetime.now()
    # Placeholder for the 12 PM Attendance Check
    if now.hour == 12 and now.minute == 0:
        print("Checking 12 PM attendance deadline...")

# ==========================================
# ❌ ERROR HANDLING (Prevents Console Spam)
# ==========================================
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRole) or isinstance(error, commands.MissingAnyRole):
        pass # Silently ignore if a normal user tries to run a locked command

# ==========================================
# 🚀 RUN THE BOT
# ==========================================
# Uses Railway's Environment Variable for the Token
bot.run(os.getenv('DISCORD_TOKEN'))
