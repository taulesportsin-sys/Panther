import discord
from discord.ext import commands
import os
import random
import asyncio

# --- Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

def get_prefix(bot, message):
    return ['P ', 'p ', 'P', 'p']

bot = commands.Bot(command_prefix=get_prefix, intents=intents, help_command=None)

# --- Constants & Variables ---
OWNER_ID = 1525484718412267662
MAX_BET_LIMIT = 250000
STARTING_BALANCE = 100000
DAILY_REWARD = 15000
OWNER_BALANCE = 100000000000

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
        return int(bet_str)
    except ValueError:
        return None

async def send_error(ctx, message):
    embed = discord.Embed(description=f"❌ **{message}**", color=0xff0000)
    await ctx.send(embed=embed)


# --- Events ---
@bot.event
async def on_ready():
    print(f'✅ {bot.user} is online with ? MINES & NEW GAMES!')
    await bot.change_presence(activity=discord.Game(name="BGMI Scrims | p help"))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        pass # Ignore wrong commands silently or add a pass to prevent spam
    elif isinstance(error, commands.MissingRequiredArgument):
        await send_error(ctx, "Missing arguments! Check `p help` for correct usage.")


# --- Help Command ---
@bot.command(name="help")
async def help_cmd(ctx):
    embed = discord.Embed(title="🤖 Ultimate Bot Commands Menu", color=0x2b2d31, description="Prefix: `p` or `P`")
    embed.add_field(name="💰 Economy", value="`p cash` - Check balance\n`p daily` - Claim daily\n`p give @user [amount]` - Transfer cash", inline=False)
    embed.add_field(name="🎲 Games (Max Bet: 250k)", value="`p mine [amount/all] [mines(1-8)]` - 3x3 Minesweeper\n`p cf [amount/all] [heads/tails]` - Flip a Coin\n`p s [amount/all]` - Spin Slots\n`p dice [amount/all]` - Roll Dice against Bot\n`p rps [amount/all] [r/p/s]` - Rock Paper Scissors", inline=False)
    embed.add_field(name="🏆 Scrims", value="`p qualify \"Team Name\" @Role @P1 @P2` - Qualify team", inline=False)
    await ctx.send(embed=embed)


# --- Economy ---
@bot.command(name="cash", aliases=["bal", "balance"])
async def cash(ctx, member: discord.Member = None):
    member = member or ctx.author
    bal = get_balance(member.id)
    embed = discord.Embed(description=f"💳 | **{member.display_name}**, you currently have **{bal:,}** cowoncy!", color=0x2b2d31)
    await ctx.send(embed=embed)

@bot.command(name="daily")
@commands.cooldown(1, 86400, commands.BucketType.user)
async def daily(ctx):
    update_balance(ctx.author.id, DAILY_REWARD)
    embed = discord.Embed(description=f"💸 | **{ctx.author.display_name}**, you claimed your daily **{DAILY_REWARD:,}** cowoncy!", color=0x00ff00)
    await ctx.send(embed=embed)

@daily.error
async def daily_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await send_error(ctx, f"Please wait **{error.retry_after // 3600:.0f}h** before claiming.")

@bot.command(name="give")
async def give(ctx, member: discord.Member, amount: int):
    if amount <= 0: return await send_error(ctx, "Amount must be > 0!")
    if ctx.author.id != OWNER_ID and get_balance(ctx.author.id) < amount: return await send_error(ctx, "Not enough cash!")
    
    update_balance(ctx.author.id, -amount)
    update_balance(member.id, amount)
    embed = discord.Embed(description=f"💳 | **{ctx.author.display_name}** sent **{amount:,}** cowoncy to **{member.display_name}**!", color=0x00ff00)
    await ctx.send(embed=embed)


