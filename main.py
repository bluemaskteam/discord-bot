import discord
from discord.ext import commands
import openai
import asyncio

# Bot tokens
DISCORD_TOKEN = 'MTM3MjMxNTk1MDI1NDI2NDMyMA.Ge7Egy.QVoQfy8wpxLJopX1-M0glltPO56s6sBKMIKQzU'
OPENAI_API_KEY = 'sk-proj-tGgoytguFyz_5sTsgOMJcBcICTBhuPe2EAYCMS-TQtDE52LymHGDEX2gWBqsg_2CliQywDvzDT3BlbkFJYcv4AqsDp_INcpxFaAMg2hOJ1NUnmrm27k5g__C41BSfvuJoZ1XxRqctfAMS8fCabo5y3uW6EA'

# Bot setup
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# OpenAI setup
openai.api_key = OPENAI_API_KEY

# Command to create server by type
@bot.command()
async def create(ctx, *, server_type: str):
    await ctx.send(f"🔧 Creating server of type: **{server_type}**...")

    # Use AI to generate server settings
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an assistant that creates Discord server setups."},
            {"role": "user", "content": f"Create professional Discord server settings for type: {server_type}. Should include decorated channels, roles, and permissions."}
        ]
    )

    settings = response['choices'][0]['message']['content']

    await ctx.send("📄 AI-generated settings:\n" + "```" + settings[:1900] + "```")

    # Create basic channels as example:
    guild = ctx.guild

    # Text channels
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=True)
    }

    await guild.create_text_channel("📜│rules", overwrites=overwrites)
    await guild.create_text_channel("💬│general-chat", overwrites=overwrites)
    await guild.create_text_channel("🛒│order-your-shop", overwrites=overwrites)

    # Roles
    await guild.create_role(name="👑 | Admin", colour=discord.Colour.red())
    await guild.create_role(name="🛍️ | Shop Owner", colour=discord.Colour.green())
    await guild.create_role(name="👤 | Member", colour=discord.Colour.blue())

    await ctx.send("✅ Server created successfully!")

# Run the bot
bot.run(DISCORD_TOKEN)
