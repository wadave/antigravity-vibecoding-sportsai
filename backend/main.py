# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import os
import uuid
import cv2
import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from services.gcs_service import GCSService
from services.gemini_service import GeminiService
from services.video_service import VideoService

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the assets directory to serve static files
os.makedirs("assets", exist_ok=True)
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

gcs_service = GCSService()
gemini_service = GeminiService()
video_service = VideoService()


@app.get("/files/{blob_name:path}")
async def get_file(blob_name: str, background_tasks: BackgroundTasks):
    # Keep this for GCS files (video uploads/processed)
    local_path = f"temp_{blob_name.replace('/', '_')}"
    if not os.path.exists(local_path):
        try:
            gcs_service.download_file(blob_name, local_path)
        except Exception:
            raise HTTPException(status_code=404, detail="File not found")

    # Schedule cleanup after serving
    background_tasks.add_task(os.remove, local_path)

    # Determine media type based on extension
    media_type = None
    if blob_name.endswith(".mp4"):
        media_type = "video/mp4"
    elif blob_name.endswith(".webm"):
        media_type = "video/webm"
    elif blob_name.endswith(".jpg") or blob_name.endswith(".jpeg"):
        media_type = "image/jpeg"
    elif blob_name.endswith(".png"):
        media_type = "image/png"

    return FileResponse(local_path, media_type=media_type)


@app.get("/header-info")
async def get_header_info():
    cache_file = "header_cache.json"

    # Check if icon exists locally
    icon_path = "assets/app_icon.png"
    if not os.path.exists(icon_path):
        print("Generating new app icon...")
        icon_prompt = "Collage of dynamic sportsmen (football, basketball, tennis) in a flat vector app icon style."
        image_data = await gemini_service.generate_image(
            icon_prompt, model="gemini-3-pro-image-preview"
        )

        if image_data:
            with open(icon_path, "wb") as f:
                f.write(image_data)
        else:
            # If generation fails, we can't save it.
            pass

    # Determine icon URL
    if os.path.exists(icon_path):
        icon_url = "http://localhost:8000/assets/app_icon.png"
    else:
        icon_url = "https://via.placeholder.com/150"

    # Handle text description caching (keep existing JSON cache for text)
    if os.path.exists(cache_file):
        try:
            with open(cache_file) as f:
                data = json.load(f)
                # Update icon_url in case it was a placeholder before
                data["icon_url"] = icon_url
                return data
        except (json.JSONDecodeError, ValueError):
            pass

    # Use a static description instead of LLM generation
    description = "Your AI-powered pocket coach. Capture, analyze, and perfect your form in seconds."

    data = {"description": description, "icon_url": icon_url}
    with open(cache_file, "w") as f:
        json.dump(data, f)
    return data


@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    file_id = str(uuid.uuid4())
    file_path = f"temp_{file_id}.mp4"
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        blob_name = f"uploads/{file_id}/{file.filename}"
        gcs_uri = gcs_service.upload_file(file_path, blob_name)
        # Use proxy URL for consistency with other files, or signed URL if preferred
        signed_url = f"http://localhost:8000/files/{blob_name}"

        return {"gcs_uri": gcs_uri, "signed_url": signed_url, "file_id": file_id}
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


