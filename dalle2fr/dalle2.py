import asyncio
import aiohttp
import requests
import json
from datetime import datetime
import scrape
from PIL import Image
import uuid
import io
import hashlib
import numpy as np
import os


with open("keys.json", "r") as keys_file:
    KEYS = json.load(keys_file)


async def request_images(prompt: str, api_key: str):
    # Create generation task
    task_response = requests.post(
        "https://labs.openai.com/api/labs/tasks",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json={
            "task_type": "text2im",
            "prompt": {"caption": prompt, "batch_size": 4},
        },
    )
    task_response.raise_for_status()
    task_data = task_response.json()
    task_id = task_data["id"]

    print(f"Created task with ID '{task_id}'")

    # Poll the task until the generation is complete
    num_500_errors = 0
    while True:
        print("Querying for task...")
        task_query_response = requests.get(
            f"https://labs.openai.com/api/labs/tasks/{task_id}",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        # check if response is a 500 level error
        if task_query_response.status_code >= 500:
            num_500_errors += 1
            if num_500_errors > 3:
                raise Exception(
                    f"Failed to get task with ID '{task_id}' after 5 500 level errors"
                )
            print(f"{num_500_errors}/5 500 error, trying again...")
            continue
        task_query_response.raise_for_status()
        task_query_data = task_query_response.json()

        if task_query_data["status"] == "succeeded":
            break

        await asyncio.sleep(1)

    image_urls = [
        item["generation"]["image_path"]
        for item in task_query_data["generations"]["data"]
    ]
    return image_urls


def store_new_key(api_key: str):
    global KEYS
    KEYS = {
        "DALLE_API_KEY": api_key,
        "LAST_SCRAPE": str(datetime.now()),
        "SCRAPE_COUNT": KEYS["SCRAPE_COUNT"] + 1,
    }
    with open("keys.json", "w") as keys_file:
        json.dump(KEYS, keys_file)


async def get_image(url: str, session: aiohttp.ClientSession):
    response = await session.get(url=url)
    content = await response.read()
    image = io.BytesIO(content)
    return Image.open(image)


async def get_images(urls: list[str]):
    async with aiohttp.ClientSession() as session:
        return await asyncio.gather(*[get_image(url, session) for url in urls])


def save_images(images: list[Image.Image], prompt: str):
    prompt_hash = hashlib.md5(prompt.encode("utf-8")).hexdigest()
    image_paths = []
    os.mkdir(f"images/{prompt_hash}")
    for image in images:
        filename = f"{uuid.uuid4()}.webp"
        image_path = f"{prompt_hash}/{filename}"
        image_paths.append(image_path)
        image.save(f"images/{image_path}")

    with open(f"images/{prompt_hash}/meta.json", "w") as metadata_file:
        json.dump({"prompt": prompt}, metadata_file)

    return image_paths


def get_cached(prompt_hash: str):
    image_paths = []
    for file in os.scandir(f"images/{prompt_hash}"):
        if file.name != "meta.json":
            image_paths.append(f"{prompt_hash}/{file.name}")
    num_images = 4
    index_picks = np.random.choice(len(image_paths), num_images, replace=False)
    picked = np.array(image_paths)[index_picks]
    return picked.tolist()


async def generate(prompt: str):
    try:
        image_urls = await request_images(prompt, KEYS["DALLE_API_KEY"])
    except requests.HTTPError as error:
        print(
            f"Failed DALL·E 2 request with {KEYS}, scraping new key and trying once more; error: {error}"
        )
        api_key = await scrape.scrape_api_key()
        store_new_key(api_key)
        print(f"trying again with {KEYS}")
        image_urls = await request_images(prompt, KEYS["DALLE_API_KEY"])
    images = await get_images(image_urls)
    return save_images(images, prompt)
