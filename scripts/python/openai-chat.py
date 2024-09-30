from dotenv import load_dotenv
import os
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Set your OpenAI API key here
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

# List to store the conversation history
conversation_history = []

def chat_with_gpt(user_input):
    # Add the user's input to the conversation history
    conversation_history.append({"role": "user", "content": user_input})

    # Get the response from OpenAI
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",  # oder "gpt-4"
        messages=conversation_history
    )

    # Extract the assistant's reply
    assistant_reply = completion.choices[0].message.content  # Hier wird der Inhalt korrekt abgerufen

    # Add the assistant's reply to the conversation history
    conversation_history.append({"role": "assistant", "content": assistant_reply})

    return assistant_reply

if __name__ == "__main__":
    # Optional: eine Systemnachricht hinzufügen
    conversation_history.insert(0, {"role": "system", "content": "You are a helpful assistant."})

    print("Welcome to the OpenAI Chat! Type 'exit' or 'quit' to end the conversation.")
    while True:
        # Get user input
        user_input = input("You: ")

        # Exit the loop if the user types 'exit' or 'quit'
        if user_input.lower() in ['exit', 'quit']:
            print("Goodbye!")
            break

        # Send the user input to the chat_with_gpt function
        reply = chat_with_gpt(user_input)

        # Print the assistant's reply
        print(f"ChatGPT: {reply}")