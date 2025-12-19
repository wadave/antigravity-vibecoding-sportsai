import asyncio
from google import genai
from google.genai import types

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

import os

PROJECT_ID = "dw-genai-dev"
LOCATION = "global"


class GeminiService:
    def __init__(self):
        self.client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
        self.aclient = genai.Client(
            vertexai=True, project=PROJECT_ID, location=LOCATION
        ).aio

    async def generate_text(self, prompt: str, model: str = "gemini-3-pro-preview"):
        response = await self.aclient.models.generate_content(
            model=model, contents=prompt
        )
        return response.text

    async def generate_image(
        self, prompt: str, model: str = "gemini-3-pro-image-preview"
    ):
        try:
            response = await self.aclient.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                ),
            )
            # Assuming the image data is in the first part of the first candidate's content
            if response.candidates and response.candidates[0].content.parts:
                part = response.candidates[0].content.parts[0]
                with open("gemini_debug.log", "a") as f:
                    f.write(f"DEBUG: Part structure: {part}\n")

                if part.inline_data:
                    return part.inline_data.data
                elif part.text:
                    with open("gemini_debug.log", "a") as f:
                        f.write(
                            f"WARNING: Received text instead of image: {part.text}\n"
                        )
            else:
                with open("gemini_debug.log", "a") as f:
                    f.write(
                        f"WARNING: No candidates or parts in response: {response}\n"
                    )

            return None  # Return None if no inline data is found
        except Exception as e:
            with open("gemini_debug.log", "a") as f:
                f.write(f"ERROR: Exception in generate_image: {e}\n")
            return None

    async def analyze_frames(
        self, frames_data: list, model: str = "gemini-3-pro-preview"
    ):
        tasks = []
        for frame_bytes in frames_data:
            # In a real scenario, we might want to batch or send as a single video.
            # Here we are processing individual frames as requested.
            part = types.Part.from_bytes(data=frame_bytes, mime_type="image/jpeg")
            tasks.append(
                self.aclient.models.generate_content(
                    model=model,
                    contents=[
                        part,
                        "Detect sportsmen bounding boxes. Return JSON format: [{'box_2d': [ymin, xmin, ymax, xmax], 'label': 'person'}]",
                    ],
                )
            )
        responses = await asyncio.gather(*tasks)
        return [r.text for r in responses]

    async def analyze_video_strategic(
        self, gs_uri: str, model: str = "gemini-3-pro-preview"
    ):
        part = types.Part.from_uri(file_uri=gs_uri, mime_type="video/mp4")
        response = await self.aclient.models.generate_content(
            model=model,
            contents=[
                part,
                """
            Analyze this sports video and provide a strategic summary. 
            Identify one key frame where the player could improve their technique.
            Return a JSON object with the following fields:
            - summary: A strategic summary of the performance.
            - key_frame_timestamp: The timestamp (in seconds) of the key frame to improve.
            - improvement_box_2d: A bounding box [ymin, xmin, ymax, xmax] (0-1000 scale) identifying the area of improvement.
            - advice: Specific advice for that frame.
            
            Ensure the response is valid JSON.
            """,
            ],
        )
        return response.text
