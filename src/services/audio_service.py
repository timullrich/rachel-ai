# Standard library imports
import concurrent.futures
import datetime
import io
import logging
import os
import queue
import re
import subprocess
import threading
import time
import wave
from typing import Any, Optional, Tuple

# Third-party imports
import numpy as np
from numpy import ndarray
import sounddevice as sd
import webrtcvad

# Local application imports
from src.connectors import OpenAiConnector
from src.entities import AudioRecordResult
from src.exceptions import AudioRecordingFailed, AudioTranscriptionFailed


class AudioService:
    """
    The AudioService class handles recording audio with speech detection,
    converting text to speech using OpenAI, playing audio from a queue,
    and transcribing recorded audio using OpenAI's Whisper API. It also
    manages audio playback, processes audio in real-time, and handles
    sound themes for different notifications.
    """

    ALLOWED_SOUND_KEYS = {"sent", "standby"}

    def __init__(
            self,
            open_ai_connector: OpenAiConnector,
            user_language: str = "en",
            sound_theme: str = "default",
    ) -> None:
        """
        Initializes the AudioService class with the necessary dependencies.

        :param open_ai_connector: An instance of OpenAiConnector for interacting with OpenAI's API.
        :param user_language: The language in which audio interactions should occur (default: 'en').
        :param sound_theme: The theme for sound notifications (default: 'default').
        """

        self.vad = webrtcvad.Vad()
        self.audio_queue: queue.Queue[np.ndarray] = queue.Queue()
        self.transcription_lock = threading.Lock()
        self.open_ai_connector = open_ai_connector
        self.logger = logging.getLogger(self.__class__.__name__)
        self.user_language = user_language
        self.sound_theme = sound_theme
        self.base_sound_path = os.path.join(
            "resources", "sounds", "themes", self.sound_theme
        )

    def play_sound(self, sound_key: str) -> None:
        """Plays a sound based on the provided key."""

        # Validate sound_key
        if sound_key not in self.ALLOWED_SOUND_KEYS:
            error_message = (
                f"Invalid sound key '{sound_key}'! "
                f"Allowed keys are: {self.ALLOWED_SOUND_KEYS}"
            )
            self.logger.error(error_message)
            raise ValueError(error_message)  # Raise an exception for invalid sound_key

        file_path = os.path.join(self.base_sound_path, f"{sound_key}.wav")

        # Validate file existence
        if not os.path.isfile(file_path):
            error_message = f"Sound file '{file_path}' not found for key '{sound_key}'!"
            self.logger.error(error_message)
            raise FileNotFoundError(
                error_message
            )  # Raise an exception if file is missing

        try:
            # Play sound using ffplay
            subprocess.run(
                ["ffplay", "-nodisp", "-autoexit", file_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error while playing sound '{sound_key}': {e}")
            raise

    def record(
            self,
            sample_rate: int = 16000,
            frame_duration_ms: int = 30,
            max_silence_duration: float = 1.0,
    ) -> AudioRecordResult:
        """
        Records audio dynamically, starting only when speech is detected,
        and stopping after 1 second of silence.

        Raises:
            AudioRecordingFailed: If no audio was captured during the recording.

        :param sample_rate: The sample rate for audio recording (default: 16000 Hz).
        :param frame_duration_ms: Frame size in milliseconds
                    (must be 10, 20, or 30, default: 30 ms).
        :param max_silence_duration: Duration in seconds after which recording stops when no
                    speech is detected (default: 1 second).
        :return: AudioRecordResult containing success state and the recorded audio data.
        """

        audio_frames = []
        silence_duration = 0
        recording_started = False
        frame_size = int(sample_rate * frame_duration_ms / 1000)

        # Using a context manager to ensure resources are properly managed
        with sd.InputStream(
                samplerate=sample_rate, channels=1, dtype="int16"
        ) as stream:
            self.logger.info("Audio stream started.")
            start_time = time.time()  # Track the start time to handle silence timeouts

            try:
                while True:
                    audio_frame, _ = stream.read(frame_size)
                    audio_frames.append(audio_frame)

                    # Detect speech in the current audio frame
                    if self.is_speech(audio_frame, sample_rate):
                        silence_duration = 0  # Reset silence if speech is detected
                        if not recording_started:
                            self.logger.info("Speech detected, starting recording...")
                            recording_started = True

                    # Handle timeout when no speech is detected
                    if not recording_started and (time.time() - start_time) > 3:
                        self.logger.info("No speech detected for 3 seconds, timeout.")
                        return AudioRecordResult(success=False, silence_timeout=True)

                    # Stop recording after 1 second of silence
                    if recording_started:
                        if silence_duration > max_silence_duration:
                            self.logger.info("Silence detected, stopping recording.")
                            break  # Stop the recording

                        silence_duration += (
                                frame_duration_ms / 1000
                        )  # Increase silence duration

            finally:
                self.logger.info("Audio stream stopped.")

        # Handle the case where no audio was captured
        if not audio_frames:
            self.logger.error("Recording started but no audio was captured.")
            raise AudioRecordingFailed("Recording started but no audio was captured.")

        # Recording was successful, concatenate the frames
        audio_array = np.concatenate(audio_frames, axis=0)
        self.logger.info(
            f"Audio recording complete with {len(audio_frames)} frames captured."
        )

        return AudioRecordResult(success=True, data=audio_array)

    def is_speech(self, frame: np.ndarray, sample_rate: int, vad_mode: int = 3) -> bool:
        """
        Check if the audio frame contains speech using webrtcvad.

        :param frame: The audio frame (NumPy array) to be checked for speech.
        :param sample_rate: The sample rate of the audio in Hz
                    (must be 8000, 16000, 32000, or 48000).
        :param vad_mode: Sensitivity of the VAD (Voice Activity Detection).
                         0 = most restrictive, 3 = most permissive. Default is 3.
        :return: True if speech is detected, otherwise False.
        :raises ValueError: If vad_mode is outside the range [0, 3].
        """

        # Validate vad_mode
        if not 0 <= vad_mode <= 3:
            self.logger.error(
                f"Invalid vad_mode: {vad_mode}. It must be between 0 and 3."
            )
            raise ValueError(f"Invalid vad_mode: {vad_mode}. Must be between 0 and 3.")

        try:
            self.vad.set_mode(vad_mode)
            # Convert the frame to bytes because webrtcvad expects raw PCM bytes
            is_speech_detected = self.vad.is_speech(frame.tobytes(), sample_rate)
            return is_speech_detected
        except Exception as e:
            self.logger.error(f"Error in is_speech detection: {e}")
            return False

    def transcribe_audio(
            self, record_result: AudioRecordResult, language: str, sample_rate: int = 16000
    ) -> str:
        """
        Transcribes the recorded audio data using OpenAI's Whisper API.

        :param record_result: An instance of AudioRecordResult containing the recorded audio data.
        :param language: The language of the audio to be transcribed. Must be supported
                            by the Whisper API.
        :param sample_rate: The sample rate for the audio recording. Default is 16000 Hz.
        :return: The transcribed text as a string.
        :raises AudioTranscriptionFailed: If no valid audio data is available or
                                            if transcription fails.
        """

        if not record_result.success or record_result.data is None:
            raise AudioTranscriptionFailed("No valid audio data to transcribe.")

        try:
            # Create a BytesIO buffer to hold the audio data in memory
            audio_buffer = io.BytesIO()

            # Write the NumPy audio data into the buffer as WAV using the 'wave' module
            with wave.open(audio_buffer, "wb") as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit Audio (2 Bytes)
                wav_file.setframerate(
                    sample_rate
                )  # Use the sample rate passed as a parameter
                wav_file.writeframes(record_result.data.tobytes())

            # Reset the buffer position to the beginning
            audio_buffer.seek(0)

            # Log information about the transcription process
            self.logger.info(
                f"Sending audio to OpenAI for transcription"
                f" (language: {language}, duration: {len(record_result.data)} samples)..."
            )

            # Send the audio file as a tuple with a filename, file content, and MIME type to the API
            transcription = self.open_ai_connector.client.audio.transcriptions.create(
                model="whisper-1",
                file=("audio.wav", audio_buffer, "audio/wav"),
                # Filename, file content, and MIME type
                language=language,
            )

            # Check if transcription contains text
            if not transcription or not hasattr(transcription, "text"):
                self.logger.error(
                    f"Transcription failed: No text in response from API."
                )
                raise AudioTranscriptionFailed(
                    "Transcription failed: No text returned from API."
                )

            return transcription.text

        except Exception as e:
            self.logger.error(f"An error occurred during transcription: {e}")
            raise AudioTranscriptionFailed(f"Transcription failed due to: {e}")

    def process_speech(self, text: str) -> None:
        """
        Converts the given text into audio using OpenAI's text-to-speech (TTS) API
        and stores the resulting audio data in the audio queue.

        :param text: The text to be converted into speech.
        :raises: Raises an exception if the TTS process fails.
        """
        self.logger.info(
            f"Sending sentence to OpenAI API to convert to audio "
            f"(text length: {len(text)} characters)."
        )

        try:
            with self.transcription_lock:
                # Request OpenAI TTS API to convert the text to audio
                with self.open_ai_connector.client.audio.speech.with_streaming_response.create(
                        model="tts-1", voice="nova", input=text, response_format="pcm"
                ) as response_audio:
                    self.logger.info("Audio of sentence received from OpenAI API.")

                    # Convert the audio response to a NumPy array
                    audio_data: ndarray = np.frombuffer(response_audio.read(), dtype=np.int16)
                    self.logger.info(
                        f"Received audio data (size: {audio_data.size} samples)."
                    )

                    # Store the audio data in the queue
                    self.audio_queue.put(audio_data)
                    self.logger.info("Audio processing completed and added to queue.")

        except Exception as e:
            # Log the error with more details
            self.logger.error(f"Error occurred during speech processing: {e}")
            # Add an empty numpy array as an end signal
            self.audio_queue.put(np.array([], dtype=np.int16))
            raise AudioTranscriptionFailed(f"Failed to process speech due to: {e}")

    def play_audio(self, samplerate: int = 24000, channels: int = 1) -> None:
        """
        Continuously plays audio data from the queue using the specified sample
        rate and channel count. Playback ends when an empty audio signal (size 0) is
        received in the queue.

        :param samplerate: The sample rate to use for audio playback (default: 24000 Hz).
        :param channels: The number of audio channels (default: 1).
        """
        self.logger.info(
            f"Starting audio playback with samplerate={samplerate}, channels={channels}."
        )

        try:
            with sd.OutputStream(
                    samplerate=samplerate, channels=channels, dtype="int16"
            ) as stream_audio:
                self.logger.info("Audio stream started.")

                while True:
                    # Blocks until audio data is available in the queue
                    audio_data = self.audio_queue.get()

                    # Check for the end signal (empty array)
                    if audio_data.size == 0:
                        self.logger.info(
                            "Received end signal, stopping audio playback."
                        )
                        break

                    # Write audio data to the output stream
                    stream_audio.write(audio_data)
                    self.logger.debug(
                        f"Played audio chunk of size {audio_data.size} samples."
                    )

        except Exception as e:
            self.logger.error(f"Error occurred during audio playback: {e}")

        finally:
            self.logger.info("Audio playback finished and stream closed.")
            sd.wait()  # Ensure all audio buffers are played

    def collect_until_sentence_end(
            self, text_buffer: str, in_code_block: bool = False
    ) -> Tuple[str, str, bool]:
        """
        Collects text from the buffer until a sentence-ending punctuation (., !, ?) is detected.
        Handles code blocks by ignoring sentence-ending punctuation within them.

        :param text_buffer: The input text buffer containing sentences.
        :param in_code_block: Flag indicating if currently inside a code block.
        :return: A tuple where the first element is the sentence up to the punctuation mark,
                 the second element is the remaining text after the punctuation mark,
                 and the third element is the updated code block flag.
        """
        # Apply special content parsing to handle links and code
        processed_text, code_block_open = self.parse_special_content(
            text_buffer, in_code_block
        )

        # Update the code block status
        in_code_block = in_code_block or code_block_open

        # If inside a code block, skip sentence detection
        if in_code_block:
            # Check if the code block closes within the current buffer
            if re.search(r"```", processed_text):
                in_code_block = False  # End of code block
            return "", processed_text, in_code_block

        # Regex to detect sentence-ending punctuation followed by a space or end of text
        match = re.search(r"[.!?](?=\s|$)", processed_text)

        if match:
            # Return the sentence and the remaining text
            sentence = processed_text[: match.end()]
            remaining_text = processed_text[match.end():]
            self.logger.debug(
                f"Detected sentence end. Sentence: '{sentence}', Remaining: '{remaining_text}'"
            )
            return sentence.strip(), remaining_text.strip(), in_code_block

        # No sentence-ending punctuation found
        self.logger.debug(
            f"No sentence end detected. Returning entire buffer: '{text_buffer}'"
        )
        return "", text_buffer, in_code_block

    def parse_special_content(self, text: str, in_code_block: bool) -> Tuple[str, bool]:
        """
        Parse the text to replace links, identify code blocks, and handle numbers and dates.
        :param text: The input text that may contain links, code snippets, numbers, and dates.
        :param in_code_block: A flag indicating if currently inside a code block.
        :return: A tuple containing the modified text and a boolean indicating if inside a
                code block.
        """
        # Handle links in Markdown format [Text](URL)
        text = re.sub(
            r"\[([^]]+)]\((https?://[^\s]+?)\)",
            r"\1 (Den Link findest du in der Textausgabe.)",
            text,
        )

        # Check for the start or end of a code block with triple backticks ```
        if in_code_block:
            end_match = re.search(r"```", text)
            if end_match:
                text = (
                        "Den Quellcode findest du in der Textausgabe."
                        + text[end_match.end():]
                )
                in_code_block = False
            else:
                text = "Den Quellcode findest du in der Textausgabe."
        else:
            start_match = re.search(r"```", text)
            if start_match:
                end_match = re.search(r"```", text[start_match.end():])
                if end_match:
                    text = (
                            text[: start_match.start()]
                            + "Den Quellcode findest du in der Textausgabe."
                            + text[start_match.end() + end_match.end():]
                    )
                else:
                    text = (
                            text[: start_match.start()]
                            + "Den Quellcode findest du in der Textausgabe."
                    )
                    in_code_block = True

        # Replace inline code with double backticks (but ignore single backticks)
        if not in_code_block:
            text = re.sub(
                r"``[^`]+``", "Den Quellcode findest du in der Textausgabe.", text
            )

        # Skip numbers in prices like "66.842 USD" to leave them as is
        text = self.skip_price_numbers(text)

        # Replace remaining numerals with written numbers
        # text = self.convert_numbers_to_words(text)

        # Replace dates like "23.10.2024"
        # text = self.convert_dates_to_words(text)

        return text, in_code_block

    def skip_price_numbers(self, text: str) -> str:
        """
        Leave prices (e.g., '66.842 USD') unchanged for TTS.
        :param text: The input text containing prices.
        :return: The modified text with prices preserved.
        """
        # Match prices with pattern 'X.XXX USD' or 'XX,XXX EUR' and keep them unchanged
        return re.sub(r"\b\d{1,3}(?:[.,]\d{3})* (USD|EUR)\b", lambda m: m.group(), text)

    def convert_numbers_to_words(self, text: str) -> str:
        """
        Replace numerical values with their written forms, excluding already formatted prices.
        :param text: The input text containing numbers.
        :return: The modified text with numbers written out.
        """
        # Map of numbers to words
        numbers_map = {
            "0": "null",
            "1": "eins",
            "2": "zwei",
            "3": "drei",
            "4": "vier",
            "5": "fünf",
            "6": "sechs",
            "7": "sieben",
            "8": "acht",
            "9": "neun",
        }

        def number_to_word(match):
            num_str = match.group()
            return " ".join(
                numbers_map[digit] for digit in num_str if digit in numbers_map
            )

        # Replace isolated numbers
        return re.sub(r"\b\d+\b", number_to_word, text)

    def convert_dates_to_words(self, text: str) -> str:
        """
        Replace date formats (e.g., DD.MM.YYYY) with spoken forms.
        :param text: The input text containing dates.
        :return: The modified text with dates written out.
        """

        def date_to_words(match):
            date_str = match.group()
            try:
                # Parse the date string
                date_obj = datetime.datetime.strptime(date_str, "%d.%m.%Y")
                day = date_obj.day
                month = date_obj.strftime("%B")  # Get full month name
                year = date_obj.year
                # Convert day and year to words
                return f"{day}. {month} {year}"
            except ValueError:
                return date_str  # If parsing fails, return the original string

        # Replace dates in the format DD.MM.YYYY
        return re.sub(r"\b\d{2}\.\d{2}\.\d{4}\b", date_to_words, text)

    def play_stream_audio(
            self, stream: Any, samplerate: int = 24000, channels: int = 1
    ) -> None:
        """
        Stream GPT responses, convert them into speech, and play the audio in a separate thread.
        This method handles streaming text, detecting sentence boundaries, and converting
        the text to audio using the process_speech method. It also manages the audio playback
        by running an audio thread and sending stop signals when finished.

        :param stream: The GPT response stream to be processed.
        :param samplerate: The sample rate for the audio playback (default: 24000 Hz).
        :param channels: The number of audio channels for playback (default: 1).
        """

        # Start the audio thread (playing responses)
        self.logger.info("Starting audio thread for playing GPT responses.")
        audio_thread: threading.Thread = threading.Thread(
            target=self.play_audio, args=(samplerate, channels)
        )
        audio_thread.start()

        # Initialize buffers for processing the stream
        text_buffer: str = ""
        assistant_reply: str = ""

        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future: Optional[concurrent.futures.Future] = None
                in_code_block = False
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        content: str = chunk.choices[0].delta.content

                        assistant_reply += content
                        text_buffer += content

                        # Sentence detection and start speech processing
                        sentence, remaining_text, in_code_block = (
                            self.collect_until_sentence_end(text_buffer, in_code_block)
                        )
                        if sentence:
                            self.logger.debug(
                                f"Detected sentence: '{sentence}'. "
                                f"Submitting for speech processing."
                            )
                            future = executor.submit(self.process_speech, sentence)
                            text_buffer = remaining_text

                # Process remaining text (if no complete sentence)
                if text_buffer:
                    self.logger.debug(f"Processing remaining text: '{text_buffer}'")
                    future = executor.submit(self.process_speech, text_buffer)

                # Ensure that the last submitted future is completed
                if future:
                    self.logger.debug(
                        "Waiting for the last speech processing task to finish."
                    )
                    future.result()

        except Exception as e:
            self.logger.error(f"Error occurred while processing stream: {e}")

        finally:
            # Signal the end of the audio stream and stop the audio thread
            self.logger.info("Sending stop signal to audio thread.")
            self.stop_audio()

            # Wait until the audio thread finishes
            audio_thread.join()
            self.logger.info("Audio thread finished.")

    def stop_audio(self) -> None:
        """
        Sends an end signal (empty np.ndarray) to the audio queue to stop the playback.
        This signal is recognized by the play_audio method, which will stop the audio stream
        once the empty array is received.
        """
        try:
            # Send an empty np.ndarray as a stop signal to the audio queue
            self.audio_queue.put(np.array([], dtype=np.int16))
            self.logger.info("Stop signal sent to audio queue.")
        except Exception as e:
            self.logger.error(
                f"Error occurred while sending stop signal to audio queue: {e}"
            )
            raise
