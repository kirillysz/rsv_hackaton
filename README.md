## Установка

### 1. Клонировать репозиторий
```bash
git clone --recurse-submodules https://github.com/kirillysz/rsv_hackaton
```

### 2. Собрать whisper.cpp
```bash
cd whisper.cpp
cmake -B build && cmake --build build --config Release
```

### 3. Скачать модель
```bash
bash whisper.cpp/models/download-ggml-model.sh large-v3-turbo
```

### 4. Установка uv
macOS / Linux
```bash
curl -Ls https://astral.sh/uv/install.sh | sh
```
Windows (PowerShell)
```bash
irm https://astral.sh/uv/install.ps1 | iex
```

### 5. Установить зависимости Python
```bash
uv sync
```

Если виртуальное окружение ещё не создано:
```bash
uv venv
uv sync
```
### 6. Активировать окружение (если нужно вручную):
macOS / Linux
```bash
source .venv/bin/activate
```
Windows (PowerShell)
```bash
.venv\Scripts\Activate.ps1
```

### 7. Установить ffmpeg
Ubuntu / Debian
```bash
sudo apt update
sudo apt install ffmpeg
```

macOS
```bash
brew install ffmpeg
```

Windows (Chocolatey)
```bash
choco install ffmpeg
```

Или скачать вручную
https://ffmpeg.org/download.html

## ⚙️ Конфигурация
Создать .env файл
```bash
YOUGILE_TOKEN=your_token_here
COLUMN_ID=column_id
BOT_TOKEN=bot_token
FORUM_CHAT_ID=forum_chat_id
FORUM_THREAD_ID=forum_thread_id
FORUM_SYNC_ID=forumn_chat_sync_id
FORUM_SYNC_THREAD_ID=forum_sync_thread_id
```

## ▶️ Запуск
#### Запуск Telegram-бота:
```bash
python run_bot.py
```

### 🔄 Как работает Yandex Telemost bot
1. 🎤 RecorderService записывает встречу
2. ✂️ FFmpeg убирает тишину
3. 🧠 Whisper.cpp делает транскрипцию
4. 🧹 Чистка текста от мусора
5. 🤖 LLM извлекает действия
6. 📌 YouGile создаёт задачи

