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

### 4. Установить зависимости Python
```bash
uv sync
```

### 5. Установить ffmpeg
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
```

## ▶️ Запуск
#### Запуск Yandex Telemost bot'a:
```bash
python telemost_run.py
```

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

