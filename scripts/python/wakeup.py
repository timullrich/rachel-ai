import os
from dotenv import load_dotenv
import pvporcupine
import sounddevice as sd
import numpy as np
import subprocess

# Load environment variables from .env file
load_dotenv()

# Add your Access Key here
access_key = os.getenv("PORCUPINE_ACCESS_KEY")


# Dynamically get the absolute path to the PPN file
script_dir = os.path.dirname(os.path.realpath(__file__))
# Paths to the PPN and PV files
keyword_path = os.path.join(script_dir, "../../resources/rachel_wake_word.ppn")
model_path = os.path.join(script_dir, "../../resources/porcupine_params_de.pv")


def start_chat():
    script_to_start = os.path.join(script_dir, "openai-talk.py")
    subprocess.run(["python3", script_to_start])

def audio_callback(indata, frames, time, status):
    global porcupine
    pcm = np.int16(indata[:, 0] * 32767)
    result = porcupine.process(pcm)

    if result >= 0:
        print("Wake word 'Hey Rachel' detected!")
        start_chat()

def main():
    global porcupine
    porcupine = None

    try:
        # Initialize Porcupine with the access key and the keyword path
        porcupine = pvporcupine.create(
            access_key=access_key,
            keyword_paths=[keyword_path],
            model_path=model_path
        )

        with sd.InputStream(samplerate=porcupine.sample_rate, channels=1, callback=audio_callback, blocksize=porcupine.frame_length):
            print("Listening for 'Hey Rachel'...")
            while True:
                sd.sleep(1000)

    finally:
        if porcupine is not None:
            porcupine.delete()

if __name__ == "__main__":
    main()
