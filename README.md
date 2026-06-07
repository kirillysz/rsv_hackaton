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
bash whisper.cpp/models/download-ggml-model.sh small
```

### 4. Установить зависимости Python
```bash
pip install -r requirements.txt
```
