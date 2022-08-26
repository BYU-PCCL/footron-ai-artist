from fastapi import FastAPI, Response, responses
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
import random
import stable_diffusion
import io

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

with open("prompts.json") as prompts_file:
    auto_prompts = json.load(prompts_file)


@app.get("/random-prompt", response_class=responses.PlainTextResponse)
def random_prompt():
    return random.choice(auto_prompts)


def image_to_byte_array(image):
    imgByteArr = io.BytesIO()
    image.save(imgByteArr, format="webp")
    imgByteArr = imgByteArr.getvalue()
    return imgByteArr


@app.get("/generate/{prompt}")
async def generate_image(prompt: str):
    print("generating image for", prompt)
    image = image_to_byte_array(await stable_diffusion.generate(prompt))
    return Response(content=image, media_type="image/webp")


if __name__ == "__main__":
    print("DALL·E 2 router running on http://localhost:32553")
    uvicorn.run("server:app", host="0.0.0.0", port=32553)
