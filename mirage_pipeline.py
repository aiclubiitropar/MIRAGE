import gc
from dotenv import load_dotenv
import json
import os

import torch
from huggingface_hub import login

load_dotenv()  # Load environment variables from .env file

# Authenticate with Hugging Face
try:
    login(token=os.getenv("HUGGINGFACE_TOKEN"))
    print("✅ Successfully logged in to Hugging Face")
except Exception as e:
    print(f"⚠️ Hugging Face login failed: {e}")
    print("💡 You may need to run 'huggingface-cli login' in terminal first")


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

    def parse_multiple_instructions(self, prompt):
        system_prompt = """You are a JSON instruction extractor for image editing.

    Your job is to convert a natural language instruction into one or more strict JSON objects.

    Only extract what the user *explicitly* says. DO NOT add your own assumptions or hallucinate any object.

    Valid actions:
    - "remove" — when the user wants something deleted
    - "replace" — when something is changed into something else

    Output Format:
    Each line should be a valid JSON object like:
    {"action": "remove", "object": "<thing>", "target": null}
    {"action": "replace", "object": "<old>", "target": "<new>"}

    If the instruction says:
    - "replace the car with a bus" → {"action":"replace","object":"car","target":"bus"}
    - "remove the dog and replace tree with lamp" →
        {"action":"remove","object":"dog","target":null}
        {"action":"replace","object":"tree","target":"lamp"}

    🚫 DO NOT return anything that was not mentioned in the instruction.

    Only return JSONs. No text or explanation.
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
        import numpy as np
        from PIL import Image
        import cv2
        from gradio_client import Client, handle_file
        import time
        import random
        
        print(f"📤 Sending image to Gradio client for mask generation with prompt: {object_prompt}")
        
        # List of alternative SAM2 endpoints to try
        sam2_endpoints = [
            "wondervictor/evf-sam2",
            "SkalskiP/florence-sam2",
            "merve/mask-sam2",
            # Add more alternatives as available
        ]
        
        for attempt, endpoint in enumerate(sam2_endpoints):
            try:
                print(f"🔌 Attempting connection to: {endpoint} (attempt {attempt + 1})")
                client = Client(endpoint)
                
                result_path = client.predict(
                    image_np=handle_file(image_path),
                    prompt=object_prompt,
                    semantic_type=False,
                    api_name="/inference_image"
                )
                print(f"📥 Successfully received mask result from {endpoint}: {result_path}")
                break
                
            except Exception as e:
                error_msg = str(e).lower()
                print(f"❌ Error with {endpoint}: {str(e)}")
                
                if "quota" in error_msg or "gpu" in error_msg:
                    print(f"⏳ GPU quota exceeded for {endpoint}")
                    if attempt < len(sam2_endpoints) - 1:
                        # wait_time = random.randint(10, 30)
                        wait_time = 1
                        print(f"⏱️ Waiting {wait_time} seconds before trying next endpoint...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print("❌ All endpoints exhausted. Using fallback method...")
                        return self._create_fallback_mask(image_path, object_prompt)
                
                elif attempt < len(sam2_endpoints) - 1:
                    print(f"🔄 Trying next endpoint...")
                    continue
                else:
                    print("❌ All endpoints failed. Using fallback method...")
                    return self._create_fallback_mask(image_path, object_prompt)
        
        vis_image = Image.open(result_path).convert("RGB")
        np_img = np.array(vis_image)
        hsv = cv2.cvtColor(np_img, cv2.COLOR_RGB2HSV)
        lower = np.array([100, 50, 50])
        upper = np.array([140, 255, 255])
        mask = cv2.inRange(hsv, lower, upper)
        print(f"🎨 Generated mask with shape: {mask.shape}")
        return Image.fromarray(mask)

    def enhance_prompt(self, raw_prompt):
        system = """You are a prompt enhancer for the Stable Diffusion XL inpainting model.
    Improve the input prompt to include rich, descriptive details while preserving the original meaning.
    Make the style fit well with high-resolution, photo-realistic SDXL outputs. Emphasize lighting, texture, and setting.

    Examples:
    - "replace dog with cat" → "replace a golden retriever dog with a fluffy tabby cat sitting on the same grass patch, in high resolution"
    - "remove man" → "remove the standing man in the background, seamlessly blending with the environment"
    """
        response = self.llm.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": raw_prompt}
            ],
            temperature=0.6,
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

    def inpaint_with_mask(self, image, mask, prompt="background", use_refiner=True, num_rounds=1, refine_each_round=True):
        from diffusers import StableDiffusionXLInpaintPipeline, StableDiffusionXLImg2ImgPipeline
        from huggingface_hub import login

        load_dotenv()  # Load environment variables from .env file

        # Authenticate with Hugging Face
        try:
            login(token=os.getenv("HUGGINGFACE_TOKEN"))
            print("✅ Successfully logged in to Hugging Face")
        except Exception as e:
            print(f"⚠️ Hugging Face login failed: {e}")
            print("💡 You may need to run 'huggingface-cli login' in terminal first")

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

        # Multi-round strategy for improved quality
        result = image
        strength_values = [0.9, 0.7, 0.5, 0.4, 0.3]  # Decreasing strength for each round
        
        for round_num in range(num_rounds):
            strength = strength_values[min(round_num, len(strength_values) - 1)]
            print(f"🎨 Starting round {round_num + 1} of {num_rounds} inpainting (strength: {strength})...")
            result = pipe(prompt=prompt, image=result, mask_image=mask, strength=strength).images[0]
            
            # Optional refinement after each round
            if refine_each_round and use_refiner:
                print(f"✨ Applying refiner after round {round_num + 1}...")
                refiner = StableDiffusionXLImg2ImgPipeline.from_pretrained(
                    "stabilityai/stable-diffusion-xl-refiner-1.0",
                    torch_dtype=torch.float16,
                    variant="fp16"
                ).to("cuda")
                
                result = refiner(prompt=prompt, image=result).images[0]
                
                del refiner
                torch.cuda.empty_cache()
                gc.collect()

        # Free up memory
        del pipe
        torch.cuda.empty_cache()
        gc.collect()

        # Final refinement (if not refining each round)
        if use_refiner and not refine_each_round:
            print("✨ Applying final refiner for quality enhancement...")
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
    
    
    def run_prompt_edit(self, image_path, user_prompt, num_rounds=3, refine_each_round=False):
        from PIL import Image
        print(f"📂 Loading image from path: {image_path}")
        original_image = Image.open(image_path).convert("RGB")

        # 🪄 Step 1: Enhance user instruction
        improved_prompt = self.enhance_prompt(user_prompt)
        print(f"✨ Enhanced Prompt: {improved_prompt}")

        # 🧠 Step 2: Parse enhanced prompt
        instructions = self.parse_multiple_instructions(improved_prompt)
        print(f"🧠 Parsed instructions: {instructions}")

        # Debugging: Log the instructions list
        print(f"🔍 Instructions received: {instructions}")

        if not instructions or not isinstance(instructions, list):
            print("❌ No valid instructions found or instructions are malformed!")
            return original_image

        # Process the first instruction (you can modify this to handle multiple)
        instr = instructions[0]
        action, obj, tgt = instr["action"], instr["object"], instr.get("target")
        print(f"🧠 Processing: action={action}, object={obj}, target={tgt}")
        
        mask = self.get_mask_from_gradio(image_path, obj)
        inpaint_prompt = tgt if action == "replace" else "background"
        print(f"🎯 Inpainting with prompt: {inpaint_prompt} (rounds: {num_rounds}, refine_each_round: {refine_each_round})")
        
        result = self.inpaint_with_mask(original_image, mask, inpaint_prompt, num_rounds=num_rounds, refine_each_round=refine_each_round)
        
        # TODO: Handle multiple instructions if needed
        if len(instructions) > 1:
            print(f"ℹ️ Note: Found {len(instructions)} instructions, but only processed the first one")
            print(f"🔄 Remaining instructions: {instructions[1:]}")
        
        return result
