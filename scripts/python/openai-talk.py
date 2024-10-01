from dotenv import load_dotenv
import os
from openai import OpenAI
import sounddevice as sd
import scipy.io.wavfile as wav
import warnings

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

# Suppress the FP16 warning
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")

# Recording parameters
duration = 10  # Recording duration in seconds
sample_rate = 16000  # Standard sample rate for Whisper
output_file = "output.wav"

# List to store the conversation history
conversation_history = []


def record_audio(duration, sample_rate):
    """Record audio for the given duration."""
    #print("Recording started for 10 seconds...")
    audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
    sd.wait()  # Wait until the recording is complete
    return audio


def save_audio_to_wav(audio, sample_rate, filename=output_file):
    """Save the recorded audio to a WAV file."""
    wav.write(filename, sample_rate, audio)
    #print(f"Audio saved to: {filename}")


def transcribe_audio(audio_file_path):
    """Transcribe the audio file using OpenAI's Whisper API."""
    with open(audio_file_path, 'rb') as audio_file:
        print("Sending audio to OpenAI for transcription...")
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
        # Accessing the 'text' attribute from the transcription object
        #print(transcription)
        return transcription.text


def delete_wav_file(filename):
    """Delete the file after transcription."""
    if os.path.exists(filename):
        os.remove(filename)
       # print(f"WAV file '{filename}' deleted.")
    #else:
        #print(f"WAV file '{filename}' not found.")


def chat_with_gpt(user_input):
    """Chat with GPT using conversation history."""
    # Add the user's input to the conversation history
    conversation_history.append({"role": "user", "content": user_input})

    # Get the response from OpenAI
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",  # or "gpt-4"
        messages=conversation_history
    )

    # Extract the assistant's reply
    assistant_reply = completion.choices[0].message.content

    # Add the assistant's reply to the conversation history
    conversation_history.append({"role": "assistant", "content": assistant_reply})

    return assistant_reply


if __name__ == "__main__":
    # Optional: eine Systemnachricht hinzufügen
    conversation_history.insert(0, {"role": "system", "content": "You are a helpful assistant."})

    print("Welcome to the OpenAI Audio Chat! Say 'exit' or 'quit' to end the conversation.")

    while True:
        # Record audio once for 10 seconds
        audio = record_audio(duration, sample_rate)
        save_audio_to_wav(audio, sample_rate)

        # Transcribe the saved audio file using OpenAI API
        user_input = transcribe_audio(output_file)
        #print(f"You (transcribed): {user_input}")

        # Exit the loop if the user says 'exit' or 'quit'
        if user_input.lower() in ['exit', 'quit']:
            print("Goodbye!")
            delete_wav_file(output_file)
            break

        # Send the transcribed input to the chat_with_gpt function
        reply = chat_with_gpt(user_input)

        # Print the assistant's reply
        print(f"ChatGPT: {reply}")

        # Delete the WAV file after transcription
        delete_wav_file(output_file)