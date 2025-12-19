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

import cv2
import json


class VideoService:
    def __init__(self):
        pass

    def extract_and_annotate_frame(
        self,
        video_path: str,
        timestamp: float,
        box_2d: list,
        label: str,
        output_path: str,
    ):
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_no = int(timestamp * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
        ret, frame = cap.read()
        cap.release()

        if not ret:
            return False

        if box_2d and len(box_2d) == 4:
            h, w, _ = frame.shape
            ymin, xmin, ymax, xmax = box_2d
            start_point = (int(xmin * w / 1000), int(ymin * h / 1000))
            end_point = (int(xmax * w / 1000), int(ymax * h / 1000))

            # Draw distinct box for advice
            cv2.rectangle(frame, start_point, end_point, (0, 0, 255), 3)  # Red box

            # Add label background
            label_size, baseline = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2
            )
            cv2.rectangle(
                frame,
                (start_point[0], start_point[1] - label_size[1] - 10),
                (start_point[0] + label_size[0], start_point[1]),
                (0, 0, 255),
                cv2.FILLED,
            )
            cv2.putText(
                frame,
                label,
                (start_point[0], start_point[1] - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
            )

        cv2.imwrite(output_path, frame)
        return True

    def extract_frames(self, video_path: str, sample_rate: int = 5):
        cap = cv2.VideoCapture(video_path)
        frames = []
        frame_count = 0
        fps = cap.get(cv2.CAP_PROP_FPS)
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            if frame_count % sample_rate == 0:
                frames.append(frame)
            frame_count += 1
        cap.release()
        return frames, fps

    def draw_bounding_boxes(
        self, frames: list, analysis_results: list, sample_rate: int = 5
    ):
        processed_frames = []
        num_frames = len(frames)

        # Parse all boxes first
        parsed_boxes = []
        for i in range(len(analysis_results)):
            boxes = []
            text = analysis_results[i]
            try:
                # Clean up markdown
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0]
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0]

                boxes_data = json.loads(text)

                # Validation
                if isinstance(boxes_data, list):
                    for item in boxes_data:
                        if (
                            isinstance(item, dict)
                            and "box_2d" in item
                            and "label" in item
                        ):
                            boxes.append(item)
                        else:
                            print(f"WARNING: Invalid item format in frame {i}: {item}")
                else:
                    print(
                        f"WARNING: Expected list but got {type(boxes_data)} in frame {i}: {boxes_data}"
                    )

            except Exception as e:
                print(f"ERROR: Failed to parse parsing JSON for frame {i}: {e}")
                print(f"DEBUG: Raw text was: {text[:100]}...")
                pass
            parsed_boxes.append(boxes)

        for i in range(num_frames):
            frame = frames[i]
            # Find current and next sampled frame index
            current_sample_idx = i // sample_rate
            next_sample_idx = current_sample_idx + 1

            # Use interpolation if we have a next sample
            if next_sample_idx < len(parsed_boxes):
                progress = (i % sample_rate) / sample_rate
                current_boxes = parsed_boxes[current_sample_idx]
                next_boxes = parsed_boxes[next_sample_idx]

                # Simple heuristic: interpolate boxes that have the same label/index
                # In a real app, we'd use object IDs, but here we just match by index
                for j in range(max(len(current_boxes), len(next_boxes))):
                    box_data = None
                    if j < len(current_boxes) and j < len(next_boxes):
                        # Interpolate
                        if isinstance(current_boxes[j], dict) and isinstance(
                            next_boxes[j], dict
                        ):
                            b1 = current_boxes[j].get("box_2d")
                            b2 = next_boxes[j].get("box_2d")
                            if b1 and b2 and len(b1) == 4 and len(b2) == 4:
                                interp_box = [
                                    int(b1[0] + (b2[0] - b1[0]) * progress),
                                    int(b1[1] + (b2[1] - b1[1]) * progress),
                                    int(b1[2] + (b2[2] - b1[2]) * progress),
                                    int(b1[3] + (b2[3] - b1[3]) * progress),
                                ]
                                label = current_boxes[j].get("label", "person")
                                self._draw_box(frame, interp_box, label)
                    elif j < len(current_boxes):
                        # Use current
                        if isinstance(current_boxes[j], dict):
                            self._draw_box(
                                frame,
                                current_boxes[j].get("box_2d"),
                                current_boxes[j].get("label", "person"),
                            )
            else:
                # Last sample or beyond, just use current
                current_boxes = (
                    parsed_boxes[current_sample_idx]
                    if current_sample_idx < len(parsed_boxes)
                    else []
                )
                for box_data in current_boxes:
                    if isinstance(box_data, dict):
                        self._draw_box(
                            frame,
                            box_data.get("box_2d"),
                            box_data.get("label", "person"),
                        )

            processed_frames.append(frame)
        return processed_frames

    def _draw_box(self, frame, box, label):
        if box and len(box) == 4:
            h, w, _ = frame.shape
            ymin, xmin, ymax, xmax = box
            start_point = (int(xmin * w / 1000), int(ymin * h / 1000))
            end_point = (int(xmax * w / 1000), int(ymax * h / 1000))
            cv2.rectangle(frame, start_point, end_point, (0, 255, 0), 2)
            cv2.putText(
                frame,
                label,
                (start_point[0], start_point[1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2,
            )

    def reassemble_video(self, frames: list, output_path: str, fps: float):
        if not frames:
            return
        h, w, _ = frames[0].shape

        # Determine codec based on extension or default to vp09 for webm
        if output_path.endswith(".webm"):
            # Try vp80 (VP8) first as it has better compatibility in some OpenCV builds
            fourcc = cv2.VideoWriter_fourcc(*"vp80")
            out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))
            if not out.isOpened():
                print("WARNING: 'vp80' codec failed. Falling back to 'vp09'.")
                fourcc = cv2.VideoWriter_fourcc(*"vp09")
                out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))
        else:
            # Default to avc1/mp4v for mp4
            fourcc = cv2.VideoWriter_fourcc(*"avc1")
            out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))
            if not out.isOpened():
                print("WARNING: 'avc1' codec failed. Falling back to 'mp4v'.")
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

        if not out.isOpened():
            print("ERROR: Failed to open VideoWriter.")
            return
        for frame in frames:
            out.write(frame)
        out.release()
