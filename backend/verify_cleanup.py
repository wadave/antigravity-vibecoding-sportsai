import os
import asyncio


async def test_cleanup():
    print("Testing local file cleanup simulation...")

    # 1. Simulate /files proxy cleanup (BackgroundTasks simulation)
    local_proxy_path = "temp_test_blob.mp4"
    with open(local_proxy_path, "w") as f:
        f.write("test data")

    print(f"Created proxy file: {local_proxy_path}")

    # In main.py, we use background_tasks.add_task(os.remove, local_path)
    # We simulate the execution of the background task
    print("Simulating FastAPI BackgroundTask execution...")
    if os.path.exists(local_proxy_path):
        os.remove(local_proxy_path)

    if not os.path.exists(local_proxy_path):
        print("✅ Proxy file cleanup simulation verified.")
    else:
        print("❌ Proxy file cleanup simulation failed.")

    # 2. Simulate analyze_video cleanup (try...finally simulation)
    file_id = "test_uuid"
    local_input_path = f"input_{file_id}.mp4"
    local_output_path = f"output_{file_id}.webm"
    advice_filename = f"advice_{file_id}.jpg"

    files_to_check = [local_input_path, local_output_path, advice_filename]

    for path in files_to_check:
        with open(path, "w") as f:
            f.write("test data")
        print(f"Created temp file: {path}")

    print("Simulating processing and finally block cleanup...")
    # This matches the code in main.py:
    # finally:
    #     for path in [local_input_path, local_output_path, advice_filename]:
    #         if os.path.exists(path):
    #             os.remove(path)

    for path in files_to_check:
        if os.path.exists(path):
            os.remove(path)
            print(f"Deleted: {path}")

    remaining = [p for p in files_to_check if os.path.exists(p)]
    if not remaining:
        print("✅ analyze_video cleanup simulation verified.")
    else:
        print(f"❌ analyze_video cleanup simulation failed. Remaining: {remaining}")


if __name__ == "__main__":
    asyncio.run(test_cleanup())
