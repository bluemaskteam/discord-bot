import requests
import schedule
import time
from datetime import datetime
import json

# إعدادات الويبهوك
WEBHOOK_URL = "https://discord.com/api/webhooks/1376361948228227125/mzAP9UpqVnEn6hWZY3q5uikBkf7OPmk5z1ty2EugrUB-UaBF25Qm3dnyhgk9EMSaMxyl"

# مصادر الألعاب المجانية (API)
FREE_GAMES_API = {
    "Epic Games":
    "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions",
    "Steam": "https://store.steampowered.com/api/featuredcategories",
    "GOG": "https://www.gog.com/games/ajax/filtered?mediaType=game&price=free"
}


def get_free_games():
    free_games = []

    try:
        # Epic Games
        epic_response = requests.get(FREE_GAMES_API["Epic Games"])
        if epic_response.status_code == 200:
            epic_data = epic_response.json()
            for game in epic_data['data']['Catalog']['searchStore'][
                    'elements']:
                if game.get('promotions'
                            ) and game['promotions']['promotionalOffers']:
                    free_games.append({
                        "title":
                        game['title'],
                        "platform":
                        "Epic Games",
                        "rating":
                        None,  # Epic لا توفر تقييمات مباشرة
                        "url":
                        f"https://www.epicgames.com/store/en-US/p/{game['productSlug']}",
                        "image":
                        game['keyImages'][0]['url']
                        if game['keyImages'] else None
                    })

    except Exception as e:
        print(f"Error fetching Epic Games: {e}")

    try:
        # Steam (مثال مبسط)
        steam_response = requests.get(FREE_GAMES_API["Steam"])
        if steam_response.status_code == 200:
            steam_data = steam_response.json()
            # هنا تحتاج إلى معالجة بيانات Steam حسب هيكل API
            pass

    except Exception as e:
        print(f"Error fetching Steam games: {e}")

    return free_games


def send_discord_notification(game):
    # إنشاء رسالة Discord غنية
    embed = {
        "title":
        f"🎮 {game['title']} - مجانية الآن!",
        "description":
        f"اللعبة {game['title']} متاحة الآن مجاناً على {game['platform']}",
        "color":
        0x00ff00,
        "fields": [{
            "name": "المنصة",
            "value": game['platform'],
            "inline": True
        }, {
            "name": "التقييم",
            "value": game['rating'] if game['rating'] else "غير متوفر",
            "inline": True
        }],
        "image": {
            "url": game['image']
        },
        "timestamp":
        datetime.utcnow().isoformat(),
        "url":
        game['url']
    }

    data = {
        "content": f"||@everyone||\n📢 لعبة جديدة مجانية! {game['title']}",
        "embeds": [embed]
    }

    headers = {"Content-Type": "application/json"}

    response = requests.post(WEBHOOK_URL,
                             data=json.dumps(data),
                             headers=headers)
    if response.status_code != 204:
        print(f"Failed to send notification: {response.status_code}")


def check_and_notify():
    print("Checking for free games...")
    games = get_free_games()
    for game in games:
        send_discord_notification(game)
    print(f"Sent notifications for {len(games)} games")


def run_scheduler():
    # جدولة الفحص كل ساعة
    schedule.every().hour.do(check_and_notify)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    print("Starting free games notifier bot...")
    check_and_notify()  # تشغيل فحص أولي عند البدء
    run_scheduler()
