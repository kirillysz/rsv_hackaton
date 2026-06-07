import asyncio
from app.utils.recorder_service import RecorderService

async def main(url):
    service = RecorderService()
    file = await service.record(url)

    print("DONE:", file)


if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else input("Введите url: ")
    asyncio.run(main(url))