import base64
import subprocess
from playwright.async_api import async_playwright

from app.utils.ffmpeg import find_ffmpeg
from app.core.stable_click import stable_click

AUDIO_PATCH_PATH = "app/recorder/audio_patch.js"


class RecorderService:

    async def record(self, url: str, output="meeting.wav"):
        ffmpeg = find_ffmpeg()

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                args=[
                    "--use-fake-ui-for-media-stream",
                    "--autoplay-policy=no-user-gesture-required",
                ]
            )

            ctx = await browser.new_context(permissions=["microphone"])

            # patch audio
            with open(AUDIO_PATCH_PATH, "r", encoding="utf-8") as f:
                await ctx.add_init_script(f.read())

            page = await ctx.new_page()
            await page.goto(url)

            await page.wait_for_timeout(3000)

            await self._join_flow(page)

            print("🟢 recording...")

            await page.wait_for_selector(
                "text=Организатор завершил встречу для всех",
                timeout=0
            )
            audio_b64 = await self._stop_and_get_audio(page)
            webm = output.replace(".wav", ".webm")

            with open(webm, "wb") as f:
                f.write(base64.b64decode(audio_b64))

            result = subprocess.run(
                [ffmpeg, "-y", "-i", webm, "-ar", "48000", "-ac", "1", output],
                capture_output=True,
                text=True
            )

            await browser.close()

            return output

    async def _join_flow(self, page):
        try:
            await page.locator('button:has-text("Продолжить в браузере")').click()
        except:
            pass

        await stable_click(page, "Понятно")
        await stable_click(page, "Понятно")

        try:
            await page.locator(
                'button:has-text("Подключиться"),'
                'button:has-text("Присоединиться")'
            ).click()
        except:
            pass

    async def _stop_and_get_audio(self, page):
        return await page.evaluate("""
            () => new Promise((resolve, reject) => {
                const r = window.__rec;
                if (!r) return reject("no recorder");

                r.onstop = async () => {
                    const blob = new Blob(window.__chunks, {type: "audio/webm"});
                    const buf = await blob.arrayBuffer();
                    const bytes = new Uint8Array(buf);

                    let bin = "";
                    const CHUNK = 8192;

                    for (let i = 0; i < bytes.length; i += CHUNK)
                        bin += String.fromCharCode(...bytes.subarray(i, i + CHUNK));

                    resolve(btoa(bin));
                };

                r.stop();
            })
        """)