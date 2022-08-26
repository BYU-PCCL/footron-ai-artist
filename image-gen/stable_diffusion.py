"""
https://github.com/huggingface/diffusers/releases/tag/v0.2.4

apt update
apt install git

pip install diffusers==0.2.4 transformers scipy
huggingface-cli login

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
"""

import torch
from torch import autocast
from diffusers import StableDiffusionPipeline, LMSDiscreteScheduler

# this will substitute the default PNDM scheduler for K-LMS
lms = LMSDiscreteScheduler(
    beta_start=0.00085,
    beta_end=0.012,
    beta_schedule="scaled_linear"
)

pipe = StableDiffusionPipeline.from_pretrained(
    "CompVis/stable-diffusion-v1-4",
    scheduler=lms,
    use_auth_token=True,
    # revision="fp16",  # uncomment this for the FP32 version
    # torch_dtype=torch.float16 # uncomment this for the FP32 version
).to("cuda")

async def generate(prompt: str):
    with autocast("cuda"):
        for _ in range(2):
            result = pipe(prompt)
            if not result["nsfw_content_detected"][0]:
                return result["sample"][0]
        # TODO: Return a placeholder image
        return result["sample"][0]
