import shutil

def find_ffmpeg() -> str:
    found = shutil.which("ffmpeg")
    if found:
        return found

    patterns = [
        r"C:\Users\*\AppData\Local\Microsoft\WinGet\Packages\**\ffmpeg.exe",
        r"C:\ProgramData\Microsoft\WinGet\Packages\**\ffmpeg.exe",
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
    ]

    for p in patterns:
        import glob
        c = glob.glob(p, recursive=True)
        if c:
            return c[0]

    raise RuntimeError("ffmpeg не найден")