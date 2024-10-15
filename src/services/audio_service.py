import logging
import os
import queue
import subprocess
import threading
import time

import numpy as np
import scipy.io.wavfile as wav
import sounddevice as sd
import webrtcvad

from src.connectors.open_ai_connector import OpenAiConnector
from src.entities.audio_record_result import AudioRecordResult
from src.exceptions.audio_recording_failed import AudioRecordingFailed


class AudioService:
    ALLOWED_SOUND_KEYS = {"sent", "standby"}

    def __init__(
            self,
            open_ai_connector: OpenAiConnector,
            user_language="en",
            sound_theme: str = "default"
    ):
        self.vad = webrtcvad.Vad()
        self.audio_queue = queue.Queue()  # Queue für Audio-Chunks
        self.transcription_lock = threading.Lock()
        self.open_ai_connector = open_ai_connector
        self.logger = logging.getLogger(__name__)
        self.user_language = user_language
        self.sound_theme = sound_theme
        self.base_sound_path = os.path.join("resources", "sounds", "themes", self.sound_theme)

    def play_sound(self, sound_key: str) -> None:
        """Plays a sound based on the provided key."""
        if sound_key not in self.ALLOWED_SOUND_KEYS:
            self.logger.error(
                f"Sound key '{sound_key}' is not allowed! Allowed keys are: "
                f"{self.ALLOWED_SOUND_KEYS}")
            return

        file_path = os.path.join(self.base_sound_path, f"{sound_key}.wav")
        if not os.path.isfile(file_path):
            self.logger.error(
                f"Sound for key '{sound_key}' not found or file {file_path} is missing!")
            return

        try:
            subprocess.run(
                ['ffplay', '-nodisp', '-autoexit', file_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
            sd.wait()
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error while playing sound: {e}")

    def record(self) -> AudioRecordResult:
        """Record audio dynamically, start only when speech is detected, stop after 1 second of silence.
        Raises:
            AudioRecordingFailed: If no audio was captured during the recording.
        """
        audio_frames = []
        silence_duration = 0
        max_silence_duration = 1  # Stop recording after 1 second of silence
        recording_started = False  # Track if recording has started after speech detection

        sample_rate = 16000
        frame_duration_ms = 30  # Frame size in ms (must be 10, 20, or 30)
        frame_size = int(sample_rate * frame_duration_ms / 1000)

        stream = sd.InputStream(samplerate=sample_rate, channels=1, dtype='int16')
        stream.start()
        self.logger.info("Audio stream started.")

        start_time = time.time()  # start time, to observer x seconds silence

        try:
            while True:
                audio_frame, _ = stream.read(frame_size)
                audio_frames.append(audio_frame)

                # detect speech
                if self.is_speech(audio_frame, sample_rate):
                    silence_duration = 0  # Reset silence duration if speech is detected
                    if not recording_started:
                        self.logger.info("Speech detected, starting recording...")
                        recording_started = True

                # if recoring has started but 3 seconds of silence was detected
                if not recording_started and (time.time() - start_time) > 3:
                    self.logger.info("No speech detected for 3 seconds, timeout.")
                    return AudioRecordResult(success=False, silence_timeout=True)

                # silence after speech has started
                if recording_started:
                    if silence_duration > max_silence_duration:
                        self.logger.info("Silence detected, stopping recording.")
                        break  # Aufnahme beenden, wenn 1 Sekunde Stille erkannt wurde

                    # increase silence duration after speech was detected
                    silence_duration += frame_duration_ms / 1000

        finally:
            stream.stop()
            stream.close()
            self.logger.info("Audio stream stopped.")

        # somehting failed with the mic
        if not audio_frames:
            raise AudioRecordingFailed("Recording started but no audio was captured.")

        # recording was successful
        audio_array = np.concatenate(audio_frames, axis=0)
        self.logger.info("Audio recording complete.")

        return AudioRecordResult(success=True, data=audio_array)

    def is_speech(self, frame: np.ndarray, sample_rate: int, vad_mode: int = 3) -> bool:
        """Check if the audio frame contains speech using webrtcvad."""
        try:
            self.vad.set_mode(vad_mode)
            return self.vad.is_speech(frame.tobytes(), sample_rate)
        except Exception as e:
            self.logger.error(f"Error in is_speech detection: {e}")
            return False

    def simple_speak(self, text: str) -> None:
        samplerate = 24000  # Set the sample rate to match the response
        chunk_size = 1024  # Original chunk size
        buffer_size = 100  # Collect chunks before playing
        audio_buffer = []

        # Open a sounddevice stream to continuously play audio
        with sd.OutputStream(samplerate=samplerate, channels=1, dtype='int16') as stream:

            with self.open_ai_connector.client.audio.speech.with_streaming_response.create(
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

    def transcribe_audio(self, audio_file_path: str, language: str="en") -> str:
        """Transcribe the audio file using OpenAI's Whisper API."""
        try:
            with open(audio_file_path, 'rb') as audio_file:
                self.logger.info(
                    f"Sending audio to OpenAI for transcription using language {language}...")
                transcription = self.open_ai_connector.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language
                )
                return transcription.text
        except FileNotFoundError:
            self.logger.error(f"Audio file not found: {audio_file_path}")
            raise
        except Exception as e:
            self.logger.error(f"An error occurred during transcription: {e}")
            raise

    def process_speech(self, text: str) -> None:
        logging.info("Sending sentence to openAi-API to convert to audio.")
        """Konvertiert den gesamten Text in Audio und speichert es in der Queue."""
        with self.transcription_lock:
            with self.open_ai_connector.client.audio.speech.with_streaming_response.create(
                    model="tts-1",
                    voice="nova",
                    input=text,
                    response_format="pcm"
            ) as response_audio:
                logging.info("Audio of sentence received from openAi-API.")
                # Hole alle Audio-Daten auf einmal
                audio_data = np.frombuffer(response_audio.read(), dtype=np.int16)
                self.audio_queue.put(audio_data)  # Lege das gesamte Audio in die Queue

    def play_audio(self) -> None:
        """Spielt kontinuierlich Audio aus der Queue ab."""
        stream_audio = sd.OutputStream(
            samplerate=24000, channels=1, dtype='int16')
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

    def stop_audio(self) -> None:
        """Sendet ein Endsignal an die Queue, um die Wiedergabe zu stoppen."""
        self.audio_queue.put(None)

    def save_audio_to_wav(self, audio: np.ndarray, sample_rate: int, filename: str) -> None:
        """Save the recorded audio to a WAV file."""
        wav.write(filename, sample_rate, audio)

    def delete_wav_file(self, filename: str) -> None:
        if os.path.exists(filename):
            os.remove(filename)
