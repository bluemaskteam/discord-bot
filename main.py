import os
import discord
from discord.ext import commands
from googleapiclient.discovery import build
from typing import List, Dict

# Initialize bot with intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Google Custom Search setup
GOOGLE_API_KEY = "AIzaSyBTMxbCz30FGJPYoXAmjjwpUEHUKM4yxCs"
CSE_ID = "f1200524064c54b08"
DISCORD_TOKEN = "MTM3MjMxNTk1MDI1NDI2NDMyMA.GZd_w4.Ts-PrqAP_OFRZXRo811lrB5-FNubyMWhSYrP_o"

class SearchPaginator(discord.ui.View):
    def __init__(self, search_results: List[Dict], query: str, start_index: int = 1):
        super().__init__(timeout=60)
        self.search_results = search_results
        self.query = query
        self.current_page = 0
        self.start_index = start_index
        self.max_pages = len(search_results) // 10 + (1 if len(search_results) % 10 else 0)

    async def update_embed(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=f"Google Search Results for: {self.query}",
            description=f"Page {self.current_page + 1}/{self.max_pages}",
            color=discord.Color.blue()
        )

        start_idx = self.current_page * 10
        end_idx = min(start_idx + 10, len(self.search_results))

        for i in range(start_idx, end_idx):
            result = self.search_results[i]
            embed.add_field(
                name=f"{i+1}. {result.get('title', 'No title')}",
                value=f"[{result.get('link', 'No link')}]({result.get('link', '')})\n{result.get('snippet', 'No description')}",
                inline=False
            )

        embed.set_footer(text=f"Results {start_idx + 1}-{end_idx} of {len(self.search_results)}")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary, disabled=True)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        self.next_page.disabled = False
        if self.current_page == 0:
            button.disabled = True
        await self.update_embed(interaction)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        self.previous_button.disabled = False
        if self.current_page == self.max_pages - 1:
            button.disabled = True
        await self.update_embed(interaction)

@bot.command(name="search", help="Search Google for any topic")
async def search(ctx: commands.Context, *, query: str):
    try:
        # Initialize Google Custom Search service
        service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)

        # Perform the search
        res = service.cse().list(
            q=query,
            cx=CSE_ID,
            num=10
        ).execute()

        items = res.get('items', [])

        if not items:
            await ctx.send("No results found.")
            return

        # Create and send the first page of results
        paginator = SearchPaginator(items, query)
        message = await ctx.send("Loading results...", view=paginator)
        interaction = await bot.wait_for("interaction", check=lambda i: i.message.id == message.id)
        await paginator.update_embed(interaction)

    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    print('------')

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
