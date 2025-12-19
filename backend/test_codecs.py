import cv2
import os

def test_codec(codec, ext):
    filename = f"test_{codec}.{ext}"
    fourcc = cv2.VideoWriter_fourcc(*codec)
    out = cv2.VideoWriter(filename, fourcc, 20.0, (640, 480))
    if out.isOpened():
        print(f"Codec {codec} ({ext}): SUCCESS")
        out.release()
        os.remove(filename)
        return True
    else:
        print(f"Codec {codec} ({ext}): FAILED")
        return False

codecs = [
    ('avc1', 'mp4'),
    ('mp4v', 'mp4'),
    ('vp80', 'webm'),
    ('vp09', 'webm'),
    ('MJPG', 'avi'),
    ('THEO', 'ogv')
]

print("Testing OpenCV Codecs...")
for codec, ext in codecs:
    test_codec(codec, ext)
