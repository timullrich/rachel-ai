import itertools
import sounddevice as sd
import numpy as np
import webrtcvad
import scipy.io.wavfile as wav
import os
import sys
import queue
import re
import concurrent.futures
import threading
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
vad.set_mode(3)  # 0 = aggressive, 3 = least aggressive

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
    recording_started = False  # Track if recording has started after speech detection

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

            # Check if speech is detected
            if is_speech(audio_frame, sample_rate):
                silence_duration = 0  # Reset silence duration if speech detected

                if not recording_started:
                    print("Speech detected, starting recording...")
                    recording_started = True  # Start recording after speech is detected

            else:
                if recording_started:
                    silence_duration += frame_duration_ms / 1000  # Count silence only after speech starts

            # If too much silence is detected after recording started, stop recording
            if recording_started and silence_duration > max_silence_duration:
                print("Silence detected, stopping recording.")
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


def stream_chat_with_gpt(user_input):
    """Stream the response from GPT using conversation history."""
    conversation_history.append({"role": "user", "content": user_input})

    # Stream the response
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=conversation_history,
        stream=True  # Enable streaming
    )

    assistant_reply = ""
    print("\nChatGPT is responding:\n")
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
            sys.stdout.write(content)
            sys.stdout.flush()
            assistant_reply += content  # Build the full response

    conversation_history.append({"role": "assistant", "content": assistant_reply})

    return assistant_reply






def stream_chat_with_gpt_and_speak(user_input):
    """Stream the GPT response and speak it in real-time."""
    conversation_history.append({"role": "user", "content": user_input})

    # Stream the response from GPT
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=conversation_history,
        stream=True  # Enable streaming
    )

    assistant_reply = ""
    print("\nChatGPT is responding:\n")
    text_buffer = ""  # Buffer to collect chunks of text for speaking
    buffer_limit = 50  # Set a reasonable buffer limit (can be adjusted)

    samplerate = 24000  # Set the sample rate for speech output
    chunk_size = 1024

    # Queue to hold audio chunks
    audio_queue = queue.Queue()

    # Lock to ensure correct order of transcription
    transcription_lock = threading.Lock()

    # Start the output audio stream for speech
    stream_audio = sd.OutputStream(samplerate=samplerate, channels=1, dtype='int16', blocksize=4096, latency='high')
    stream_audio.start()

    def process_speech(text):
        """Converts text to speech and stores audio chunks in the queue."""
        with transcription_lock:
            with client.audio.speech.with_streaming_response.create(
                    model="tts-1",
                    voice="nova",
                    input=text,
                    response_format="pcm"
            ) as response_audio:
                for audio_chunk in response_audio.iter_bytes(chunk_size):
                    audio_data = np.frombuffer(audio_chunk, dtype=np.int16)
                    audio_queue.put(audio_data)  # Store audio in the queue

    def play_audio():
        """Continuously play audio from the queue."""
        while True:
            audio_data = audio_queue.get()  # Blocking until an item is available
            if audio_data is None:  # End signal
                break
            stream_audio.write(audio_data)  # Write audio data to the stream

    # Start a thread to play audio continuously
    audio_thread = threading.Thread(target=play_audio)
    audio_thread.start()

    def collect_until_sentence_end(text_buffer):
        """Collect text until a sentence end is detected (., !, ?)."""
        match = re.search(r'[.!?]', text_buffer)   # Look for sentence-ending punctuation
        if match:
            return text_buffer[:match.end()], text_buffer[match.end():]  # Return the sentence and the remaining text
        return "", text_buffer

    # Use a thread pool to process speech in the background
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = None
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                sys.stdout.write(content)
                sys.stdout.flush()
                assistant_reply += content
                text_buffer += content

                # Check if the sentence ends to process the text
                sentence, remaining_text = collect_until_sentence_end(text_buffer)
                if sentence:
                    future = executor.submit(process_speech, sentence)
                    text_buffer = remaining_text  # Keep the leftover text for the next round

        # Process remaining text if any (even if it's not a complete sentence)
        if text_buffer:
            future = executor.submit(process_speech, text_buffer)

        # Wait for the speech processing to finish
        if future:
            future.result()

    # Signal the end of the stream
    audio_queue.put(None)

    # Wait for the audio thread to finish
    audio_thread.join()

    # Stop and close the audio stream
    stream_audio.stop()
    stream_audio.close()
    sd.wait()

    # Add final assistant reply to conversation history
    conversation_history.append({"role": "assistant", "content": assistant_reply})

    return assistant_reply


def highlight_chatgpt_reply(reply):
    """Highlight the reply from ChatGPT using a brighter style to simulate bold."""
    print(Fore.CYAN + Style.BRIGHT + "\nChatGPT: " + reply + Style.RESET_ALL)

def speak_reply(reply):
    samplerate = 24000  # Set the sample rate to match the response
    chunk_size = 1024  # Original chunk size
    buffer_size = 50  # collect chunks before playing.
    audio_buffer = []

    # Open a sounddevice stream to continuously play audio
    stream = sd.OutputStream(samplerate=samplerate, channels=1, dtype='int16')
    stream.start()

    with client.audio.speech.with_streaming_response.create(
            model="tts-1",
            voice="nova",
            input=reply,
            response_format="pcm"
    ) as response:
        for chunk in response.iter_bytes(chunk_size):
            # Convert the chunk to a NumPy array
            audio_data = np.frombuffer(chunk, dtype=np.int16)

            # Buffer the audio chunks
            audio_buffer.append(audio_data)

            # Wenn genügend Chunks gesammelt wurden, spiele sie ab
            if len(audio_buffer) >= buffer_size:
                complete_audio = np.concatenate(audio_buffer)

                # Write directly to the stream without waiting
                stream.write(complete_audio)

                # Puffer leeren für den nächsten Block
                audio_buffer = []

        # Spiele verbleibende Audio-Chunks nach dem Empfang ab
        if audio_buffer:
            complete_audio = np.concatenate(audio_buffer)
            stream.write(complete_audio)

    stream.stop()
    stream.close()
    sd.wait()


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

        # Stream the transcribed input to GPT and speak it in real-time
        reply = stream_chat_with_gpt_and_speak(user_input)

        # Highlight the final response after streaming
        highlight_chatgpt_reply(reply)

        # Delete the WAV file after transcription
        delete_wav_file(output_file)