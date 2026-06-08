import subprocess, os, re
import tempfile

JUNK_PATTERNS = [
    r"Редактор\s+субтитров[^\n]*",
    r"Корректор[^\n]*",
    r"Субтитры[^\n]*",
    r"Перевод[^\n]*",
    r"Продюсер[^\n]*",
    r"\b[А-ЯЁ]\.[А-ЯЁ][а-яё]+",
    r"\[\s*BLANK_AUDIO\s*\]",
    r"\(.*?шум.*?\)",
    r"\(.*?тишина.*?\)",
]

def clean_transcription(text: str) -> str:
    for pattern in JUNK_PATTERNS:
        text = re.sub(pattern, "", text, flags=re.MULTILINE | re.IGNORECASE)

    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return "\n".join(lines)


def transcribe_whisper_cpp(audio_path: str) -> str:
    base = r"C:\Users\timos\rsv_hackaton\whisper.cpp"
    exe = os.path.join(base, r"build\bin\whisper-cli.exe")
    model = os.path.join(base, r"models\ggml-large-v3-turbo.bin")

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name

    processed_path = tmp_path.replace(".wav", "_clean.wav")

    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-i", audio_path,
        "-af",
        "silenceremove=start_periods=1:start_threshold=-45dB:detection=peak",
        "-ar", "16000",
        "-ac", "1",
        "-c:a", "pcm_s16le",
        processed_path
    ]

    ffmpeg_res = subprocess.run(ffmpeg_cmd, capture_output=True)

    if ffmpeg_res.returncode != 0:
        print("FFMPEG ERROR:", ffmpeg_res.stderr.decode("utf-8", errors="ignore"))

    env = os.environ.copy()
    env["PATH"] = r"C:\msys64\mingw64\bin" + ";" + env["PATH"]

    result = subprocess.run(
        [
            exe,
            "-m", model,
            "-f", processed_path,
            "-l", "ru",
            "--temperature", "0.2",
            "-bs", "5",
            "-np", "1"
        ],
        capture_output=True,
        env=env,
)

    stdout = result.stdout.decode("utf-8", errors="ignore")
    stderr = result.stderr.decode("utf-8", errors="ignore")

    print("STDOUT:\n", stdout)
    print("STDERR:\n", stderr)

    text = stdout.strip()
    if not text:
        text = stderr.strip()

    if result.returncode != 0:
        print(f"[whisper] returncode={result.returncode}")

    os.unlink(tmp_path)
    os.unlink(processed_path)

    return clean_transcription(text)