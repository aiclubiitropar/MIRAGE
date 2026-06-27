# MIRAGE – AI-Powered Natural Language Image Editing

## Overview

MIRAGE is an AI-powered image editing system that enables users to modify images using simple natural language instructions such as:

* *"Remove the car"*
* *"Replace the tiger with a lion"*

Instead of requiring manual masking or traditional image editing software, MIRAGE combines Large Language Models, vision foundation models, and diffusion models into a unified pipeline that performs semantic image editing automatically.

---

## Features

* 📝 Natural language-based image editing
* 🎯 Automatic object detection and segmentation
* 🖌️ AI-powered object removal and replacement
* ✨ Photorealistic image refinement
* ☁️ Remote GPU inference with client-server architecture
* 🔧 Modular and extensible AI pipeline

---

## Architecture

```
User Image + Text Prompt
            │
            ▼
  Llama 3.1 (Groq API)
  ↓ Parse Instruction
            │
            ▼
 Structured JSON
(Action, Target, Replacement)
            │
            ▼
      EVF-SAM2
 Object Segmentation
            │
            ▼
 Binary Mask Generation
   (OpenCV Processing)
            │
            ▼
 Stable Diffusion XL
      Inpainting
            │
            ▼
 Stable Diffusion XL
       Refiner
            │
            ▼
     Final Edited Image
```

---

## Technology Stack

### AI Models

* Llama 3.1 8B Instant (Groq API)
* EVF-SAM2
* Stable Diffusion XL Inpainting
* Stable Diffusion XL Refiner

### Libraries

* Python
* PyTorch
* Hugging Face Diffusers
* Transformers
* OpenCV
* Pillow
* NumPy
* Gradio Client
* Groq SDK

---

## How It Works

1. The user uploads an image and enters a natural language editing instruction.
2. Llama 3.1 interprets the instruction and converts it into structured JSON.
3. EVF-SAM2 automatically segments the requested object.
4. OpenCV processes the segmentation output into a binary mask.
5. Stable Diffusion XL performs object removal or replacement using the generated mask.
6. SDXL Refiner enhances image quality and removes artifacts.
7. The edited image is returned to the user.

---

## Distributed Deployment

MIRAGE follows a client-server architecture where computationally intensive AI models execute on remote GPU servers. Client applications submit editing requests consisting of an image and text prompt, while the server performs segmentation and diffusion-based inference before returning the edited result. This architecture enables lightweight clients, centralized model management, and scalable multi-user deployment.

---

## Supported Editing Operations

* Object Removal
* Object Replacement

Examples:

* Remove the car
* Remove the person
* Replace the cat with a tiger
* Replace the chair with a sofa

---

## Project Structure

```
MIRAGE/
│
├── Client/
│   ├── Image Upload
│   └── Prompt Interface
│
├── Backend/
│   ├── LLM Instruction Parser
│   ├── EVF-SAM2 Segmentation
│   ├── OpenCV Mask Processing
│   ├── SDXL Inpainting
│   └── SDXL Refiner
│
├── Models/
├── Utilities/
└── Outputs/
```

---

## Future Improvements

* Multi-object editing
* Style transfer
* Background replacement
* Object insertion
* Image expansion (Outpainting)
* Local deployment with optimized inference
* Interactive web application
* Support for additional diffusion models

---

## Domain

**Generative AI • Computer Vision • Natural Language Processing (NLP)**

---

## Authors

Developed as part of an AI image editing project integrating Large Language Models, vision foundation models, and diffusion-based image generation into a scalable end-to-end semantic image editing platform.
