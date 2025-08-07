from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
from dotenv import load_dotenv
load_dotenv()
from mirage_pipeline import MiragePipeline
from PIL import Image
import tempfile
import logging
import traceback
import time

app = FastAPI()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Error logging middleware
@app.middleware("http")
async def error_logging_middleware(request: Request, call_next):
    start_time = time.time()
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(f"Request: {request.method} {request.url} - Status: {response.status_code} - Time: {process_time:.4f}s")
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"Request: {request.method} {request.url} - Error: {str(e)} - Time: {process_time:.4f}s")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "detail": str(e)}
        )

# Allow CORS for all origins (adjust as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set your GROQ API key here or use env var
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "API KEY")  # Replace with your key
pipeline = MiragePipeline(groq_api_key=GROQ_API_KEY)

@app.post("/edit-image/")
async def edit_image(
    image: UploadFile = File(...),
    prompt: str = Form(...)
):
    if not image or not prompt:
        raise HTTPException(status_code=422, detail="Image file and prompt are required.")

    # Save uploaded image to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_img:
        shutil.copyfileobj(image.file, temp_img)
        temp_img_path = temp_img.name

    try:
        # Run MIRAGE pipeline
        logger.info(f"Processing image edit request with prompt: {prompt[:100]}...")
        result_img = pipeline.run_prompt_edit(temp_img_path, prompt)
        # Save result to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as out_img:
            result_img.save(out_img.name)
            result_path = out_img.name
        logger.info("Image edit completed successfully")
        return FileResponse(result_path, media_type="image/png", filename="edited_image.png")
    except Exception as e:
        logger.error(f"Error processing image edit: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        os.remove(temp_img_path)

@app.get("/")
def root():
    return {"message": "MIRAGE FastAPI backend is running."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8017, log_level="info")
