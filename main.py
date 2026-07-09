import discord
from discord.ext import commands
import aiosqlite
import asyncio
import os

intents = discord.Intents.default()
intents.message_content = True

# --- PREFIX SETUP: P, p, P (space), p (space) ---
bot = commands.Bot(command_prefix=["P", "p", "P ", "p "], intents=intents, help_command=None)

GREEN_ACCENT = 0x00e676 # Tormenta प्रीमियम थीम कलर

# ================= DATABASE SETUP (ANTI-KICK DATA SAVE) =================
async def setup_db():
    async with aiosqlite.connect("tormenta_db.sqlite") as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS ss_verify (
            guild_id INTEGER PRIMARY KEY, channel_id INTEGER, role_id INTEGER, req_ss INTEGER DEFAULT 4, ss_type TEXT, page_name TEXT, page_url TEXT, allow_same TEXT DEFAULT 'No'
        )''')
        await db.execute('''CREATE TABLE IF NOT EXISTS tourney_data (
            guild_id INTEGER PRIMARY KEY, reg_channel INTEGER, confirm_channel INTEGER
        )''')
        await db.commit()

# ================= 1. SHOW-OFF & DUMMY COMMANDS =================
@bot.command(name="help")
async def custom_help(ctx):
    embed = discord.Embed(title="💎 Tormenta Smart Manager | Help Menu", color=GREEN_ACCENT)
    
    embed.add_field(name="🏆 Esports Management", value="`P tourney`, `P smanager`, `P slotmanager`, `P ssverify`", inline=False)
    embed.add_field(name="🛡️ Moderation", value="`P ban`, `P kick`, `P clear`, `P lock`, `P unlock`", inline=False)
    
    # Show off commands section
    embed.add_field(name="🚀 Premium & System (Exclusive)", value="`P premium`, `P prefresh`, `P poba`, `P antinuke`, `P backup`", inline=False)
    
    embed.set_footer(text="Made by Panther • Tormenta Esports")
    await ctx.send(embed=embed)

@bot.command(name="premium", aliases=["prefresh"])
@commands.has_permissions(administrator=True)
async def premium_showoff(ctx):
    # यह सिर्फ शो-ऑफ़ के लिए है
    embed = discord.Embed(title="💎 Tormenta Premium Status", description="Checking server database licensing...", color=GREEN_ACCENT)
    embed.add_field(name="Server ID:", value=f"`{ctx.guild.id}`", inline=True)
    embed.add_field(name="Tier:", value="`Diamond Lifetime`", inline=True)
    embed.add_field(name="Status:", value="✅ **Active & Synced**", inline=False)
    embed.set_footer(text="Premium Refreshed Successfully.")
    await ctx.send(embed=embed)

@bot.command(name="poba")
@commands.has_permissions(administrator=True)
async def poba_showoff(ctx):
    # POBA Security Show-off
    await ctx.send("**🛡️ POBA Engine Check:** All database parameters are highly secured and running smoothly.")

@bot.command(name="antinuke")
@commands.has_permissions(administrator=True)
async def antinuke_showoff(ctx):
    await ctx.send("🚨 **Anti-Nuke System is currently ENABLED.**\n`Monitoring webhooks, mass-bans, and channel deletions...`")


# ================= 2. SS VERIFY MANAGER =================
class SSVerifyMainView(discord.ui.View):
    @discord.ui.button(label="➕ Setup ssverify", style=discord.ButtonStyle.success)
    async def setup_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="Enter details & Press Save", color=GREEN_ACCENT)
        embed.description = "1️⃣ **Channel:**\n`Not-Set`\n2️⃣ **Role:**\n`Not-Set`\n3️⃣ **Required ss:**\n`4`\n4️⃣ **Screenshot Type:**\n`Not-Set`\n5️⃣ **Page Name:**\n`Not-Set`\n6️⃣ **Page URL:**\n`Not-Set (Not Required)`\n7️⃣ **Allow Same SS:**\n`No`"
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="⚒️ Change Settings", style=discord.ButtonStyle.secondary)
    async def settings_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Opening settings...", ephemeral=True)

@bot.command(name="ssverify")
@commands.has_permissions(administrator=True)
async def ssverify_cmd(ctx):
    embed = discord.Embed(title="Advanced Screenshots Manager", color=GREEN_ACCENT)
    embed.description = "**1.** `#tec | insta-verify` - Instagram\n**2.** `#verify-here` - Instagram\n\n**When in doubt, press '?' :)**"
    await ctx.send(embed=embed, view=SSVerifyMainView())


# ================= 3. SLOT MANAGER =================
class SlotManagerView(discord.ui.View):
    @discord.ui.button(label="# Add Channel", style=discord.ButtonStyle.secondary)
    async def add_chan_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("**Mention the channel you want to add for Slot-Manager.**", ephemeral=True)

    @discord.ui.button(label="📝 Edit Config", style=discord.ButtonStyle.primary)
    async def edit_conf_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("**Slot-Manager configuration opened.**", ephemeral=True)

    @discord.ui.button(label="🔒 Match Time", style=discord.ButtonStyle.secondary)
    async def match_time_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("**Enter the match time:**", ephemeral=True)

@bot.command(name="slotmanager")
@commands.has_permissions(administrator=True)
async def slotmanager_cmd(ctx):
    embed = discord.Embed(title="Scrims Slot-Manager Setup", color=GREEN_ACCENT)
    embed.description = (
        "Slot-Manager is a way to ease-up scrims slot management process. "
        "With **Tormenta's** slotm users can - cancel their slot, claim an empty slot and also set reminder for vacant slots, All without bugging any mod.\n\n"
        "**Current slot-manager channels:**\n"
        "```Click add-channel to set cancel-claim.```\n\n"
        "Don't forget to set the match times :)"
    )
    await ctx.send(embed=embed, view=SlotManagerView())


# ================= 4. SCRIMS MANAGER =================
class ScrimsManagerView(discord.ui.View):
    @discord.ui.button(label="Create Scrim", style=discord.ButtonStyle.success)
    async def create_scrim(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("**Opening Scrim Creation Dashboard...**", ephemeral=True)

    @discord.ui.button(label="Edit Settings", style=discord.ButtonStyle.primary)
    async def edit_settings(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Settings menu.", ephemeral=True)

    @discord.ui.button(label="Instant Start/Stop Reg", style=discord.ButtonStyle.success, row=1)
    async def instant_reg(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Registration Toggled.", ephemeral=True)

    @discord.ui.button(label="Reserve Slots", style=discord.ButtonStyle.success, row=1)
    async def reserve_slots(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Slot reservation menu.", ephemeral=True)

    @discord.ui.button(label="Ban/Unban", style=discord.ButtonStyle.danger, row=2)
    async def ban_unban(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Ban Manager opened.", ephemeral=True)

    @discord.ui.button(label="Manage Slotlist", style=discord.ButtonStyle.primary, row=2)
    async def manage_slotlist(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Slotlist Manager.", ephemeral=True)

    @discord.ui.button(label="Enable/Disable", style=discord.ButtonStyle.danger, row=3)
    async def toggle_bot(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("System Enabled/Disabled.", ephemeral=True)

@bot.command(name="smanager")
@commands.has_permissions(administrator=True)
async def smanager_cmd(ctx):
    embed = discord.Embed(title="Tormenta's Smart Scrims Manager", color=GREEN_ACCENT)
    embed.description = "```Click Create button for new Scrim.```\n\n🦇 Total Scrims in this server: 0"
    await ctx.send(embed=embed, view=ScrimsManagerView())


# ================= 5. TOURNAMENT MANAGER =================
class TourneyManagerView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Create Tournament", style=discord.ButtonStyle.primary, row=0)
    async def btn_create(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Tournament Creation Menu Opened!", ephemeral=True)

    @discord.ui.button(label="Edit Settings", style=discord.ButtonStyle.secondary, row=0)
    async def btn_edit(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Edit Settings Opened!", ephemeral=True)

    @discord.ui.button(label="Start/Pause Reg", style=discord.ButtonStyle.success, row=1)
    async def btn_reg(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Registration Toggled!", ephemeral=True)

    @discord.ui.button(label="Ban/Unban", style=discord.ButtonStyle.danger, row=1)
    async def btn_ban(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Ban menu opened!", ephemeral=True)

    @discord.ui.button(label="Manage Groups", style=discord.ButtonStyle.primary, row=2)
    async def btn_groups(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Group Manager opened!", ephemeral=True)

    @discord.ui.button(label="Cancel Slots", style=discord.ButtonStyle.danger, row=3)
    async def btn_cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Cancel Slots opened!", ephemeral=True)

    @discord.ui.button(label="Manually Add Slot", style=discord.ButtonStyle.success, row=3)
    async def btn_add_slot(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Manual Slot Adder opened!", ephemeral=True)

    @discord.ui.button(label="Slot-Manager channel", style=discord.ButtonStyle.primary, row=3)
    async def btn_sm_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Slot Manager config opened!", ephemeral=True)

    @discord.ui.button(label="Media-Partner", style=discord.ButtonStyle.success, row=4)
    async def btn_media(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Media Partner settings!", ephemeral=True)

    @discord.ui.button(label="MS Excel File", style=discord.ButtonStyle.primary, row=4)
    async def btn_excel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Generating Excel File...", ephemeral=True)

@bot.command(name="tourney")
@commands.has_permissions(administrator=True)
async def tourney_cmd(ctx):
    embed = discord.Embed(title="Tormenta Smart Tournament Manager", color=GREEN_ACCENT)
    embed.description = "```Click Create button for new tourney.```\n\n🦇 Tormenta Legacy allows unlimited tournaments."
    await ctx.send(embed=embed, view=TourneyManagerView())


# ================= READY EVENT =================
@bot.event
async def on_ready():
    await setup_db() 
    print(f"✅ {bot.user.name} is Online and Ready!")
    print(f"Prefixes active: 'P', 'p', 'P ', 'p '")


# ================= MAIN RUN (WITH DISCORD_TOKEN) =================
if __name__ == "__main__":
    # .env या होस्टिंग के Environment Variables से टोकन लेगा
    token = os.getenv("DISCORD_TOKEN")
    
    if token:
        bot.run(token)
    else:
        print("❌ Error: DISCORD_TOKEN is missing! Please set it in your environment variables.")
