# Импорт библиотек
from telegram import Update  # Для работы с обновлениями сообщений Telegram
from telegram.ext import Application, CommandHandler, ContextTypes  # Основные компоненты бота
import requests  # Для HTTP-запросов к API
import time      # Для задержек при retry
import os        # Для работы с переменными окружения
from dotenv import load_dotenv  # Для загрузки токенов из .env
import datetime  # Для работы с датой и временем
import feedparser  # Для парсинга RSS-лент 

# Токены
load_dotenv()  # Загружаем переменные окружения из .env
TG_TOKEN = os.getenv("TG_TOKEN")           # Токен Telegram-бота
WEATHER_TOKEN = os.getenv("WEATHER_TOKEN") # Токен OpenWeatherMap
FOOTBALL_TOKEN = os.getenv("FOOTBALL_TOKEN") # Токен football-data.org (для моей любимой EPL)

# Наличие токенов
if not TG_TOKEN or not WEATHER_TOKEN or not FOOTBALL_TOKEN:
    raise ValueError("Ошибка: не найден один из токенов. Проверь файл .env")

# Категорически вас приветствую
async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    welcome_text = (
        "Привет!\n"
        "Я помогу тебе узнать погоду, курсы валют, криптовалюты и таблицу EPL.\n\n"
        "Команды:\n"
        "/weather <город> — погода\n"
        "/rate — курсы валют\n"
        "/crypto — курсы 10 популярных криптовалют\n"
        "/premier — таблица Премьер-лиги\n"
        "/football_news — последние футбольные новости\n"
        '/help — справочник по командам. Они и так тут приведены, но по тз нужно чтобы была команда хелп (:'
    )
    await update.message.reply_text(welcome_text)

# Погода
def fetch_weather_data(city: str, attempts: int = 3, pause: int = 2):
    """Запрашивает данные о погоде с retry"""
    for i in range(attempts):
        try:
            response = requests.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={"q": city, "appid": WEATHER_TOKEN, "units": "metric", "lang": "ru"},
                timeout=5
            )
            if response.status_code == 200:
                return response.json()  # Успешный ответ
            elif response.status_code == 404:
                return {"error": "Город не найден. Проверьте написание."}
            else:
                return {"error": "Ошибка при обращении к серверу погоды."}
        except requests.RequestException:
            if i < attempts - 1:
                time.sleep(pause)  # Ждём перед повторной попыткой
            else:
                return {"error": "Не удалось подключиться к серверу. Попробуйте позже."}

async def handle_weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /weather"""
    if not context.args:
        await update.message.reply_text("Пожалуйста, укажите город: /weather <название>")
        return
    city = " ".join(context.args)
    data = fetch_weather_data(city)
    if "error" in data:
        await update.message.reply_text(data["error"])
        return

    info = data["main"]  # Основные данные о погоде
    weather = data["weather"][0]  # Описание погоды
    wind = data["wind"]["speed"]  # Скорость ветра
    country = data["sys"].get("country", "")

    msg = (
        f"☁️ Погода в {city}, {country}\n\n"
        f"🌡 Температура: {info['temp']:.1f}°C\n"
        f"🤚 Ощущается как: {info['feels_like']:.1f}°C\n"
        f"💧 Влажность: {info['humidity']}%\n"
        f"🎚 Давление: {info['pressure']} гПа\n"
        f"💨 Ветер: {wind} м/с\n"
        f"📝 Описание: {weather['description'].capitalize()}"
    )
    await update.message.reply_text(msg)

# Валюта
POPULAR = ["RUB", "USD", "EUR", "GBP", "JPY", "CNY"]  # Популярные валюты
CURRENCY_FLAGS = {"RUB":"🇷🇺","USD":"🇺🇸","EUR":"🇪🇺","GBP":"🇬🇧","JPY":"🇯🇵","CNY":"🇨🇳"}

def get_exchange_rates():
    """Получает актуальные курсы валют от ЦБ РФ"""
    url = "https://www.cbr-xml-daily.ru/daily_json.js"
    response = requests.get(url)
    data = response.json()
    rates = {v["CharCode"]: v["Value"]/v["Nominal"] for v in data["Valute"].values()}
    rates["RUB"] = 1.0
    return rates

async def handle_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /rate"""
    rates = get_exchange_rates()
    msg_lines = ["💱 Курсы валют относительно рубля:\n"]
    for cur in POPULAR:
        flag = CURRENCY_FLAGS.get(cur, "")
        msg_lines.append(f"{flag} {cur}: {rates.get(cur,0.0):.4f} ₽")
    await update.message.reply_text("\n".join(msg_lines))

