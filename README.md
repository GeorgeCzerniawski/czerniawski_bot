# czerniawski_bot

Telegram-бот, предоставляющий информацию о погоде, курсах валют, криптовалют, таблице Премьер-лиги и последних футбольных новостях.

## Установка

1. Клонируйте репозиторий:

   ```bash
   git clone https://github.com/GeorgeCzerniawski/czerniawski_bot.git
   cd czerniawski_bot

2.Установите зависимости:

    
    pip install -r requirements.txt

3.Создайте файл .env и добавьте в него ваш токен Telegram-бота:

   
   TG_TOKEN=your_telegram_bot_token

4.Запустите бота:

   
  python czerniawski_bot.py

5.Команды:

   ```bash
  /start — Приветствие и информация о боте.
  /help — Список доступных команд.
  /weather <город> — Погода в указанном городе.
  /rate — Курсы популярных валют.
  /crypto — Курсы популярных криптовалют.
  /premier — Таблица Премьер-лиги.
  /football_news — Последние футбольные новости.
