import discord
from discord.ext import commands
import os
import random
import asyncio

# --- Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Prefix handler: supports 'p', 'P', 'p ', 'P '
def get_prefix(bot, message):
    return ['P ', 'p ', 'P', 'p']

bot = commands.Bot(command_prefix=get_prefix, intents=intents, help_command=None)

# --- Constants & Variables ---
OWNER_ID = 1525484718412267662
MAX_BET_LIMIT = 250000
STARTING_BALANCE = 100000
DAILY_REWARD = 15000
OWNER_BALANCE = 100000000000  # 10 followed by 10 zeros

# Database Placeholder
users_db = {}

def get_balance(user_id):
    if user_id not in users_db:
        if user_id == OWNER_ID:
            users_db[user_id] = OWNER_BALANCE
        else:
            users_db[user_id] = STARTING_BALANCE
    return users_db[user_id]

def update_balance(user_id, amount):
    users_db[user_id] = get_balance(user_id) + amount

def parse_bet(bet_str, balance):
    if bet_str.lower() == "all":
        return min(balance, MAX_BET_LIMIT)
    try:
        amount = int(bet_str)
        return amount
    except ValueError:
        return None

# --- Events & Error Handling ---
@bot.event
async def on_ready():
    print(f'✅ {bot.user} is online with ADVANCED GAMES!')
    await bot.change_presence(activity=discord.Game(name="BGMI Scrims | p help"))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ **Invalid command!** Type `p help` to see all available commands.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ **Missing arguments!** Check `p help` for the correct usage format.")

# --- Custom Help Command ---
@bot.command(name="help")
async def help_cmd(ctx):
    embed = discord.Embed(title="🤖 Ultimate Bot Commands Menu", color=0x2b2d31, description="Prefix: `p` or `P` (with or without space)")
    
    embed.add_field(name="💰 Economy", 
                    value="`p cash` - Check your current balance\n"
                          "`p daily` - Claim your daily 15,000 cash\n"
                          "`p give @user [amount]` - Transfer cash to another user", inline=False)
                    
    embed.add_field(name="🎲 Games (Max Bet: 250k)", 
                    value="`p mine [amount/all] [mines(1-15)]` - Play Interactive Minesweeper\n"
                          "`p cf [amount/all] [heads/tails]` - Flip a Coin\n"
                          "`p s [amount/all]` - Spin the Slot Machine\n"
                          "`p hl [amount/all]` - Play High-Low Card Game", inline=False)
                    
    embed.add_field(name="🏆 Scrims (Staff Only)", 
                    value="`p qualify \"Team Name\" @Role @Player1 @Player2` - Qualify team and assign roles", inline=False)
                    
    await ctx.send(embed=embed)


# --- Economy Commands ---
@bot.command(name="cash", aliases=["bal", "balance"])
async def cash(ctx, member: discord.Member = None):
    member = member or ctx.author
    bal = get_balance(member.id)
    await ctx.send(f"💳 | **{member.display_name}**, you currently have **{bal:,}** cowoncy!")

@bot.command(name="daily")
@commands.cooldown(1, 86400, commands.BucketType.user)
async def daily(ctx):
    update_balance(ctx.author.id, DAILY_REWARD)
    await ctx.send(f"💸 | **{ctx.author.display_name}**, you claimed your daily **{DAILY_REWARD:,}** cowoncy!")

