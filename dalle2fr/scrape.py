from playwright.async_api import CDPSession, Page, async_playwright
import asyncio


async def query_objects(cdp_session: CDPSession):
    # Use Runtime.evaluate to get object id for Object.prototype
    object_prototype_id = await cdp_session.send(
        "Runtime.evaluate",
        {
            "expression": "Object.prototype",
        },
    )
    object_id = object_prototype_id["result"]["objectId"]
    objects = await cdp_session.send(
        "Runtime.queryObjects", {"prototypeObjectId": object_id}
    )
    return objects


async def query_api_key_until_found(page: Page):
    client = await page.context.new_cdp_session(page)
    objects = []
    while len(objects) == 0:
        print("Querying API key...")
        await asyncio.sleep(1)
        objects_handle = await query_objects(client)
        objects = (
            await client.send(
                "Runtime.callFunctionOn",
                {
                    "functionDeclaration": """
                objects => objects
                    .map(obj => {
                        try {
                            return Object.values(obj).filter(obj => typeof obj === "string" && obj.startsWith("sess-"))
                        } catch (e) {}
                        return ""
                    })
                    .filter(obj => obj && obj.length > 0)
                    .reduce((acc, obj) => {
                        return acc.concat(obj)
                    }, [])
                """,
                    "arguments": [{"objectId": objects_handle["objects"]["objectId"]}],
                    "objectId": objects_handle["objects"]["objectId"],
                    "returnByValue": True,
                },
            )
        )["result"]["value"]
    return objects[0]


async def scrape_api_key():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        # cdp_session = await page.context.new_cdp_session(page)
        await page.goto("about:blank")
        await page.goto("https://labs.openai.com/auth/login")
        await page.wait_for_selector("#username")
        await page.type("#username", "wingated@cs.byu.edu")
        await page.wait_for_selector('button[type="submit"]')
        await asyncio.sleep(1)
        submit_button = await page.query_selector('button[type="submit"]')
        rect = await page.evaluate(
            """
            header => {
                const { top, left, bottom, right } = header.getBoundingClientRect()
                return { top, left, bottom, right }
            }
            """,
            submit_button,
        )
        # Move mouse to center of rect
        await page.mouse.move(
            rect["left"] + (rect["right"] - rect["left"]) / 2,
            rect["top"] + (rect["bottom"] - rect["top"]) / 2,
        )
        # Click mouse
        await page.mouse.down()
        await page.mouse.up()
        await page.wait_for_selector("#password")
        await page.type("#password", "D4ll3!!!")
        submit_button = await page.query_selector('button[type="submit"]')
        rect = await page.evaluate(
            """
            header => {
                const { top, left, bottom, right } = header.getBoundingClientRect()
                return { top, left, bottom, right }
            }
            """,
            submit_button,
        )
        # Move mouse to center of rect
        await page.mouse.move(
            rect["left"] + (rect["right"] - rect["left"]) / 2,
            rect["top"] + (rect["bottom"] - rect["top"]) / 2,
        )
        # Click mouse
        await page.mouse.down()
        await page.mouse.up()

        return await query_api_key_until_found(page)
