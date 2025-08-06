from mirage_pipeline import MiragePipeline
from mirage_utils import MirageImageUtils
import os
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

# Example usage for the final pipeline
if __name__ == "__main__":
    # 🔑 Set your GROQ API key here
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # Replace with your key

    # Login to HuggingFace if needed
    from huggingface_hub import login
    login()  # will prompt for your token

    # Get latest image and user prompt
    latest_image_path = MirageImageUtils.get_latest_image("/content/")
    print(f"📸 Using latest image: {latest_image_path}")
    user_prompt = MirageImageUtils.get_user_prompt()

    # Run pipeline
    pipeline = MiragePipeline(groq_api_key=GROQ_API_KEY)
    result = pipeline.run_prompt_edit(latest_image_path, user_prompt)

    # Save and show result
    MirageImageUtils.save_and_show_result(result, output_path="/content/edited_image.png")
