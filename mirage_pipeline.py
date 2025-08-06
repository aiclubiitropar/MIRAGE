from dotenv import load_dotenv
import json
import os

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

    def parse_instruction(self, prompt):
        import json
        instruction_prompt = f'''You are an instruction parser.\n\nInstruction: "{prompt}"\n\nOutput JSON:\n{{"action": "remove" or "replace", "object": "<object>", "target": "<new object>" or null}}\n\nExamples:\nremove tiger → {{"action":"remove","object":"tiger","target":null}}\nreplace tiger with lion → {{"action":"replace","object":"tiger","target":"lion"}}\n\nONLY return JSON.'''
        print(f"📝 Sending instruction to LLM: {instruction_prompt}")
        response = self.llm.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": instruction_prompt}],
            temperature=0.0,
            max_completion_tokens=256,
            top_p=1,
            stream=False
        )
        print(f"🔄 LLM Response: {response.choices[0].message.content.strip()}")
        return json.loads(response.choices[0].message.content.strip())

    def get_mask_from_gradio(self, image_path, object_prompt):
        import numpy as np
        from PIL import Image
        import cv2
        from gradio_client import Client, handle_file
        print(f"📤 Sending image to Gradio client for mask generation with prompt: {object_prompt}")
        client = Client("wondervictor/evf-sam2")
        result_path = client.predict(
            image_np=handle_file(image_path),
            prompt=object_prompt,
            semantic_type=False,
            api_name="/inference_image"
        )
        print(f"📥 Received mask result from Gradio client: {result_path}")
        vis_image = Image.open(result_path).convert("RGB")
        np_img = np.array(vis_image)
        hsv = cv2.cvtColor(np_img, cv2.COLOR_RGB2HSV)
        lower = np.array([100, 50, 50])
        upper = np.array([140, 255, 255])
        mask = cv2.inRange(hsv, lower, upper)
        print(f"🎨 Generated mask with shape: {mask.shape}")
        return Image.fromarray(mask)

    def inpaint_with_mask(self, image, mask, prompt="background"):
        """
        Inpaint using the Gradio client (IotaCluster/Inpaint_Refine space).
        """
        from gradio_client import Client, handle_file
        import tempfile
        from PIL import Image
        print(f"🖼️ Starting inpainting with prompt: {prompt}")
        # Save image and mask to temp files
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as img_tmp, \
             tempfile.NamedTemporaryFile(suffix='.png', delete=False) as mask_tmp:
            image.save(img_tmp.name)
            mask.save(mask_tmp.name)
            print(f"📤 Sending image and mask to Gradio client for inpainting")
            client = Client("IotaCluster/Inpaint_Refine")
            result_path = client.predict(
                image=handle_file(img_tmp.name),
                mask=handle_file(mask_tmp.name),
                prompt=prompt,
                api_name="/inpaint_with_mask"
            )
        print(f"📥 Received inpainted result from Gradio client: {result_path}")
        # Load and return the result image
        return Image.open(result_path)

    def run_prompt_edit(self, image_path, user_prompt):
        from PIL import Image
        print(f"📂 Loading image from path: {image_path}")
        original_image = Image.open(image_path).convert("RGB")
        print(f"📝 Parsing user prompt: {user_prompt}")
        instr = self.parse_instruction(user_prompt)
        action, obj, tgt = instr["action"], instr["object"], instr.get("target")
        print(f"🧠 Parsed: action={action}, object={obj}, target={tgt}")
        mask = self.get_mask_from_gradio(image_path, obj)
        inpaint_prompt = tgt if action == "replace" else "background"
        print(f"🎯 Inpainting with prompt: {inpaint_prompt}")
        return self.inpaint_with_mask(original_image, mask, inpaint_prompt)
