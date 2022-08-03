from fastapi import FastAPI, responses, Response
from fastapi.middleware.cors import CORSMiddleware
from dalle2 import get_cached, generate
import asyncio
import uvicorn
import json
import os
import hashlib
import random

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

with open("prompts.json") as prompts_file:
    auto_prompts = json.load(prompts_file)
    auto_hash_prompts = {
        hashlib.md5(prompt.encode("utf-8")).hexdigest(): prompt
        for prompt in auto_prompts
    }


@app.get("/random-prompt", response_class=responses.PlainTextResponse)
def get_random_prompt(cache_only: bool = True):
    cached_prompt_hashes = [f.name for f in os.scandir("images")]
    if cache_only:
        prompt_hashes = cached_prompt_hashes
    else:
        prompt_hashes = list(set(cached_prompt_hashes + list(auto_hash_prompts.keys())))
    prompt_hash = random.choice(prompt_hashes)
    if prompt_hash in auto_hash_prompts:
        return auto_hash_prompts[prompt_hash]
    with open(f"images/{prompt_hash}/meta.json") as metadata_file:
        metadata = json.load(metadata_file)
    return metadata["prompt"]


@app.get("/autopilot/{prompt}")
async def get_autopilot_images(prompt: str):
    # print(prompt)
    prompt_hash = hashlib.md5(prompt.encode("utf-8")).hexdigest()
    cached_prompt_hashes = [f.name for f in os.scandir("images")]
    if prompt_hash in cached_prompt_hashes:
        # print("cache hit")
        return {
            "success": True,
            "prompt": prompt,
            "image_paths": get_cached(prompt_hash),
        }
    # print("cache miss")
    try:
        # raise Exception("cache miss")
        return {
            "success": True,
            "prompt": prompt,
            "image_paths": await generate(prompt),
        }
    except Exception:
        fallback_prompt = get_random_prompt(True)
        fallback_hash = hashlib.md5(fallback_prompt.encode("utf-8")).hexdigest()
        return {
            "success": False,
            "prompt": fallback_prompt,
            "image_paths": get_cached(fallback_hash),
        }


@app.get("generate/{prompt}")
async def get_generated(prompt: str):
    try:
        return {
            "success": True,
            "prompt": prompt,
            "image_paths": await generate(prompt),
        }
    except Exception:
        fallback_prompt = get_random_prompt(True)
        fallback_hash = hashlib.md5(fallback_prompt.encode("utf-8")).hexdigest()
        return {
            "success": False,
            "prompt": fallback_prompt,
            "image_paths": get_cached(fallback_hash),
        }


@app.get("/image/{prompt_hash}/{filename}", response_class=responses.FileResponse)
async def get_image(prompt_hash: str, filename: str, response: Response):
    response.headers["content-type"] = "image/webp"
    return f"images/{prompt_hash}/{filename}"


if __name__ == "__main__":
    print("DALL·E 2 router running on http://localhost:32553")
    uvicorn.run("server:app", host="0.0.0.0", port=32553, reload=True, log_level="info")
