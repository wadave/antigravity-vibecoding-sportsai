import json


# Mock the class structure efficiently to test the method
class VideoService:
    def draw_bounding_boxes(
        self, frames: list, analysis_results: list, sample_rate: int = 5
    ):
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

        return parsed_boxes


def test_parsing():
    service = VideoService()

    # Test Case 1: Valid JSON
    print("\n--- Test Case 1: Valid JSON ---")
    valid_json = '[{"box_2d": [0, 0, 100, 100], "label": "person"}]'
    results = service.draw_bounding_boxes([], [valid_json])
    print(f"Result: {len(results[0])} boxes found.")
    assert len(results[0]) == 1

    # Test Case 2: Markdown JSON
    print("\n--- Test Case 2: Markdown JSON ---")
    markdown_json = '```json\n[{"box_2d": [0, 0, 100, 100], "label": "person"}]\n```'
    results = service.draw_bounding_boxes([], [markdown_json])
    print(f"Result: {len(results[0])} boxes found.")
    assert len(results[0]) == 1

    # Test Case 3: Invalid Structure (Int)
    print("\n--- Test Case 3: Invalid Structure (Int) ---")
    int_json = "123"
    results = service.draw_bounding_boxes([], [int_json])
    print(f"Result: {len(results[0])} boxes found.")
    assert len(results[0]) == 0

    # Test Case 4: Invalid Structure (Dict instead of List)
    print("\n--- Test Case 4: Invalid Structure (Dict) ---")
    dict_json = '{"box_2d": [0,0,0,0], "label": "person"}'
    results = service.draw_bounding_boxes([], [dict_json])
    print(f"Result: {len(results[0])} boxes found.")
    assert len(results[0]) == 0

    # Test Case 5: Malformed JSON
    print("\n--- Test Case 5: Malformed JSON ---")
    malformed_json = '[{"box_2d":...'
    results = service.draw_bounding_boxes([], [malformed_json])
    print(f"Result: {len(results[0])} boxes found.")
    assert len(results[0]) == 0

    print("\n✅ All parsing tests passed!")


if __name__ == "__main__":
    test_parsing()
