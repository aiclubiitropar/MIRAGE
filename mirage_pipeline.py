import gc
from dotenv import load_dotenv
import json
import os
import torch
import cv2
import numpy as np
import tempfile
from PIL import Image
from gradio_client import Client, handle_file
from huggingface_hub import login

load_dotenv()  # Load environment variables from .env file

class MiragePipeline:
    """
    Main pipeline for object removal/replacement in images using Stable Diffusion XL and Gradio mask extraction.
    """
    def __init__(self, groq_api_key=os.getenv("GROQ_API_KEY"), device="cuda"):
        import torch
        from groq import Groq
        self.groq = Groq(api_key=groq_api_key)
        self.llm = self.groq.chat.completions
        self.device = device
        self.torch = torch
        try:
            login(token=os.getenv("HUGGINGFACE_TOKEN"))
            print("✅ Successfully logged in to Hugging Face")
        except Exception as e:
            print(f"⚠️ Hugging Face login failed: {e}")
            print("💡 You may need to run 'huggingface-cli login' in terminal first")


    def parse_multiple_instructions(self, prompt):
        system_prompt = """You are a strict JSON instruction extractor for image editing.

You must extract instructions from the user's prompt and convert them into JSON.

Each instruction must include:
- "action": either "remove" or "replace"
- "object": the original thing being removed or replaced (even if descriptive)
- "target": the new thing (only for "replace"; null for "remove")

✅ Object and target can be long, descriptive phrases.
✅ Handle enhanced prompts like "replace the majestic falana tiger with a cool majestic dog" as:
{"action":"replace","object":"majestic falana tiger","target":"cool majestic dog"}

❌ Do not break object/target into individual words.
❌ Do not hallucinate or invent instructions.

🎯 Output Format (one instruction per line):
{"action": "remove", "object": "<thing>", "target": null}
{"action": "replace", "object": "<thing>", "target": "<thing>"}

Only output JSONs. No explanations. No extra text.
"""

        response = self.llm.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_completion_tokens=512,
            top_p=1.0,
            stream=False,
        )

        raw = response.choices[0].message.content.strip()
        print("🔎 LLM RAW:", raw)

        # Parse each line as JSON (ignore non-JSON junk if hallucinated)
        return [json.loads(line.strip()) for line in raw.splitlines() if line.strip().startswith('{')]

    def get_mask_from_gradio(self, image_path, object_prompt):
        print(f"📤 Sending image to Gradio client for mask generation with prompt: {object_prompt}")
        
        try:
            client = Client("wondervictor/evf-sam2")
            result_path = client.predict(
                image_np=handle_file(image_path),
                prompt=object_prompt,
                semantic_type=False,
                api_name="/inference_image"
            )
            vis_image = Image.open(result_path).convert("RGB")
            np_img = np.array(vis_image)

            # Extract mask based on highlight color (blue hues)
            hsv = cv2.cvtColor(np_img, cv2.COLOR_RGB2HSV)
            lower = np.array([100, 50, 50])
            upper = np.array([140, 255, 255])
            mask = cv2.inRange(hsv, lower, upper)

            return Image.fromarray(mask)
        except Exception as e:
            print(f"⚠️ Gradio mask generation failed: {e}")
            print("💡 Tip: Consider setting up your own SAM2 instance or using API tokens for better reliability")
            return self._create_fallback_mask(image_path, object_prompt)
        print(f"🎨 Generated mask with shape: {mask.shape}")
        return Image.fromarray(mask)

    def enhance_prompt(self, raw_prompt):
        system = """You are a prompt enhancer for the Stable Diffusion XL inpainting model.
Improve the input prompt to include rich, descriptive details while preserving the original meaning.
Make the style fit well with high-resolution, photo-realistic SDXL outputs. Emphasize lighting, texture, and setting.The tokens should be not exceeded so like I dont want it to exceed maximum tokens , so keep tokens less than 200 tokens like this is the maxiumum limit so try to keep it under 100 o 150 tokens so not too many words. The limit is only 77 tokens so keep it less than 75 tokens , maybe 50 tokens


Examples:
- "replace dog with cat" → "replace a golden retriever dog with a fluffy tabby cat sitting on the same grass patch"
- "remove man" → "remove the standing man in the background, seamlessly blending with the environment"
"""
        response = self.llm.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": raw_prompt}
            ],
            temperature=0.5,
            max_completion_tokens=256
        )
        return response.choices[0].message.content.strip()

    def _create_fallback_mask(self, image_path, object_prompt):
        """
        Fallback mask creation when Gradio services are unavailable.
        Creates a simple center-based mask as a last resort.
        """
        from PIL import Image, ImageDraw
        import numpy as np
        
        print(f"🚨 Creating fallback mask for: {object_prompt}")
        print("⚠️ Note: This is a simple fallback and may not be as accurate")
        
        # Load image to get dimensions
        image = Image.open(image_path).convert("RGB")
        width, height = image.size
        
        # Create a simple center-based circular mask
        mask = Image.new("L", (width, height), 0)
        draw = ImageDraw.Draw(mask)
        
        # Create a circular mask in the center (you can modify this logic)
        center_x, center_y = width // 2, height // 2
        radius = min(width, height) // 4
        
        draw.ellipse([
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius
        ], fill=255)
        
        print(f"🎭 Created fallback circular mask: {width}x{height}, radius: {radius}")
        print("💡 Tip: Consider setting up your own SAM2 instance or using API tokens for better reliability")
        
        return mask

    def inpaint_with_mask(self, image, mask, prompt="background", use_refiner=True):
        from diffusers import StableDiffusionXLInpaintPipeline, StableDiffusionXLImg2ImgPipeline

        # Resize image and mask if needed
        MAX_RES = 1024
        if max(image.size) > MAX_RES:
            image.thumbnail((MAX_RES, MAX_RES))
        mask = mask.resize(image.size).convert("L")

        # Load Inpainting pipeline
        pipe = StableDiffusionXLInpaintPipeline.from_pretrained(
            "diffusers/stable-diffusion-xl-1.0-inpainting-0.1",
            torch_dtype=torch.float16,
            variant="fp16"
        ).to("cuda")

        result = pipe(prompt=prompt, image=image, mask_image=mask).images[0]

        # Free up memory
        del pipe
        torch.cuda.empty_cache()
        gc.collect()

        if use_refiner:
            # Load Refiner only if needed
            refiner = StableDiffusionXLImg2ImgPipeline.from_pretrained(
                "stabilityai/stable-diffusion-xl-refiner-1.0",
                torch_dtype=torch.float16,
                variant="fp16"
            ).to("cuda")

            result = refiner(prompt=prompt, image=result).images[0]

            del refiner
            torch.cuda.empty_cache()
            gc.collect()

        return result


    def run_prompt_edit(self, image_path, user_prompt):
        # 🪄 Step 1: Enhance user instruction
        improved_prompt = self.enhance_prompt(user_prompt)
        print(f"✨ Enhanced Prompt: {improved_prompt}")

        # 🧠 Step 2: Parse enhanced prompt
        instructions = self.parse_multiple_instructions(improved_prompt)
        print(f"🧠 Parsed: {instructions}")

        image = Image.open(image_path).convert("RGB")

        for step, instr in enumerate(instructions):
            action, obj, tgt = instr["action"], instr["object"], instr.get("target")
            print(f"🔁 Step {step+1}: {action} {obj} {'→ ' + tgt if tgt else ''}")

            mask = self.get_mask_from_gradio(image_path, obj)
            inpaint_prompt = tgt if action == "replace" else "background"

            # 1st Inpainting
            image = self.inpaint_with_mask(image, mask, prompt=inpaint_prompt, use_refiner=False)

            # 1st Refining
            from diffusers import StableDiffusionXLImg2ImgPipeline
            refiner = StableDiffusionXLImg2ImgPipeline.from_pretrained(
                "stabilityai/stable-diffusion-xl-refiner-1.0",
                torch_dtype=torch.float16,
                variant="fp16"
            ).to("cuda")
            image = refiner(prompt=inpaint_prompt, image=image).images[0]
            del refiner
            torch.cuda.empty_cache()
            gc.collect()

            # 2nd Inpainting (same mask reused)
            image = self.inpaint_with_mask(image, mask, prompt=inpaint_prompt, use_refiner=True)

            # 2nd Refining
            refiner = StableDiffusionXLImg2ImgPipeline.from_pretrained(
                "stabilityai/stable-diffusion-xl-refiner-1.0",
                torch_dtype=torch.float16,
                variant="fp16"
            ).to("cuda")
            image = refiner(prompt=inpaint_prompt, image=image).images[0]
            del refiner
            torch.cuda.empty_cache()
            gc.collect()

            # Save intermediate image
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                image.save(tmp.name)
                image_path = tmp.name

        return image