# Фантики
CRYPTO_LIST = [
    ("bitcoin", "₿ Bitcoin"), ("ethereum", "Ξ Ethereum"), ("binancecoin", "🟡 BNB"),
    ("cardano", "🔷 ADA"), ("solana", "🟣 SOL"), ("ripple", "💧 XRP"),
    ("dogecoin", "🐶 DOGE"), ("polkadot", "⚫ DOT"), ("litecoin", "Ł LTC"),
    ("avalanche-2", "🔥 AVAX")
]

async def handle_crypto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /crypto"""
    try:
        ids = ",".join([c[0] for c in CRYPTO_LIST])
        response = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": ids, "vs_currencies": "usd"}, timeout=5
        )
        data = response.json()
        msg_lines = [f"{name}: ${data.get(cid, {}).get('usd', 0.0):.2f}" for cid, name in CRYPTO_LIST]
        msg = "\n".join(msg_lines)
    except Exception:
        msg = "Не удалось получить данные о криптовалюте 😅 Попробуйте позже."
    await update.message.reply_text(msg)

# PREMIER LEAGUE
async def handle_premier(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вывод всей таблицы Премьер-лиги с 💙 у Everton"""
    headers = {"X-Auth-Token": FOOTBALL_TOKEN}  # Заголовки с токеном
    try:
        resp = requests.get(
            "https://api.football-data.org/v4/competitions/PL/standings",
            headers=headers,
            timeout=5
        )
        data = resp.json()
        table = data.get("standings", [])[0].get("table", [])
        msg_lines = ["🏆 Таблица Премьер-лиги:\n"]
        for t in table:
            pos = t["position"]  # Позиция в таблице
            team_name = t["team"]["name"]  # Название команды
            if team_name == "Everton FC":
                team_name += " 💙"  # Я болею за Everton
            points = t["points"]  # Количество очков
            msg_lines.append(f"{pos}. {team_name} — {points} очков")
    except Exception:
        msg_lines = ["Не удалось получить таблицу Премьер-лиги 😅 Попробуйте позже."]
    await update.message.reply_text("\n".join(msg_lines))

# Ну и раз уж у меня футбольный бот, то пусть парсит новости с еспн
async def handle_football_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Выводит топ-5 последних футбольных новостей из RSS ESPN Soccer
    try:
        feed_url = "https://www.espn.com/espn/rss/soccer/news"  # RSS-лента
        feed = feedparser.parse(feed_url)  # Парсим ленту
        msg_lines = ["⚽ Последние футбольные новости:\n"]
        for entry in feed.entries[:5]:  # Берем только 5 новостей
            title = entry.title  # Заголовок
            link = entry.link    # Ссылка
            msg_lines.append(f"• {title}\n{link}")  # Формируем сообщение
    except Exception:
        msg_lines = ["Не удалось получить новости( Попробуйте позже."]
    await update.message.reply_text("\n\n".join(msg_lines))

# хелп
async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Выводит список всех доступных команд бота с кратким описанием
    help_text = (
        "💡 Доступные команды:\n\n"
        "/start — приветствие и краткая информация\n"
        "/help — этот справочник по командам\n"
        "/weather <город> — погода в указанном городе\n"
        "/rate — курсы популярных валют\n"
        "/crypto — курсы 10 популярных криптовалют\n"
        "/premier — таблица Премьер-лиги (Everton всегда на дне)\n"
        "/football_news — топ-5 последних футбольных новостей"
    )
    await update.message.reply_text(help_text)

def main():
    # Приложение бота с токеном
    app = Application.builder().token(TG_TOKEN).build()

    # Обработчики команд
    app.add_handler(CommandHandler("start", handle_start))           # Приветствие
    app.add_handler(CommandHandler("help", handle_help))             # Справка по командам
    app.add_handler(CommandHandler("weather", handle_weather))       # Погода
    app.add_handler(CommandHandler("rate", handle_rate))             # Курсы валют
    app.add_handler(CommandHandler("crypto", handle_crypto))         # Курсы криптовалют
    app.add_handler(CommandHandler("premier", handle_premier))       # Таблица Премьер-лиги
    app.add_handler(CommandHandler("football_news", handle_football_news))  # Новости футбола

    # Сообщение о запуске
    print("Бот запущен! Используйте /start или /help для начала работы.")
    
    # Проверка новых сообщений через polling
    app.run_polling()

if __name__ == "__main__":
    main()
