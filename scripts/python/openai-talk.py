import itertools
import sounddevice as sd
import numpy as np
import webrtcvad
import scipy.io.wavfile as wav
import os
import sys
from pathlib import Path
import subprocess
from colorama import Fore, Style
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

# Initialize VAD
vad = webrtcvad.Vad()
vad.set_mode(1)  # 0 = aggressive, 3 = least aggressive

# Recording parameters
sample_rate = 16000  # Standard sample rate for Whisper
output_file = "output.wav"
frame_duration_ms = 30  # Frame size in ms (must be 10, 20, or 30)
frame_size = int(sample_rate * frame_duration_ms / 1000)

# List to store the conversation history
conversation_history = []

# Rotating spinner for visual feedback
spinner = itertools.cycle(['-', '\\', '|', '/'])

def is_speech(frame, sample_rate):
    """Check if the audio frame contains speech using webrtcvad."""
    return vad.is_speech(frame.tobytes(), sample_rate)

def record_audio(sample_rate):
    """Record audio dynamically, stop when no speech is detected."""
    audio_frames = []
    silence_duration = 0
    max_silence_duration = 1  # Stop recording after 1 second of silence

    stream = sd.InputStream(samplerate=sample_rate, channels=1, dtype='int16')
    stream.start()

    try:
        while True:
            audio_frame, _ = stream.read(frame_size)
            audio_frames.append(audio_frame)
            # Display a rotating spinner
            sys.stdout.write(next(spinner))  # Show the next spinner character
            sys.stdout.flush()
            sys.stdout.write('\b')  # Erase the last character printed

            if is_speech(audio_frame, sample_rate):
                silence_duration = 0  # Reset silence duration if speech detected
            else:
                silence_duration += frame_duration_ms / 1000  # Count silence

            # If there's too much silence, stop recording
            if silence_duration > max_silence_duration:
                #print("\nSilence detected, stopping recording.")
                break
    except KeyboardInterrupt:
        print("\nRecording interrupted manually.")

    stream.stop()
    audio = np.concatenate(audio_frames, axis=0)
    return audio

def save_audio_to_wav(audio, sample_rate, filename=output_file):
    """Save the recorded audio to a WAV file."""
    wav.write(filename, sample_rate, audio)
    #print(f"Audio saved to: {filename}")


def transcribe_audio(audio_file_path):
    """Transcribe the audio file using OpenAI's Whisper API."""
    with open(audio_file_path, 'rb') as audio_file:
        #print("Sending audio to OpenAI for transcription...")
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
        return transcription.text

def delete_wav_file(filename):
    """Delete the file after transcription."""
    if os.path.exists(filename):
        os.remove(filename)
    #     print(f"WAV file '{filename}' deleted.")
    # else:
    #     print(f"WAV file '{filename}' not found.")


def chat_with_gpt(user_input):
    """Chat with GPT using conversation history."""
    conversation_history.append({"role": "user", "content": user_input})

    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=conversation_history
    )

    assistant_reply = completion.choices[0].message.content
    conversation_history.append({"role": "assistant", "content": assistant_reply})

    return assistant_reply

def highlight_chatgpt_reply(reply):
    """Highlight the reply from ChatGPT using a brighter style to simulate bold."""
    print(Fore.CYAN + Style.BRIGHT + "\nChatGPT: " + reply + Style.RESET_ALL)

def play_audio_with_ffplay(file_path):
    """Play the audio file using ffplay."""
    subprocess.run(["ffplay", "-nodisp", "-autoexit", str(file_path)])

def speak_reply(reply):
    """Convert the ChatGPT reply to speech using OpenAI's Text-to-Speech API and play it."""
    speech_file_path = Path(__file__).parent / "speech.mp3"
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",  # You can change the voice if needed
        input=reply
    )
    response.stream_to_file(speech_file_path)
    print(f"Speech saved as {speech_file_path}")

    # Play the saved speech file using ffplay
    play_audio_with_ffplay(speech_file_path)

if __name__ == "__main__":
    conversation_history.insert(0, {"role": "system", "content": "You are a helpful assistant."})

    print("Welcome to the OpenAI Audio Chat! Say 'exit' or 'quit' to end the conversation.")

    while True:
        # Dynamically record audio until silence is detected
        audio = record_audio(sample_rate)
        save_audio_to_wav(audio, sample_rate)

        # Transcribe the saved audio file using OpenAI API
        user_input = transcribe_audio(output_file)
        print(f"You: {user_input}")

        # Exit the loop if the user says 'exit' or 'quit'
        if user_input.lower() in ['exit', 'quit']:
            print("Goodbye!")
            delete_wav_file(output_file)
            break

        # Send the transcribed input to the chat_with_gpt function
        reply = chat_with_gpt(user_input)
        highlight_chatgpt_reply(reply)

        # Convert the reply to speech using OpenAI TTS
        speak_reply(reply)

        # Delete the WAV file after transcription
        delete_wav_file(output_file)