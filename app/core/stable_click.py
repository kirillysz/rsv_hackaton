async def stable_click(page, name: str, timeout=8000):
    locators = [
        page.get_by_role("button", name=name),
        page.locator(f'button:has-text("{name}")'),
        page.locator(f'[role="button"]:has-text("{name}")'),
    ]

    for loc in locators:
        try:
            await loc.first.wait_for(state="visible", timeout=timeout)
            await loc.first.scroll_into_view_if_needed()

            try:
                await loc.first.click(timeout=2000)
                return True
            except:
                try:
                    await loc.first.click(force=True)
                    return True
                except:
                    await loc.first.evaluate("el => el.click()")
                    return True

        except:
            continue

    return False