# --- GAME: 3x3 MINESWEEPER (With '?' marks) ---
class MineGridButton(discord.ui.Button):
    def __init__(self, index, view):
        # Start with a Question Mark
        super().__init__(style=discord.ButtonStyle.secondary, label="?", row=index // 3)
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
        self.num_mines = min(max(1, num_mines), 8)
        self.multiplier = 1.0
        self.safe_clicks = 0
        
        self.board = [0] * 9
        mine_indices = random.sample(range(9), self.num_mines)
        for i in mine_indices:
            self.board[i] = 1
            
        self.buttons = []
        for i in range(9):
            btn = MineGridButton(i, self)
            self.buttons.append(btn)
            self.add_item(btn)
            
        self.cashout_btn = discord.ui.Button(style=discord.ButtonStyle.success, label="Cash Out", row=3)
        self.cashout_btn.callback = self.cashout_callback
        self.add_item(self.cashout_btn)
        
        self.embed = discord.Embed(color=0x3498db) # Blue color for start
        self.update_embed_text(playing=True)

    def update_embed_text(self, playing=True, boom=False, cashed_out=False):
        current_payout = int(self.bet_amount * self.multiplier) if self.safe_clicks > 0 else 0
        next_mult = self.multiplier + (self.num_mines * 0.15) if self.safe_clicks > 0 else 1.0 + (self.num_mines * 0.15)
        next_payout = int(self.bet_amount * next_mult)
        
        if playing:
            self.embed.color = 0x3498db # Blue Line
            if self.safe_clicks == 0:
                self.embed.description = f"💣 **{self.ctx.author.display_name} started a mines game.**\n\n"
            else:
                self.embed.description = f"💣 **{self.ctx.author.display_name} is playing mines.**\n\n"
                
            self.embed.description += f"**Bet:** {self.bet_amount:,}   **Mines:** {self.num_mines}\n" \
                                      f"**Cash Out:** {current_payout:,} ({self.multiplier if self.safe_clicks > 0 else 0:.2f}x)\n" \
                                      f"**Next:** {next_payout:,} ({next_mult:.2f}x)"
        elif boom:
            self.embed.color = 0xff0000 # Red Line
            self.embed.description = f"💥 **{self.ctx.author.display_name} touched a mine!**\n\n" \
                                     f"~~**Bet:** {self.bet_amount:,}   **Mines:** {self.num_mines}~~\n" \
                                     f"~~**Cash Out:** {current_payout:,} ({self.multiplier:.2f}x)~~"
        elif cashed_out:
            self.embed.color = 0x00ff00 # Green Line
            self.embed.description = f"💎 **| {self.ctx.author.display_name} cashed out!**\n\n" \
                                     f"**Bet:** {self.bet_amount:,}   **Mines:** {self.num_mines}\n" \
                                     f"**Winnings:** {current_payout:,} ({self.multiplier:.2f}x)"

    async def process_click(self, interaction: discord.Interaction, button: MineGridButton):
        idx = button.index
        is_mine = self.board[idx] == 1
        
        if is_mine:
            update_balance(self.ctx.author.id, -self.bet_amount)
            for i, btn in enumerate(self.buttons):
                btn.disabled = True
                btn.label = None # Remove the '?' mark
                if self.board[i] == 1:
                    btn.emoji = "💥" if i == idx else "💣"
                    btn.style = discord.ButtonStyle.danger
                else:
                    btn.emoji = "💎"
                    btn.style = discord.ButtonStyle.secondary
            self.cashout_btn.disabled = True
            
            self.update_embed_text(playing=False, boom=True)
            await interaction.response.edit_message(embed=self.embed, view=self)
            self.stop()
        else:
            if self.safe_clicks == 0:
                self.multiplier = 1.0 + (self.num_mines * 0.15)
            else:
                self.multiplier += (self.num_mines * 0.15)
                
            self.safe_clicks += 1
            button.disabled = True
            button.label = None # Remove the '?' mark
            button.emoji = "💎"
            button.style = discord.ButtonStyle.success
            
            self.update_embed_text(playing=True)
            
            if self.safe_clicks == (9 - self.num_mines):
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
        
        for i, btn in enumerate(self.buttons):
            btn.disabled = True
            if self.board[i] == 1 and not btn.emoji:
                btn.label = None
                btn.emoji = "💣"
                btn.style = discord.ButtonStyle.danger
                
        self.cashout_btn.disabled = True
        self.update_embed_text(playing=False, cashed_out=True)
        await interaction.response.edit_message(embed=self.embed, view=self)
        self.stop()

@bot.command(name="mine", aliases=["mines"])
async def mine(ctx, bet: str, num_mines: int = 1):
    bal = get_balance(ctx.author.id)
    bet_amount = parse_bet(bet, bal)
    
    if not bet_amount: return await send_error(ctx, "Invalid amount!")
    if bet_amount > MAX_BET_LIMIT: return await send_error(ctx, f"Max limit is {MAX_BET_LIMIT:,}!")
    if bet_amount <= 0 or bet_amount > bal: return await send_error(ctx, "Insufficient funds!")
    if num_mines < 1 or num_mines > 8: return await send_error(ctx, "Mines must be between 1 and 8!")
    
    view = MinesGameView(ctx, bet_amount, num_mines)
    await ctx.send(embed=view.embed, view=view)


# --- GAME: SLOTS ---
@bot.command(name="slots", aliases=["s"])
async def slots(ctx, bet: str):
    bal = get_balance(ctx.author.id)
    bet_amount = parse_bet(bet, bal)
    
    if not bet_amount or bet_amount > MAX_BET_LIMIT or bet_amount <= 0 or bet_amount > bal: 
        return await send_error(ctx, "Invalid amount or insufficient funds!")

    update_balance(ctx.author.id, -bet_amount)
    emojis = ["🍎", "🍒", "🍇", "💎", "🔔", "💖", "🥔", "🍌", "🍉"]
    
    embed = discord.Embed(color=0x2b2d31)
    embed.description = f"**___SLOTS___**\n[ 🔄 🔄 🔄 ] **{ctx.author.display_name}** bet 💵 {bet_amount:,}\n|               | Spinning...\n|               |"
    msg = await ctx.send(embed=embed)

    for _ in range(3): # Reduced slightly for better speed
        e1, e2, e3 = random.choice(emojis), random.choice(emojis), random.choice(emojis)
        embed.description = f"**___SLOTS___**\n[ {e1} {e2} {e3} ] **{ctx.author.display_name}** bet 💵 {bet_amount:,}\n|               | Spinning...\n|               |"
        await msg.edit(embed=embed)
        await asyncio.sleep(1)

    s1, s2, s3 = random.choice(emojis), random.choice(emojis), random.choice(emojis)
    winnings = 0
    
    if s1 == s2 == s3:
        winnings = bet_amount * 5
        result_text = f"and **WON {winnings:,}!!** 🎰🔥"
        embed.color = 0x00ff00 
    elif s1 == s2 or s2 == s3 or s1 == s3:
        winnings = bet_amount * 2
        result_text = f"and won **{winnings:,}!** 🎰"
        embed.color = 0x00ff00
    else:
        result_text = f"and won nothing... :c"
        embed.color = 0xff0000

    if winnings > 0: update_balance(ctx.author.id, winnings)
    embed.description = f"**___SLOTS___**\n[ {s1} {s2} {s3} ] **{ctx.author.display_name}** bet 💵 {bet_amount:,}\n|               | {result_text}\n|               |"
    await msg.edit(embed=embed)


# --- GAME: Coinflip (cf) ---
@bot.command(name="coinflip", aliases=["cf"])
async def coinflip(ctx, bet: str, choice: str = "heads"):
    bal = get_balance(ctx.author.id)
    bet_amount = parse_bet(bet, bal)
    
    if not bet_amount or bet_amount > MAX_BET_LIMIT or bet_amount <= 0 or bet_amount > bal: 
        return await send_error(ctx, "Invalid amount or insufficient funds!")
    if choice.lower() not in ["heads", "tails", "h", "t"]: 
        return await send_error(ctx, "Please choose heads or tails!")

    choice_full = "heads" if choice.lower() in ["heads", "h"] else "tails"
    result = random.choice(["heads", "tails"])
    
    embed = discord.Embed(description=f"**{ctx.author.display_name}** spent 💵 **{bet_amount:,}** and chose **{choice_full}**\nThe coin spins... 🪙", color=0x2b2d31)
    msg = await ctx.send(embed=embed)
    await asyncio.sleep(2)
    
    if choice_full == result:
        update_balance(ctx.author.id, bet_amount)
        embed.color = 0x00ff00
        embed.description = f"**{ctx.author.display_name}** spent 💵 **{bet_amount:,}** and chose **{choice_full}**\nThe coin spins... 🪙 and you **WON {bet_amount * 2:,}!** 🎉"
    else:
        update_balance(ctx.author.id, -bet_amount)
        embed.color = 0xff0000
        embed.description = f"**{ctx.author.display_name}** spent 💵 **{bet_amount:,}** and chose **{choice_full}**\nThe coin spins... 🪙 and you **lost it all... :c**"
        
    await msg.edit(embed=embed)


# --- NEW GAME: DICE ROLL ---
@bot.command(name="dice", aliases=["roll"])
async def dice(ctx, bet: str):
    bal = get_balance(ctx.author.id)
    bet_amount = parse_bet(bet, bal)
    
    if not bet_amount or bet_amount > MAX_BET_LIMIT or bet_amount <= 0 or bet_amount > bal: 
        return await send_error(ctx, "Invalid amount or insufficient funds!")

    player_roll = random.randint(1, 12)
    bot_roll = random.randint(1, 12)
    
    embed = discord.Embed(title="🎲 Dice Roll", color=0x2b2d31)
    embed.description = f"**{ctx.author.display_name}** rolls the dice... 🎲"
    msg = await ctx.send(embed=embed)
    await asyncio.sleep(1.5)
    
    if player_roll > bot_roll:
        update_balance(ctx.author.id, bet_amount)
        embed.color = 0x00ff00
        embed.description = f"You rolled **{player_roll}** 🎲\nBot rolled **{bot_roll}** 🎲\n\n🎉 You **WON {bet_amount * 2:,}!**"
    elif player_roll < bot_roll:
        update_balance(ctx.author.id, -bet_amount)
        embed.color = 0xff0000
        embed.description = f"You rolled **{player_roll}** 🎲\nBot rolled **{bot_roll}** 🎲\n\n💀 You **lost {bet_amount:,}...**"
    else:
        embed.color = 0xffff00 # Yellow for tie
        embed.description = f"You rolled **{player_roll}** 🎲\nBot rolled **{bot_roll}** 🎲\n\n🤝 It's a **TIE!** You kept your money."
        
    await msg.edit(embed=embed)


# --- NEW GAME: Rock Paper Scissors (RPS) ---
@bot.command(name="rps")
async def rps(ctx, bet: str, choice: str):
    bal = get_balance(ctx.author.id)
    bet_amount = parse_bet(bet, bal)
    
    if not bet_amount or bet_amount > MAX_BET_LIMIT or bet_amount <= 0 or bet_amount > bal: 
        return await send_error(ctx, "Invalid amount or insufficient funds!")
        
    valid_choices = {"r": "rock", "rock": "rock", "p": "paper", "paper": "paper", "s": "scissors", "scissors": "scissors"}
    player_choice = valid_choices.get(choice.lower())
    
    if not player_choice:
        return await send_error(ctx, "Choose Rock (r), Paper (p), or Scissors (s)!")

    bot_choice = random.choice(["rock", "paper", "scissors"])
    emojis = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
    
    embed = discord.Embed(title="✊✋✌️ Rock Paper Scissors", color=0x2b2d31)
    
    if player_choice == bot_choice:
        embed.color = 0xffff00
        embed.description = f"You: {emojis[player_choice]} | Bot: {emojis[bot_choice]}\n\n🤝 It's a **TIE!**"
    elif (player_choice == "rock" and bot_choice == "scissors") or \
         (player_choice == "paper" and bot_choice == "rock") or \
         (player_choice == "scissors" and bot_choice == "paper"):
        update_balance(ctx.author.id, bet_amount)
        embed.color = 0x00ff00
        embed.description = f"You: {emojis[player_choice]} | Bot: {emojis[bot_choice]}\n\n🎉 You **WON {bet_amount * 2:,}!**"
    else:
        update_balance(ctx.author.id, -bet_amount)
        embed.color = 0xff0000
        embed.description = f"You: {emojis[player_choice]} | Bot: {emojis[bot_choice]}\n\n💀 You **lost {bet_amount:,}...**"
        
    await ctx.send(embed=embed)


# --- Scrims Qualifiers Command ---
@bot.command(name="qualify")
@commands.has_permissions(manage_roles=True)
async def qualify(ctx, team_name: str, role: discord.Role, *members: discord.Member):
    if not members: return await send_error(ctx, "Please mention at least one player!")
    mentions = " ".join([m.mention for m in members])
    for m in members:
        try: await m.add_roles(role)
        except discord.Forbidden: return await send_error(ctx, "Bot lacks permission!")
            
    embed = discord.Embed(title="🏆 ARISE QUALIFIERS — RESULTS", color=0x00ff00)
    embed.description = f"**GROUP:** G501 | **DATE:** Custom\n-------------------------\n🌟 **QUALIFIED TEAMS**\n1.  ✓ **{team_name}** —\n{mentions}\n\nCongratulations!!"
    await ctx.send(embed=embed)

# --- Run ---
token = os.environ.get("DISCORD_TOKEN")
if token: bot.run(token)
else: print("❌ ERROR: DISCORD_TOKEN is missing!")
