import itertools
import sounddevice as sd
import numpy as np
import webrtcvad
import scipy.io.wavfile as wav
import os
import sys
import queue
import time
import re
import concurrent.futures
import threading
import subprocess
from colorama import Fore, Style
from openai import OpenAI
from dotenv import load_dotenv
import pvporcupine
from scipy.signal import butter, sosfilt
from scipy.fft import rfft, rfftfreq

# Load environment variables from .env file
load_dotenv()

platform = os.getenv("PLATFORM")
access_key = os.getenv("PORCUPINE_ACCESS_KEY")

# Initialize OpenAI client
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

script_dir = os.path.dirname(os.path.realpath(__file__))
audio_queue = queue.Queue()
transcription_lock = threading.Lock()

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

# Porcupine wake-word initialization
keyword_path = os.path.join(script_dir,
                            f"../../resources/porcupine/platform/{platform}/rachel_wake_word.ppn")
model_path = os.path.join(script_dir, "../../resources/porcupine/porcupine_params_de.pv")

stop_flag = threading.Event()  # Flag to stop processes when wake-word is detected

# Rotating spinner for visual feedback
spinner = itertools.cycle(['-', '\\', '|', '/'])

def execute_command(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return result.stderr.strip()
    except Exception as e:
        return f"Error executing command: {str(e)}"

def butter_bandpass_sos(lowcut, highcut, fs, order=14):
    """Create an even sharper bandpass filter using Second-Order Sections to filter out unwanted frequencies."""
    sos = butter(order, [lowcut, highcut], btype='band', output='sos', fs=fs)
    return sos


def apply_filter_sos(data, sos):
    """Apply the second-order sections filter to the audio data."""
    filtered = sosfilt(sos, data)
    return filtered


def is_speech(frame, sample_rate, volume_threshold=1500, frame_duration_ms=30):
    """Check if the audio frame contains speech using webrtcvad and additional filtering."""

    # Convert frame to numpy array
    audio_data = np.frombuffer(frame, dtype=np.int16)

    # Check if the volume is above the threshold to filter out quiet noise
    max_amplitude = np.max(np.abs(audio_data))
    if max_amplitude < volume_threshold:
        return False  # Frame is too quiet to be speech

    # Frequency analysis to discard non-speech-like sounds
    yf = rfft(audio_data)
    xf = rfftfreq(len(audio_data), 1 / sample_rate)

    # Reject non-speech frequencies and tighten the range further
    dominant_freq = np.argmax(np.abs(yf))
    dominant_frequency_value = xf[dominant_freq]

    if dominant_frequency_value < 500 or dominant_frequency_value > 2400:
        return False  # Not speech-like sound based on frequency range

    # Create the bandpass filter (using sos format for stability)
    sos = butter_bandpass_sos(lowcut=500.0, highcut=2400.0, fs=sample_rate)

    # Apply the sos filter to the audio data
    filtered_data = apply_filter_sos(audio_data, sos)

    # Convert filtered data back to bytes for webrtcvad
    filtered_frame = filtered_data.astype(np.int16).tobytes()

    # Use webrtcvad to check if the frame contains speech
    speech_detected = vad.is_speech(filtered_frame, sample_rate)

    return speech_detected


def aggregate_frames(frames, sample_rate):
    """Aggregate multiple frames to avoid reacting to short, sudden sounds."""
    aggregated = np.concatenate(frames)
    return is_speech(aggregated.tobytes(), sample_rate)

def record_audio(sample_rate):
    """Record audio dynamically, stop when no speech is detected."""

    play_sound(os.path.join(script_dir, "../../resources/sounds/sent.wav"))

    audio_frames = []
    silence_duration = 0
    max_silence_duration = 1  # Stop recording after 1 second of silence
    recording_started = False  # Track if recording has started after speech detection

    stream = sd.InputStream(samplerate=sample_rate, channels=1, dtype='int16')
    stream.start()

    start_time = time.time()

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

            # Check if 5 seconds have passed without starting the recording
            if not recording_started and (time.time() - start_time) > 4:
                print("No speech detected for 4 seconds, exiting...")
                play_sound(os.path.join(script_dir, "../../resources/sounds/standby.wav"))
                sys.exit()  # Exit the entire script

            else:
                if recording_started:
                    if silence_duration < max_silence_duration:
                        silence_duration += frame_duration_ms / 1000  # Count silence only after speech starts

            # If too much silence is detected after recording started, stop recording
            if recording_started and silence_duration > max_silence_duration:
                print("Silence detected, stopping recording.")
                break

    finally:
        stream.stop()
        stream.close()

    # Convert audio_frames (list of arrays) to a single NumPy array
    if audio_frames:
        audio_array = np.concatenate(audio_frames, axis=0)
        return audio_array  # Rückgabe als NumPy-Array
    else:
        return None  # Rückgabe None, wenn kein Audio aufgenommen wurde


def save_audio_to_wav(audio, sample_rate, filename=output_file):
    """Save the recorded audio to a WAV file."""
    wav.write(filename, sample_rate, audio)


def transcribe_audio(audio_file_path):
    """Transcribe the audio file using OpenAI's Whisper API."""
    with open(audio_file_path, 'rb') as audio_file:
        print("Sending audio to OpenAI for transcription...")
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
        return transcription.text


def delete_wav_file(filename):
    if os.path.exists(filename):
        os.remove(filename)


def process_speech(client, text, chunk_size=1024):
    if stop_flag.is_set():
        return

    """Converts text to speech and stores audio chunks in the queue."""
    with transcription_lock:
        if stop_flag.is_set():
            return
        with client.audio.speech.with_streaming_response.create(
                model="tts-1",
                voice="nova",
                input=text,
                response_format="pcm"
        ) as response_audio:
            for audio_chunk in response_audio.iter_bytes(chunk_size):
                if stop_flag.is_set():
                    response_audio.close()
                    return
                audio_data = np.frombuffer(audio_chunk, dtype=np.int16)
                audio_queue.put(audio_data)  # Store audio in the queue


def play_audio(samplerate=24000, channels=1):
    """Continuously play audio from the queue."""
    stream_audio = sd.OutputStream(samplerate=samplerate, channels=channels, dtype='int16',
                                   blocksize=4096, latency=0.5)
    stream_audio.start()

    while True:
        if stop_flag.is_set():
            break

        try:
            audio_data = audio_queue.get(timeout=1)
        except queue.Empty:
            continue

        if audio_data is None:
            stop_flag.set()
            break

        stream_audio.write(audio_data)

    # Stoppe und schließe den Audio-Stream
    stream_audio.stop()
    stream_audio.close()
    sd.wait()
    sd.wait()

    # Leere die Audio-Queue, um sicherzustellen, dass keine weiteren Chunks abgespielt werden
    with audio_queue.mutex:
        audio_queue.queue.clear()


def collect_until_sentence_end(text_buffer):
    """Collect text until a sentence end is detected (., !, ?)."""
    match = re.search(r'[.!?]', text_buffer)  # Look for sentence-ending punctuation
    if match:
        return text_buffer[:match.end()], text_buffer[
                                          match.end():]  # Return the sentence and the remaining text
    return "", text_buffer


def format_and_print_content(content):
    """Formats content for console output."""
    formatted_content = Fore.CYAN + Style.BRIGHT + content + Style.RESET_ALL
    sys.stdout.write(formatted_content)
    sys.stdout.flush()


def play_sound(file_path):
    if not os.path.isfile(file_path):
        print(f"File {file_path} not found!")
        return
    try:
        subprocess.run(
            ['ffplay', '-nodisp', '-autoexit', file_path],
            stdout=subprocess.DEVNULL,  # Verbirgt Standardausgabe
            stderr=subprocess.DEVNULL,  # Verbirgt Fehlerausgabe
            check=True
        )
        sd.wait()
    except subprocess.CalledProcessError as e:
        print(f"Error while playing sound: {e}")


def audio_callback(indata, frames, time, status):
    global porcupine
    pcm = np.int16(indata[:, 0] * 32767)
    result = porcupine.process(pcm)

    if result >= 0:
        # Stop Wake Word detected
        stop_flag.set()  # Set the flag to stop GPT and audio streaming.


def listen_for_wakeword():
    """Listens for the wakeword in a separate thread."""
    global porcupine
    porcupine = None
    try:
        porcupine = pvporcupine.create(
            access_key=access_key,
            keyword_paths=[keyword_path],
            model_path=model_path
        )

        with sd.InputStream(samplerate=porcupine.sample_rate, channels=1, callback=audio_callback, blocksize=porcupine.frame_length):
            print("Listening for 'Hey Rachel'...")
            while not stop_flag.is_set():
                sd.sleep(1000)


    finally:
        if porcupine:
            porcupine.delete()


def speak(text):
    samplerate = 24000  # Set the sample rate to match the response
    chunk_size = 1024  # Original chunk size
    buffer_size = 100  # Collect chunks before playing
    audio_buffer = []

    # Open a sounddevice stream to continuously play audio
    with sd.OutputStream(samplerate=samplerate, channels=1, dtype='int16') as stream:

        with client.audio.speech.with_streaming_response.create(
                model="tts-1",
                voice="nova",
                input=text,
                response_format="pcm"
        ) as response:
            for chunk in response.iter_bytes(chunk_size):
                # Convert the chunk to a NumPy array
                audio_data = np.frombuffer(chunk, dtype=np.int16)

                # Buffer the audio chunks
                audio_buffer.append(audio_data)

                # if collected enough chunks, start playing
                if len(audio_buffer) >= buffer_size:
                    complete_audio = np.concatenate(audio_buffer)

                    # Write directly to the stream without waiting
                    stream.write(complete_audio)

                    # clear buffer for the next block
                    audio_buffer = []

            # Spiele verbleibende Audio-Chunks nach dem Empfang ab
            if audio_buffer:
                complete_audio = np.concatenate(audio_buffer)
                stream.write(complete_audio)

        # Wait a short moment to ensure all data is played before closing the stream
        sd.sleep(500)


def stream_chat_with_gpt_and_speak(client, user_input, conversation_history, chunk_size=1024):
    """Stream GPT responses and handle function calls like executing system commands."""
    assistant_reply = ""
    text_buffer = ""
    function_call_name = None
    function_call_arguments = ""

    # Start the wake-word detection in a separate thread
    wakeword_thread = threading.Thread(target=listen_for_wakeword)
    wakeword_thread.start()

    # Play audio in a separate thread
    audio_thread = threading.Thread(target=play_audio)
    audio_thread.start()

    conversation_history.append({"role": "user", "content": user_input})

    # Start GPT stream with function calling enabled
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=conversation_history,
        stream=True,
        functions=[
            {
                "name": "execute_command",
                "description": "Executes a system command on the Linux OS",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The shell command to be executed"
                        }
                    },
                    "required": ["command"]
                }
            }
        ],
        function_call="auto"  # GPT will automatically decide if a function should be called
    )

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = None

        try:
            for chunk in stream:
                if stop_flag.is_set():  # Wenn Wakeword erkannt wird
                    executor.shutdown(wait=False)
                    break

                choice = chunk.choices[0].delta

                if hasattr(choice, 'content') and choice.content is not None:
                    content = chunk.choices[0].delta.content
                    format_and_print_content(content)

                    assistant_reply += content
                    text_buffer += content

                    sentence, remaining_text = collect_until_sentence_end(text_buffer)
                    if sentence and not stop_flag.is_set():
                        future = executor.submit(process_speech, client, sentence, chunk_size)
                        text_buffer = remaining_text  # Resttext für nächste Runde behalten

                        # Prüfe, ob GPT eine Funktion aufrufen möchte
                if hasattr(choice, 'function_call') and choice.function_call is not None:
                            function_call = choice.function_call

                            # Sammle den Namen der Funktion (nur einmal)
                            if function_call_name is None and hasattr(function_call, 'name'):
                                function_call_name = function_call.name

                            # Sammle die Arguments stückweise
                            if hasattr(function_call,
                                       'arguments') and function_call.arguments is not None:
                                function_call_arguments += function_call.arguments

                            # Prüfe, ob die Arguments vollständig sind (einfacher Ansatz)
                            if function_call_arguments.endswith('}'):
                                function_call_detected = True  # Setze das Flag, um die Funktion nur einmal auszuführen

                                # Jetzt können wir die gesammelten Arguments parsen
                                try:
                                    # Entferne mögliche zusätzliche Leerzeichen
                                    arguments_str = function_call_arguments.strip()
                                    # Parsen der Arguments aus dem String
                                    import json
                                    arguments = json.loads(arguments_str)
                                    command = arguments.get('command')
                                    print('command')
                                    print(command)
                                    if command:
                                        print(f"Executing command: {command}")
                                        command_output = execute_command(command)
                                        print(f"Command output: {command_output}")

                                        # Sende die Befehlsausgabe zur weiteren Verarbeitung an ChatGPT
                                        conversation_history.append(
                                            {"role": "function", "name": function_call_name,
                                             "content": command_output})

                                        # Hole die finale Antwort von ChatGPT basierend auf der Befehlsausgabe
                                        reply = client.chat.completions.create(
                                            model="gpt-4o-mini",
                                            messages=conversation_history
                                        )
                                        assistant_reply = reply.choices[0].message.content
                                        print(assistant_reply)
                                        return assistant_reply
                                except Exception as e:
                                    print(f"Error parsing function arguments: {e}")

            if stop_flag.is_set():
                    print("Skipping future.result() due to stop flag")
            elif future:
                future.result()

        except Exception as e:
            print(f"Error encountered: {e}")

        finally:
            if stop_flag.is_set():
                executor.shutdown(wait=False)
                audio_queue.put(None)

    # Signal the end of the stream
    audio_queue.put(None)

    # Wait for the audio thread to finish
    audio_thread.join()

    # Wait for the wake-word thread to finish
    wakeword_thread.join()

    # Reset the stop_flag so the script can listen again
    stop_flag.clear()

    # Add final assistant reply to conversation history
    conversation_history.append({"role": "assistant", "content": assistant_reply})

    print('\n')

    return assistant_reply



if __name__ == "__main__":

    conversation_history.insert(0, {"role": "system", "content": "You are a helpful assistant."})

    while True:
        # Dynamically record audio until silence is detected
        audio = record_audio(sample_rate)
        save_audio_to_wav(audio, sample_rate)
        play_sound(os.path.join(script_dir, "../../resources/sounds/sent.wav"))
        # Transcribe the saved audio file using OpenAI API
        user_input = transcribe_audio(output_file)
        print(f"You: {user_input}")
        # Delete the WAV file after transcription
        delete_wav_file(output_file)

        # Stream the transcribed input to GPT and speak it in real-time
        reply = stream_chat_with_gpt_and_speak(client, user_input, conversation_history)