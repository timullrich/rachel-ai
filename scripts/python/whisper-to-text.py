import sounddevice as sd
import whisper
import scipy.io.wavfile as wav
import warnings
import os

# Suppress the FP16 warning
warnings.filterwarnings(
    "ignore", message="FP16 is not supported on CPU; using FP32 instead"
)

# Load the Whisper model
model = whisper.load_model(
    "base"
)  # You can also choose "tiny" or "small" based on resource availability

# Recording parameters
duration = 10  # Recording duration in seconds
sample_rate = 16000  # Standard sample rate for Whisper
output_file = "output.wav"


def record_audio(duration, sample_rate):
    """Record audio for the given duration."""
    print("Recording started for 10 seconds...")
    audio = sd.rec(
        int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype="int16"
    )
    sd.wait()  # Wait until the recording is complete
    return audio


def save_audio_to_wav(audio, sample_rate, filename=output_file):
    """Save the recorded audio to a WAV file."""
    wav.write(filename, sample_rate, audio)
    print(f"Audio saved to: {filename}")


def transcribe_audio(filename):
    """Transcribe the WAV file using Whisper."""
    print("Processing audio with Whisper...")
    result = model.transcribe(filename)
    print(f"Transcribed text: {result['text']}")


def delete_wav_file(filename):
    """Delete the WAV file after transcription."""
    if os.path.exists(filename):
        os.remove(filename)
        print(f"WAV file '{filename}' deleted.")
    else:
        print(f"WAV file '{filename}' not found.")


if __name__ == "__main__":
    print("Welcome to Whisper-to-Text!")

    # Record audio once for 10 seconds
    audio = record_audio(duration, sample_rate)
    save_audio_to_wav(audio, sample_rate)

    # Process the saved audio file
    transcribe_audio(output_file)

    # Delete the WAV file after transcription
    delete_wav_file(output_file)

    print("Exiting program.")
