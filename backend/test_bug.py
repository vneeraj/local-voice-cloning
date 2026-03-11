import traceback
from tts_service import XTTSv2Service
import os

try:
    tts = XTTSv2Service()
    # take the first file in uploads
    upload_dir = "uploads"
    files = os.listdir(upload_dir)
    if files:
        ref_path = os.path.join(upload_dir, files[0])
        print(f"Testing with {ref_path}")
        tts.generate_speech('test', ref_path, 'en', 'out.wav')
    else:
        print("No uploads found.")
except Exception as e:
    traceback.print_exc()
