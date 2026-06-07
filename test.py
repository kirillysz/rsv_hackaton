import subprocess, os

def transcribe_whisper_cpp(audio_path: str):
    base  = r"C:\Users\timos\rsv_hackaton\whisper.cpp"
    exe   = os.path.join(base, r"build\bin\whisper-cli.exe")
    model = os.path.join(base, r"models\ggml-small.bin")

    env = os.environ.copy()
    env["PATH"] = r"C:\msys64\mingw64\bin" + ";" + env["PATH"]

    result = subprocess.run(
        [exe, "-m", model, "-f", audio_path, "-l", "ru", "-nt"],
        capture_output=True,
        env=env
    )

    for enc in ["utf-8", "cp1251", "cp866"]:
        try:
            stdout = result.stdout.decode(enc)
            stderr = result.stderr.decode(enc)
            break
        except Exception as e:
            print(f"[{enc}] failed:", e)

    return stdout

print(transcribe_whisper_cpp(audio_path=r"C:\Users\timos\rsv_hackaton\meeting.wav"))