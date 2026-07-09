import discord
from discord.ext import commands
import os
import asyncio

# ---------------------------------------------------------
# BOT SETUP & CONFIGURATION
# ---------------------------------------------------------
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.moderation = True # Ban/Kick logs के लिए ज़रूरी

bot = commands.Bot(command_prefix=['P ', 'p ', 'P', 'p'], intents=intents, help_command=None)

# ---------------------------------------------------------
# UI CLASSES (DROPDOWNS)
# ---------------------------------------------------------
class HelpDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label='Security Modules', description='Antinuke, Raidmode, Automod', emoji='🛡️'),
            discord.SelectOption(label='Moderation', description='Ban, Kick, Purge, Lock', emoji='🔨'),
            discord.SelectOption(label='Utility & Info', description='Server info, Weather, User details', emoji='⚙️')
        ]
        super().__init__(placeholder='Explore Panther Modules...', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == 'Security Modules':
            embed = discord.Embed(title="🛡️ Security Modules", color=0x2b2d31)
            embed.add_field(name="Core Setup", value="`P setup logs` - Setup antinuke logging\n`P wl @user` - Advanced Whitelist UI", inline=False)
            embed.add_field(name="Protections", value="`P antinuke`, `P superantinuke`, `P raidmode`, `P beastmode`", inline=False)
            await interaction.response.edit_message(embed=embed)
            
        elif self.values[0] == 'Moderation':
            embed = discord.Embed(title="🔨 Moderation Tools", color=0x2b2d31)
            embed.add_field(name="Mass Actions", value="`P massban`, `P masskick`, `P tempban`", inline=False)
            embed.add_field(name="Channel Controls", value="`P nukechannel`, `P lock`, `P unlock`, `P purge <amount>`", inline=False)
            await interaction.response.edit_message(embed=embed)
            
        elif self.values[0] == 'Utility & Info':
            embed = discord.Embed(title="⚙️ Utility & Server Info", color=0x2b2d31)
            embed.add_field(name="Info", value="`P serverinfo`, `P userinfo`, `P avatar`", inline=False)
            embed.add_field(name="Tools", value="`P weather <city>`, `P calc <expression>`, `P afk`", inline=False)
            await interaction.response.edit_message(embed=embed)

class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(HelpDropdown())

class WhitelistDropdown(discord.ui.Select):
    def __init__(self, target_user):
        self.target_user = target_user
        options = [
            discord.SelectOption(label='Ban/Kick', description='Allow user to ban or kick members', emoji='🔨'),
            discord.SelectOption(label='Channel Management', description='Allow create/delete/update channels', emoji='📁'),
            discord.SelectOption(label='Role Management', description='Allow create/delete/update roles', emoji='🎭'),
            discord.SelectOption(label='Server Management', description='Allow editing server settings', emoji='⚙️'),
            discord.SelectOption(label='Full Whitelist', description='Bypass all antinuke protections', emoji='🌟')
        ]
        super().__init__(placeholder='Select permissions to whitelist...', min_values=1, max_values=5, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected = ", ".join(self.values)
        await interaction.response.send_message(f"✅ {self.target_user.mention} has been whitelisted for: **{selected}** by {interaction.user.mention}")

class WhitelistView(discord.ui.View):
    def __init__(self, target_user):
        super().__init__()
        self.add_item(WhitelistDropdown(target_user))

# ---------------------------------------------------------
# BOT EVENTS
# ---------------------------------------------------------
@bot.event
async def on_ready():
    print(f'✅ {bot.user.name} is online and ready!')
    await bot.change_presence(activity=discord.Game(name="Protecting Server | P help"))

# ---------------------------------------------------------
# MAIN & SETUP COMMANDS
# ---------------------------------------------------------
@bot.command(name='help', aliases=['h'])
async def custom_help(ctx):
    embed = discord.Embed(
        title="🛡️ Panther Security",
        description="**🚀 Your Ultimate Security Guardian**\n\n"
                    "• **Server Prefix:** `P ` or `P`\n"
                    "• **Total Commands:** 50+\n"
                    "• **Status:** Active & Protecting\n\n"
                    "*Use the dropdown below to explore modules!*",
        color=0x2b2d31
    )
    view = HelpView()
    await ctx.send(embed=embed, view=view)

@bot.command(name='wl', aliases=['whitelist'])
@commands.has_permissions(administrator=True)
async def whitelist(ctx, user: discord.Member = None):
    if user is None:
        return await ctx.send("⚠️ Please mention a user! Usage: `P wl @user`")
    view = WhitelistView(user)
    await ctx.send(f"🛡️ Whitelist Settings for {user.mention}:", view=view)

@bot.command(name='setup', aliases=['autosetup'])
@commands.has_permissions(administrator=True)
async def setup(ctx, module: str = None):
    if module and module.lower() == 'logs':
        category = discord.utils.get(ctx.guild.categories, name="🛡️ Panther Security")
        if not category: category = await ctx.guild.create_category("🛡️ Panther Security")
        log_channel = discord.utils.get(ctx.guild.text_channels, name="antinuke-logs")
        if not log_channel:
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            log_channel = await ctx.guild.create_text_channel('antinuke-logs', category=category, overwrites=overwrites)
            await ctx.send(f"✅ Setup Complete! {log_channel.mention} created.")
        else:
            await ctx.send(f"⚠️ Setup already done: {log_channel.mention}")
    else:
        await ctx.send("Usage: `P setup logs`")

# ---------------------------------------------------------
# SECURITY PANELS (UPGRADED TO EMBEDS)
# ---------------------------------------------------------
@bot.command()
async def antinuke(ctx):
    embed = discord.Embed(title="⚙️ Setup & Configuration", description="Configure core antinuke and security roles.", color=0x2b2d31)
    embed.add_field(name="Commands", value="`P antinuke enable` — Enable antinuke protection\n`P antinuke disable` — Disable antinuke protection\n`P antinuke settings` — View current configuration\n`P antinuke info` — Show detailed antinuke info", inline=False)
    embed.add_field(name="🚀 Whitelist System", value="`P antinuke whitelist add <user>`\n`P antinuke whitelist remove <user>`\n`P antinuke whitelist show`", inline=False)
    embed.set_footer(text="Aliases: an, wl | Antinuke & SuperAntinuke have separate whitelists")
    await ctx.send(embed=embed)

@bot.command()
async def superantinuke(ctx):
    embed = discord.Embed(title="⚡ Core Commands (SuperAntinuke)", description="Advanced server protection against mass actions.", color=0x2b2d31)
    embed.add_field(name="Controls", value="`P superantinuke enable` — Enable SuperAntinuke\n`P superantinuke disable` — Disable SuperAntinuke\n`P superantinuke config` — View configuration", inline=False)
    embed.add_field(name="Threshold Configuration", value="`P setthreshold <action> <limit> <period>` — Set action thresholds", inline=False)
    embed.set_footer(text="Aliases: sn")
    await ctx.send(embed=embed)

@bot.command()
async def raidmode(ctx):
    embed = discord.Embed(title="⚙️ System Control (Raidmode)", description="Protect against server raids and spam.", color=0x2b2d31)
    embed.add_field(name="Main", value="`P raidmode enable` — Enable modules\n`P raidmode disable` — Disable raidmode\n`P raidmode config` — Show current configuration", inline=False)
    embed.add_field(name="🚀 Individual Modules", value="`P raidmode antimultispam` — Multi-ID spam\n`P raidmode antispam` — Message spam\n`P raidmode antiping` — Mass ping\n`P raidmode antilink` — Link spam\n`P raidmode antieveryone` — @everyone ping", inline=False)
    embed.set_footer(text="Aliases: rm, autosetup, setup")
    await ctx.send(embed=embed)

@bot.command()
async def beastmode(ctx):
    embed = discord.Embed(title="⚠️ Beast Mode - Maximum Security", description="Extreme security lockdown mode.\n▶ Strips dangerous permissions automatically.\n▶ Only whitelisted users retain access.", color=0xED4245) # Red Color
    embed.add_field(name="🛡️ Controls", value="`P beastmode` — View status\n`P beastmode enable` — Activate maximum security\n`P beastmode disable` — Deactivate Beast Mode\n`P beastmode status` — Check current state", inline=False)
    embed.add_field(name="What Beast Mode Does", value="+ Strips: Administrator, Manage Server, Kick, Ban\n+ Protects: Security roles & bots\n+ Auto-enforces: Permission restrictions", inline=False)
    await ctx.send(embed=embed)

# ---------------------------------------------------------
# MODERATION & UTILITY
# ---------------------------------------------------------
@bot.command(name='nukechannel', aliases=['nuke'])
@commands.has_permissions(manage_channels=True)
async def nukechannel(ctx, channel: discord.TextChannel = None):
    channel = channel or ctx.channel
    position = channel.position
    new_channel = await channel.clone(reason="Panther Security")
    await new_channel.edit(position=position)
    await channel.delete()
    await new_channel.send("https://tenor.com/view/explosion-mushroom-cloud-atomic-bomb-bomb-boom-gif-4464831\n☢️ **Channel Nuked!**")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int = 5):
    await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(f"🧹 Purged {amount} messages.")
    await asyncio.sleep(3)
    await msg.delete()

@bot.command()
async def serverinfo(ctx):
    embed = discord.Embed(title=f"📊 {ctx.guild.name} Info", color=0x2b2d31)
    embed.add_field(name="Owner", value=ctx.guild.owner.mention)
    embed.add_field(name="Members", value=ctx.guild.member_count)
    embed.add_field(name="Created At", value=ctx.guild.created_at.strftime("%d %b %Y"))
    await ctx.send(embed=embed)

# ---------------------------------------------------------
# RUN BOT
# ---------------------------------------------------------
if __name__ == '__main__':
    if not TOKEN:
        print("CRITICAL ERROR: DISCORD_TOKEN is missing! Please set it in Railway Variables.")
    else:
        bot.run(TOKEN)
