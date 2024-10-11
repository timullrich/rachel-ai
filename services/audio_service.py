import logging
import sounddevice as sd
import queue
import threading
import subprocess
import os
import time
import sys
import itertools
import webrtcvad
import numpy as np
import scipy.io.wavfile as wav

class SilenceDetection(Exception):
    """Exception raised when no speech is detected within a specified time."""
    pass

class AudioService:
    def __init__(self, open_ai_client):
        self.audio_queue = queue.Queue()  # Queue für Audio-Chunks
        self.transcription_lock = threading.Lock()
        self.open_ai_client = open_ai_client

        self.logger = logging.getLogger(__name__)

    def play_sound(self, file_path):
        if not os.path.isfile(file_path):
            self.logger.error(f"File {file_path} not found!")
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
            self.logger.error(f"Error while playing sound: {e}")

    def record(self):
        """Record audio dynamically, stop when no speech is detected."""
        audio_frames = []
        silence_duration = 0
        max_silence_duration = 1  # Stop recording after 1 second of silence
        recording_started = False  # Track if recording has started after speech detection

        # Rotating spinner for visual feedback
        spinner = itertools.cycle(['-', '\\', '|', '/'])

        sample_rate = 16000
        frame_duration_ms = 30  # Frame size in ms (must be 10, 20, or 30)
        frame_size = int(sample_rate * frame_duration_ms / 1000)

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
                if self.is_speech(audio_frame, sample_rate):
                    silence_duration = 0  # Reset silence duration if speech detected

                    if not recording_started:
                        self.logger.info("Speech detected, starting recording...")

                        recording_started = True  # Start recording after speech is detected

                # Check if 5 seconds have passed without starting the recording
                if not recording_started and (time.time() - start_time) > 4:
                    self.logger.info("No speech detected for 4 seconds...")
                    raise SilenceDetection

                else:
                    if recording_started:
                        if silence_duration < max_silence_duration:
                            silence_duration += frame_duration_ms / 1000  # Count silence only after speech starts

                # If too much silence is detected after recording started, stop recording
                if recording_started and silence_duration > max_silence_duration:
                    self.logger.info("Silence detected, stopping recording.")
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

    def is_speech(self, frame, sample_rate):
        """Check if the audio frame contains speech using webrtcvad."""
        vad = webrtcvad.Vad()
        vad.set_mode(3)  # 0 = aggressive, 3 = least aggressive

        return vad.is_speech(frame.tobytes(), sample_rate)

    def simple_speak(self, text):
        samplerate = 24000  # Set the sample rate to match the response
        chunk_size = 1024  # Original chunk size
        buffer_size = 100  # Collect chunks before playing
        audio_buffer = []

        # Open a sounddevice stream to continuously play audio
        with sd.OutputStream(samplerate=samplerate, channels=1, dtype='int16') as stream:

            with self.open_ai_client.audio.speech.with_streaming_response.create(
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

            sd.wait()

    def transcribe_audio(self, audio_file_path):
        """Transcribe the audio file using OpenAI's Whisper API."""
        with open(audio_file_path, 'rb') as audio_file:
            self.logger.info("Sending audio to OpenAI for transcription...")
            transcription = self.open_ai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            return transcription.text

    def process_speech(self, text):
        """Konvertiert den gesamten Text in Audio und speichert es in der Queue."""
        with self.transcription_lock:
            with self.open_ai_client.audio.speech.with_streaming_response.create(
                    model="tts-1",
                    voice="nova",
                    input=text,
                    response_format="pcm"
            ) as response_audio:
                # Hole alle Audio-Daten auf einmal
                audio_data = np.frombuffer(response_audio.read(), dtype=np.int16)
                self.audio_queue.put(audio_data)  # Lege das gesamte Audio in die Queue

    def play_audio(self):
        """Spielt kontinuierlich Audio aus der Queue ab."""
        stream_audio = sd.OutputStream(samplerate=24000, channels=1, dtype='int16')
        stream_audio.start()

        while True:
            audio_data = self.audio_queue.get()  # Blockiert, bis ein Item verfügbar ist
            if audio_data is None:  # Endsignal
                break
            stream_audio.write(audio_data)  # Audio-Daten in den Stream schreiben
            sd.wait()

        stream_audio.stop()
        stream_audio.close()
        sd.wait()

    def stop_audio(self):
        """Sendet ein Endsignal an die Queue, um die Wiedergabe zu stoppen."""
        self.audio_queue.put(None)

    def save_audio_to_wav(self, audio, sample_rate, filename):
        """Save the recorded audio to a WAV file."""
        wav.write(filename, sample_rate, audio)

    def delete_wav_file(self, filename):
        if os.path.exists(filename):
            os.remove(filename)