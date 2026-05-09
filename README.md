# Homework Notifier Bot

Telegram bot that monitors Yandex.Practicum homework statuses and sends instant notifications.  
Also provides an Excel report of all homework submissions.

## Features

- 🔔 Real‑time homework status notifications
- 📊 Full homework report in `.xlsx` format
- 🔐 Secure token storage (SQLite)
- ⚙️ Enable/disable notifications per user
- 🛡️ Works only in private chats for security
- 📝 Detailed logging to file and console

## Tech Stack

- Python 3.14+
- [aiogram](https://docs.aiogram.dev/) – Telegram Bot API framework
- [aiosqlite](https://github.com/omnilib/aiosqlite) – async SQLite
- [httpx](https://www.python-httpx.org/) – async HTTP client
- [pandas](https://pandas.pydata.org/) + [openpyxl](https://openpyxl.readthedocs.io/) – Excel reports
- [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) – configuration management
- [make](https://www.gnu.org/software/make/manual/make.html) - commands execution
- [uv](https://docs.astral.sh/uv/) - package management

## Installation

### Clone the repository

```bash
git clone https://github.com/yourusername/hw-notifier.git
cd hw-notifier
```

### Install dependencies

Recommended: use `uv`

```bash
make req
```

### Create a `.env` file** in the project root

```bash
TOKEN=your_telegram_bot_token_here
```

Get the token from [@BotFather](https://t.me/BotFather).

## Running the Bot

```bash
make run
```

The bot will:

- Create the SQLite database and tables
- Start polling Yandex.Practicum every 30 seconds
- Send notifications to registered users

## Usage

Start a private chat with the bot and use the buttons:

- **Register using Yandex OAuth** – obtain a token from [Yandex OAuth](https://oauth.yandex.ru/authorize?response_type=token&client_id=1d0b9dd4d652455a9eb710d450ff456a) and send it to the bot.
- **Notify on homework updates** – enable notifications.
- **Stop notifications** – disable notifications.
- **Full report** – generate and download an Excel file with all homework items.
- **Help** – shows the main menu.

## How It Works

1. User registers with a Yandex.Practicum OAuth token.
2. The bot periodically calls the Practicum API (`/api/user_api/homework_statuses/`) for each active user.
3. When a new homework status is found, the bot sends a message with the update.
4. Users can request a complete `.xlsx` report at any time.

## Development

### Linting & Type Checking

Install optional lint dependencies:

```bash
make req-dev
```

Then run:

```bash
make lint
make lint-fix  # apply autofixes where possible
```

## Notes

- The bot only works in **private chats** (security requirement).
- Tokens are stored as plain text in the database – treat the database file as sensitive.
- Logs are written to `logs/` directory with timestamps.

## License

This project is for educational purposes. No explicit license is provided.
