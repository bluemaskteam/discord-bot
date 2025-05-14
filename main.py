import discord
from discord.ext import commands
import openai
import json
import os
from datetime import datetime

# إعدادات البوت
CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "owner_id": "1326282398299586611",  # أضف أيدي المالك هنا
    "allowed_users": [],
    "user_limits": {}
}

# تحميل أو إنشاء ملف الإعدادات
def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        return DEFAULT_CONFIG
    else:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

# تحميل الإعدادات
config = load_config()

# إعداد البوت
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# إعداد OpenAI (استبدل بمفتاح API الخاص بك)
openai.api_key = "your-openai-api-key"

class ImageGeneration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = config

    def is_owner(self, user_id):
        return str(user_id) == self.config["owner_id"]

    def is_allowed(self, user_id):
        return str(user_id) in self.config["allowed_users"] or self.is_owner(user_id)

    def get_user_limit(self, user_id):
        if self.is_allowed(user_id):
            return float('inf')  # لا يوجد حد للمستخدمين المسموح لهم
        return self.config["user_limits"].get(str(user_id), 5)  # الحد الافتراضي هو 5

    def update_user_limit(self, user_id, count):
        if not self.is_allowed(user_id):
            self.config["user_limits"][str(user_id)] = self.get_user_limit(user_id) - count
            save_config(self.config)

    @commands.command(name="generate", help="إنشاء صورة باستخدام الذكاء الاصطناعي. الاستخدام: !generate وصف الصورة")
    async def generate_image(self, ctx, *, prompt: str):
        user_id = str(ctx.author.id)
        remaining = self.get_user_limit(user_id)

        if remaining <= 0:
            await ctx.send(f"لقد استنفدت عدد المحاولات المسموح بها ({self.get_user_limit(user_id)}). اتصل بالمالك للحصول على المزيد.")
            return

        try:
            await ctx.send("جاري إنشاء الصورة... قد يستغرق الأمر بضع لحظات ⏳")

            # استدعاء OpenAI API لإنشاء الصورة
            response = openai.Image.create(
                prompt=prompt,
                n=1,
                size="1024x1024"
            )

            image_url = response['data'][0]['url']
            
            # إنشاء embed لعرض الصورة
            embed = discord.Embed(
                title="الصورة المطلوبة",
                description=prompt,
                color=discord.Color.blue()
            )
            embed.set_image(url=image_url)
            embed.set_footer(text=f"طلب من قبل: {ctx.author.display_name}")
            
            await ctx.send(embed=embed)
            
            # تحديث عدد المحاولات المتبقية
            self.update_user_limit(user_id, 1)
            
            if not self.is_allowed(user_id):
                await ctx.send(f"تبقى لديك {self.get_user_limit(user_id)} محاولات.")

        except Exception as e:
            await ctx.send(f"حدث خطأ أثناء إنشاء الصورة: {str(e)}")

    @commands.command(name="adduser", help="إضافة مستخدم إلى قائمة المسموح لهم (للمالك فقط)")
    @commands.has_permissions(administrator=True)
    async def add_allowed_user(self, ctx, user: discord.User):
        if not self.is_owner(str(ctx.author.id)):
            await ctx.send("ليس لديك صلاحية تنفيذ هذا الأمر.")
            return

        user_id = str(user.id)
        if user_id not in self.config["allowed_users"]:
            self.config["allowed_users"].append(user_id)
            save_config(self.config)
            await ctx.send(f"تمت إضافة {user.display_name} إلى قائمة المسموح لهم.")
        else:
            await ctx.send(f"{user.display_name} موجود بالفعل في القائمة.")

    @commands.command(name="removeuser", help="إزالة مستخدم من قائمة المسموح لهم (للمالك فقط)")
    @commands.has_permissions(administrator=True)
    async def remove_allowed_user(self, ctx, user: discord.User):
        if not self.is_owner(str(ctx.author.id)):
            await ctx.send("ليس لديك صلاحية تنفيذ هذا الأمر.")
            return

        user_id = str(user.id)
        if user_id in self.config["allowed_users"]:
            self.config["allowed_users"].remove(user_id)
            save_config(self.config)
            await ctx.send(f"تمت إزالة {user.display_name} من قائمة المسموح لهم.")
        else:
            await ctx.send(f"{user.display_name} غير موجود في القائمة.")

    @commands.command(name="resetlimits", help="إعادة تعيين حدود جميع المستخدمين (للمالك فقط)")
    @commands.has_permissions(administrator=True)
    async def reset_limits(self, ctx):
        if not self.is_owner(str(ctx.author.id)):
            await ctx.send("ليس لديك صلاحية تنفيذ هذا الأمر.")
            return

        self.config["user_limits"] = {}
        save_config(self.config)
        await ctx.send("تم إعادة تعيين حدود جميع المستخدمين.")

    @commands.command(name="checklimit", help="التحقق من عدد المحاولات المتبقية")
    async def check_limit(self, ctx):
        user_id = str(ctx.author.id)
        remaining = self.get_user_limit(user_id)
        
        if self.is_allowed(user_id):
            await ctx.send("لديك صلاحية إنشاء عدد غير محدود من الصور.")
        else:
            await ctx.send(f"تبقى لديك {remaining} محاولات لإنشاء الصور.")

# إعداد الأحداث
@bot.event
async def on_ready():
    await bot.add_cog(ImageGeneration(bot))
    print(f'تم تسجيل الدخول كـ {bot.user}')

# تشغيل البوت
if __name__ == "__main__":
    # تأكد من تعيين أيدي المالك في ملف الإعدادات
    if not config["owner_id"]:
        print("يرجى تعيين أيدي المالك في ملف config.json قبل تشغيل البوت.")
    else:
        bot.run("your-discord-bot-token")  # استبدل ب token البوت الخاص بك
