import asyncio
from app.utils.recorder_service import RecorderService
from app.transcription.whisper import transcribe_whisper_cpp

from app.utils.yougile.service import YougileClient
from app.utils.yougile.executor import YouGileExecutor

from app.llm.service import LLMService

from config import settings

async def run_tm(url):
    service = RecorderService()
    file = await service.record(url)

    print("DONE:", file)
    text = transcribe_whisper_cpp(audio_path=file)
    print(f"text = {text}")

    yc = YougileClient(token=settings.YOUGILE_TOKEN)
    llm = LLMService(model="qwen2.5:3b")
    executor = YouGileExecutor(client=yc)

    result = await llm.chat(messages=[
        {
            "role": "user",
            "content": text
        }
    ])

    parsed = result.get("parsed")
    exec_result = await executor.execute(parsed)

    print("\n===== EXECUTOR RESULT =====\n")
    print(exec_result)

if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else input("Введите url: ")
    asyncio.run(run_tm(url))