@daily.error
async def daily_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ | Please wait **{error.retry_after // 3600:.0f}h** before claiming your next daily reward.")

@bot.command(name="give")
async def give(ctx, member: discord.Member, amount: int):
    if amount <= 0: return await ctx.send("❌ **Amount must be greater than 0!**")
    sender_bal = get_balance(ctx.author.id)
    if ctx.author.id != OWNER_ID and sender_bal < amount:
        return await ctx.send("❌ **You do not have enough cash!**")
        
    update_balance(ctx.author.id, -amount)
    update_balance(member.id, amount)
    await ctx.send(f"💳 | **{ctx.author.display_name}** sent **{amount:,}** cowoncy to **{member.display_name}**!")


# --- GAME: Slots (s) - Visual Match ---
@bot.command(name="slots", aliases=["s"])
async def slots(ctx, bet: str):
    bal = get_balance(ctx.author.id)
    bet_amount = parse_bet(bet, bal)
    
    if not bet_amount: return await ctx.send("❌ **Invalid amount!** Enter a number or `all`.")
    if bet_amount > MAX_BET_LIMIT: return await ctx.send(f"❌ **Max bet limit is {MAX_BET_LIMIT:,}!**")
    if bet_amount <= 0 or bet_amount > bal: return await ctx.send("❌ **Insufficient funds!**")

    emojis = ["🍎", "🍒", "🍇", "💎", "🔔", "💖"]
    s1, s2, s3 = random.choice(emojis), random.choice(emojis), random.choice(emojis)
    
    if s1 == s2 == s3:
        multiplier = 5
        winnings = bet_amount * multiplier
        update_balance(ctx.author.id, winnings - bet_amount)
        result_text = f"and **WON {winnings:,}!!** 🎰🔥"
    elif s1 == s2 or s2 == s3 or s1 == s3:
        multiplier = 2
        winnings = bet_amount * multiplier
        update_balance(ctx.author.id, winnings - bet_amount)
        result_text = f"and won **{winnings:,}!** 🎰"
    else:
        update_balance(ctx.author.id, -bet_amount)
        result_text = f"and won nothing... :c"

    embed = discord.Embed(color=0x2b2d31)
    embed.description = f"**___SLOTS___**\n[ {s1} {s2} {s3} ] **{ctx.author.display_name}** bet 💵 {bet_amount:,}\n|               | {result_text}\n|               |"
    await ctx.send(embed=embed)


# --- GAME: INTERACTIVE MINESWEEPER (mine) ---
class MineGridButton(discord.ui.Button):
    def __init__(self, index, view):
        super().__init__(style=discord.ButtonStyle.secondary, label="\u200b", row=index // 4)
        self.index = index
        self.mine_view = view

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.mine_view.ctx.author:
            return await interaction.response.send_message("❌ This is not your game!", ephemeral=True)
        await self.mine_view.process_click(interaction, self)

class MinesGameView(discord.ui.View):
    def __init__(self, ctx, bet_amount, num_mines):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.bet_amount = bet_amount
        self.num_mines = min(max(1, num_mines), 15) # Max 15 mines in a 4x4 grid (16 spots)
        self.multiplier = 1.0
        self.safe_clicks = 0
        
        # 0 = Safe, 1 = Mine
        self.board = [0] * 16
        mine_indices = random.sample(range(16), self.num_mines)
        for i in mine_indices:
            self.board[i] = 1
            
        self.buttons = []
        for i in range(16):
            btn = MineGridButton(i, self)
            self.buttons.append(btn)
            self.add_item(btn)
            
        # Cash Out Button placed on the 5th Row
        self.cashout_btn = discord.ui.Button(style=discord.ButtonStyle.success, label="Cash Out", row=4)
        self.cashout_btn.callback = self.cashout_callback
        self.add_item(self.cashout_btn)
        
        self.embed = discord.Embed(color=0x2b2d31)
        self.update_embed_text()

    def update_embed_text(self):
        next_mult = self.multiplier + (self.num_mines * 0.08)
        self.embed.description = f"**Bet:** {self.bet_amount:,}   **Mines:** {self.num_mines}\n" \
                                 f"**Current:** {self.multiplier:.2f}x\n" \
                                 f"**Next:** {next_mult:.2f}x\n"

    async def process_click(self, interaction: discord.Interaction, button: MineGridButton):
        idx = button.index
        is_mine = self.board[idx] == 1
        
        if is_mine:
            # Player hit a mine - Game Over
            update_balance(self.ctx.author.id, -self.bet_amount)
            self.embed.title = f"💥 {self.ctx.author.display_name} touched a mine!"
            self.embed.color = 0xff0000
            
            # Reveal Board
            for i, btn in enumerate(self.buttons):
                btn.disabled = True
                if self.board[i] == 1:
                    btn.emoji = "💥" if i == idx else "💣"
                    btn.style = discord.ButtonStyle.danger
                else:
                    btn.emoji = "💎"
                    btn.style = discord.ButtonStyle.secondary
            self.cashout_btn.disabled = True
            
            self.embed.description = f"~~**Bet:** {self.bet_amount:,}   **Mines:** {self.num_mines}~~\n" \
                                     f"~~**Cash Out:** {int(self.bet_amount * self.multiplier):,} ({self.multiplier:.2f}x)~~\n"
            await interaction.response.edit_message(embed=self.embed, view=self)
            self.stop()
            
        else:
            # Player clicked a safe spot
            self.safe_clicks += 1
            self.multiplier += (self.num_mines * 0.08)
            
            button.disabled = True
            button.emoji = "💎"
            button.style = discord.ButtonStyle.success
            
            self.update_embed_text()
            
            # Auto win if all safe spots are cleared
            if self.safe_clicks == (16 - self.num_mines):
                await self.do_cashout(interaction, auto=True)
            else:
                await interaction.response.edit_message(embed=self.embed, view=self)

    async def cashout_callback(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("❌ This is not your game!", ephemeral=True)
        if self.safe_clicks == 0:
            return await interaction.response.send_message("You must click at least one spot before cashing out!", ephemeral=True)
        await self.do_cashout(interaction)

    async def do_cashout(self, interaction, auto=False):
        winnings = int(self.bet_amount * self.multiplier)
        update_balance(self.ctx.author.id, winnings - self.bet_amount)
        
        self.embed.title = f"💎 {self.ctx.author.display_name} cashed out!"
        self.embed.color = 0x00ff00
        
        for i, btn in enumerate(self.buttons):
            btn.disabled = True
            if self.board[i] == 1 and not btn.emoji:
                btn.emoji = "💣"
                btn.style = discord.ButtonStyle.danger
                
        self.cashout_btn.disabled = True
        self.embed.description = f"**Bet:** {self.bet_amount:,}   **Mines:** {self.num_mines}\n" \
                                 f"**Winnings:** {winnings:,} ({self.multiplier:.2f}x)\n"
                                 
        await interaction.response.edit_message(embed=self.embed, view=self)
        self.stop()

@bot.command(name="mine", aliases=["mines"])
async def mine(ctx, bet: str, num_mines: int = 1):
    bal = get_balance(ctx.author.id)
    bet_amount = parse_bet(bet, bal)
    
    if not bet_amount: return await ctx.send("❌ **Invalid amount!** Enter a number or `all`.")
    if bet_amount > MAX_BET_LIMIT: return await ctx.send(f"❌ **Max bet limit is {MAX_BET_LIMIT:,}!**")
    if bet_amount <= 0 or bet_amount > bal: return await ctx.send("❌ **Insufficient funds!**")
    
    # Send Interactive Game
    view = MinesGameView(ctx, bet_amount, num_mines)
    await ctx.send(embed=view.embed, view=view)


# --- GAME: Coinflip (cf) ---
@bot.command(name="coinflip", aliases=["cf"])
async def coinflip(ctx, bet: str, choice: str = "heads"):
    bal = get_balance(ctx.author.id)
    bet_amount = parse_bet(bet, bal)
    
    if not bet_amount: return await ctx.send("❌ **Invalid amount!**")
    if bet_amount > MAX_BET_LIMIT: return await ctx.send(f"❌ **Max bet limit is {MAX_BET_LIMIT:,}!**")
    if bet_amount <= 0 or bet_amount > bal: return await ctx.send("❌ **Insufficient funds!**")
    if choice.lower() not in ["heads", "tails", "h", "t"]: return await ctx.send("❌ **Please choose heads or tails!**")

    choice_full = "heads" if choice.lower() in ["heads", "h"] else "tails"
    result = random.choice(["heads", "tails"])
    
    msg = await ctx.send(f"**{ctx.author.display_name}** spent 💵 **{bet_amount:,}** and chose **{choice_full}**\nThe coin spins... 🪙")
    await asyncio.sleep(2)
    
    if choice_full == result:
        update_balance(ctx.author.id, bet_amount)
        await msg.edit(content=f"**{ctx.author.display_name}** spent 💵 **{bet_amount:,}** and chose **{choice_full}**\nThe coin spins... 🪙 and you **WON {bet_amount * 2:,}!** 🎉")
    else:
        update_balance(ctx.author.id, -bet_amount)
        await msg.edit(content=f"**{ctx.author.display_name}** spent 💵 **{bet_amount:,}** and chose **{choice_full}**\nThe coin spins... 🪙 and you **lost it all... :c**")


# --- Scrims Qualifiers Command ---
@bot.command(name="qualify")
@commands.has_permissions(manage_roles=True)
async def qualify(ctx, team_name: str, role: discord.Role, *members: discord.Member):
    if not members: return await ctx.send("❌ **Please mention at least one player!**")
        
    mentions = " ".join([m.mention for m in members])
    for m in members:
        try: await m.add_roles(role)
        except discord.Forbidden: return await ctx.send("❌ **Bot lacks permission to assign this role!**")
            
    embed = discord.Embed(title="🏆 ARISE QUALIFIERS — RESULTS", color=0x00ff00)
    embed.description = f"**GROUP:** G501 | **DATE:** Custom\n" \
                        f"-------------------------\n" \
                        f"🌟 **QUALIFIED TEAMS**\n" \
                        f"1.  ✓ **{team_name}** —\n{mentions}\n\n" \
                        f"Congratulations to all the qualified teams.!!"
    embed.set_footer(text=f"Verified by {ctx.author.display_name} • ARISE QUALIFIERS")
    
    await ctx.send(embed=embed)


# --- Run the Bot ---
token = os.environ.get("DISCORD_TOKEN")
if token: bot.run(token)
else: print("❌ ERROR: DISCORD_TOKEN environment variable is not set!")
