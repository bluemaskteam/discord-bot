import discord
from discord.ext import commands
from googleapiclient.discovery import build
import aiohttp
from typing import List, Dict

# إعداد البوت
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# مفاتيح API
GOOGLE_API_KEY = "AIzaSyBTMxbCz30FGJPYoXAmjjwpUEHUKM4yxCs"
CSE_ID = "f1200524064c54b08"
DISCORD_TOKEN = "MTM3MjMxNTk1MDI1NDI2NDMyMA.Gcbiw3.QPJ4vVHRqM8JFaGxPlIn7wyS7xDMv-slm8XGKc"  # تأكد من إبقاء التوكن سريًا
YOUTUBE_API_KEY = "AIzaSyACclABa9OG8C2jB8hM8RCfqYLT7YoMJfg"

# -------------------- Image Search -------------------- #
class ImageSearchPaginator(discord.ui.View):
    def __init__(self, search_results: List[Dict], query: str):
        super().__init__(timeout=60)
        self.search_results = search_results
        self.query = query
        self.current_page = 0
        self.max_pages = len(search_results)
        self.message = None

    async def update_embed(self):
        result = self.search_results[self.current_page]
        title = result.get("title", "لا يوجد عنوان")
        link = result.get("link", "")
        image_url = result.get("link", "")

        embed = discord.Embed(
            title=title,
            url=link,
            description=f"النتيجة {self.current_page + 1} من {self.max_pages}",
            color=discord.Color.blurple()
        )
        embed.set_image(url=image_url)
        embed.set_footer(text=f"بحث عن: {self.query}")

        if self.message:
            await self.message.edit(embed=embed, view=self)

    @discord.ui.button(label="السابق", style=discord.ButtonStyle.primary, disabled=True)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        self.next_page.disabled = False
        if self.current_page == 0:
            button.disabled = True
        await interaction.response.defer()
        await self.update_embed()

    @discord.ui.button(label="التالي", style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        self.previous_button.disabled = False
        if self.current_page == self.max_pages - 1:
            button.disabled = True
        await interaction.response.defer()
        await self.update_embed()


@bot.command(name="image", help="Search Google Images for any topic")
async def image(ctx: commands.Context, *, query: str):
    try:
        service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
        res = service.cse().list(
            q=query,
            cx=CSE_ID,
            searchType="image",
            num=10
        ).execute()
        items = res.get('items', [])

        if not items:
            await ctx.send("لم يتم العثور على صور.")
            return

        paginator = ImageSearchPaginator(items, query)
        msg = await ctx.send("جارٍ جلب نتائج الصور...", view=paginator)
        paginator.message = msg
        await paginator.update_embed()

    except Exception as e:
        await ctx.send(f"حدث خطأ: {str(e)}")

# -------------------- Define -------------------- #
@bot.command(name="define", help="Get the definition of a word")
async def define(ctx, *, word: str):
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                await ctx.send(f"لم يتم العثور على تعريف للكلمة '{word}'.")
                return
            data = await response.json()

    definitions = data[0].get("meanings", [])
    if not definitions:
        await ctx.send("لم يتم العثور على تعريفات.")
        return

    embed = discord.Embed(title=f"تعريف كلمة {word}", color=discord.Color.green())
    for meaning in definitions:
        part_of_speech = meaning.get("partOfSpeech", "")
        defs = meaning.get("definitions", [])
        if defs:
            definition = defs[0].get("definition", "")
            embed.add_field(name=part_of_speech, value=definition, inline=False)

    await ctx.send(embed=embed)

# -------------------- YouTube Search -------------------- #
@bot.command(name="youtube", help="Search for YouTube tutorials")
async def youtube(ctx, *, query: str):
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=5&q={query}&key={YOUTUBE_API_KEY}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()

    items = data.get("items", [])
    if not items:
        await ctx.send("لم يتم العثور على نتائج على يوتيوب.")
        return

    embed = discord.Embed(title=f"نتائج يوتيوب لـ: {query}", color=discord.Color.red())
    for item in items:
        title = item['snippet']['title']
        video_id = item['id'].get('videoId')
        if video_id:
            url = f"https://www.youtube.com/watch?v={video_id}"
            embed.add_field(name=title, value=url, inline=False)

    await ctx.send(embed=embed)

# -------------------- Research Search -------------------- #
@bot.command(name="research", help="Search for research or articles")
async def research(ctx: commands.Context, *, query: str):
    try:
        service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
        res = service.cse().list(
            q=query,
            cx=CSE_ID,
            num=10,
            siteSearch="scholar.google.com"
        ).execute()
        items = res.get('items', [])

        if not items:
            await ctx.send("لم يتم العثور على أبحاث أو مقالات.")
            return

        embed = discord.Embed(title=f"نتائج البحث عن: {query}", color=discord.Color.dark_gold())
        for item in items:
            title = item.get("title", "لا يوجد عنوان")
            link = item.get("link", "")
            embed.add_field(name=title, value=link, inline=False)

        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"حدث خطأ: {str(e)}")

# -------------------- Quote Command -------------------- #
@bot.command(name="quote", help="Get a random inspirational quote")
async def quote(ctx):
    url = "https://api.quotable.io/random"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()

    content = data["content"]
    author = data["author"]
    embed = discord.Embed(description=f"\"{content}\"", color=discord.Color.purple())
    embed.set_footer(text=f"— {author}")
    await ctx.send(embed=embed)

# -------------------- Joke Command -------------------- #
@bot.command(name="joke", help="Get a random joke")
async def joke(ctx):
        url = "https://official-joke-api.appspot.com/jokes/random"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()

        setup = data["setup"]
        punchline = data["punchline"]
        # ترجمة بسيطة للنكتة (يمكن تطويرها لاحقاً)
        joke_ar = f"نكتة:\n{setup} 😂\n||{punchline}||"
        await ctx.send(joke_ar)

# -------------------- Fact Command -------------------- #
@bot.command(name="fact", help="Get a random fun fact")
async def fact(ctx):
    url = "https://uselessfacts.jsph.pl/random.json?language=en"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()

    fact_text = data['text']

    # حاولنا ترجمة النص تلقائياً (إن لم يكن لديك ترجمة يمكنك استخدام مكتبة ترجمة أو API)
    # هنا ببساطة نضيف مقدمة عربية
    fact_ar = f"🧠 هل تعلم؟ {fact_text}"
    await ctx.send(fact_ar)
# -------------------- Help Command -------------------- #
@bot.command(name="h", help="Show all bot commands")
async def help_command(ctx):
    help_text = """
**🤖 Available Commands:**
`!image [query]` - 🔍 ابحث عن الصور
`!define [word]` - 📖 احصل على تعريف كلمة
`!youtube [topic]` - 🎥 ابحث عن شروحات على يوتيوب
`!research [topic]` - 📚 ابحث عن أبحاث أو مقالات
`!quote` - 💬 احصل على اقتباس ملهم عشوائي
`!joke` - 😂 احصل على نكتة عشوائية
`!fact` - 🧠 احصل على معلومة عشوائية ممتعة
`!h` - ℹ️ عرض قائمة الأوامر
    """
    await ctx.send(help_text)

# -------------------- Ready Event -------------------- #
@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user.name} ({bot.user.id})')

# -------------------- Run Bot -------------------- #
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