@app.post("/analyze_video")
async def analyze_video(gcs_uri: str, file_id: str):
    # Background task would be better for long running, but for simplicity we do it here
    # or use BackgroundTasks.

    local_input_path = f"input_{file_id}.mp4"
    local_output_path = f"output_{file_id}.webm"
    advice_filename = f"advice_{file_id}.jpg"

    try:
        # 1. Download video
        bucket_name, blob_name = gcs_service.parse_gs_uri(gcs_uri)
        gcs_service.download_file(blob_name, local_input_path)

        # 2. Extract frames
        frames, fps = video_service.extract_frames(local_input_path, sample_rate=5)

        # 3. Analyze frames with Gemini
        frames_data = []
        for frame in frames:
            _, buffer = cv2.imencode(".jpg", frame)
            frames_data.append(buffer.tobytes())

        # Limit frames to avoid hitting rate limits in prototype
        print(f"Analyzing {len(frames_data[:10])} frames...")
        analysis_results = await gemini_service.analyze_frames(frames_data[:10])
        print(f"Analysis complete. Received {len(analysis_results)} results.")

        # 4. Draw bounding boxes
        processed_frames = video_service.draw_bounding_boxes(
            frames[:10], analysis_results, sample_rate=5
        )

        # 5. Reassemble video
        video_service.reassemble_video(
            processed_frames, local_output_path, fps / 5
        )  # Adjusted FPS for sampled frames

        # 6. Upload to GCS
        if not os.path.exists(local_output_path):
            raise HTTPException(
                status_code=500, detail="Failed to generate processed video"
            )

        output_blob_name = f"processed/{file_id}/processed_video.webm"
        gcs_service.upload_file(local_output_path, output_blob_name)
        output_signed_url = f"http://localhost:8000/files/{output_blob_name}"

        # Get strategic summary and visual advice
        strategic_response = await gemini_service.analyze_video_strategic(gcs_uri)

        summary_text = strategic_response
        advice_url = None

        try:
            # Clean up JSON markdown if present
            json_str = strategic_response
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]

            data = json.loads(json_str)
            summary_text = data.get("summary", strategic_response)

            # Generate visual advice image
            timestamp = data.get("key_frame_timestamp")
            box_2d = data.get("improvement_box_2d")
            advice = data.get("advice", "Improvement Area")

            if timestamp is not None:
                if video_service.extract_and_annotate_frame(
                    local_input_path, timestamp, box_2d, advice, advice_filename
                ):
                    advice_blob_name = f"processed/{file_id}/advice.jpg"
                    gcs_service.upload_file(advice_filename, advice_blob_name)
                    advice_url = f"http://localhost:8000/files/{advice_blob_name}"

        except Exception as e:
            print(f"Error generating visual advice: {e}")
            # Fallback to just text if JSON parsing or image generation fails
            pass

        return {
            "processed_url": output_signed_url,
            "summary": summary_text,
            "advice_url": advice_url,
        }

    finally:
        # Final cleanup of all local files
        for path in [local_input_path, local_output_path, advice_filename]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as e:
                    print(f"Error deleting {path}: {e}")


@app.get("/readme")
async def get_readme():
    cache_file = "generated_readme.md"
    if os.path.exists(cache_file):
        with open(cache_file) as f:
            return {"content": f.read()}

    prompt = """
    Generate a comprehensive README.md for a Sports Video Analysis App.
    The app uses React (Vite) + Tailwind CSS for the frontend, and Python FastAPI for the backend.
    It integrates OpenCV for video processing, Google Cloud Storage (GCS) for asset management,
    and Google's Gemini Models (gemini-3-pro-preview, gemini-3-pro-image-preview) for AI analysis and image generation.

    Include:
    1. App Description
    2. Basic Setup Instructions (using uv and npm)
    3. Usage Guide
    """
    content = await gemini_service.generate_text(prompt)
    with open(cache_file, "w") as f:
        f.write(content)
    return {"content": content}


@app.get("/architecture-image")
async def get_architecture_image():
    # Check if architecture diagram exists locally
    image_path = "assets/architecture_diagram.png"

    if not os.path.exists(image_path):
        print("Generating new architecture diagram...")

        # Instructions say: Backend reads README.md, then sends text to gemini-3-pro-image-preview
        readme_content = ""
        cache_file = "generated_readme.md"
        if os.path.exists(cache_file):
            with open(cache_file) as f:
                readme_content = f.read()
        else:
            # Fallback if readme not yet generated
            readme_data = await get_readme()
            readme_content = readme_data["content"]

        prompt = f"System Architecture Infographic based on the following README content:\n\n{readme_content[:2000]}"
        image_data = await gemini_service.generate_image(
            prompt, model="gemini-3-pro-image-preview"
        )

        if image_data:
            with open(image_path, "wb") as f:
                f.write(image_data)
        else:
            # If generation fails
            pass

    if os.path.exists(image_path):
        image_url = "http://localhost:8000/assets/architecture_diagram.png"
    else:
        image_url = "https://via.placeholder.com/600x400"

    data = {"image_url": image_url}
    return data


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
