
# Rachel AI Project
Script Collection for the Rachel AI assistant project, designed to manage various tasks through modular executors.

## Project Overview

Rachel AI is a versatile AI assistant project designed to perform a variety of tasks using custom executors.
Each executor serves a specific function, such as weather retrieval, email management, and web scraping.
Rachel AI leverages OpenAI’s API to interact and respond to user commands, making it a powerful tool for both
personal and professional use.

## Technical Architecture

The project is structured in a modular manner:
- **Executors**: Perform specific tasks. For example:
    - `WeatherExecutor`: Retrieves weather information.
    - `EmailExecutor`: Manages email operations such as sending, listing, and deleting emails.
    - `WebScraperExecutor`: Scrapes web content for information retrieval.
    - `CryptoDataExecutor`: Fetches cryptocurrency market data and trends.
    - `SpotifyExecutor`: Interacts with Spotify API to manage playlists, search for tracks, and control playback.
- **Connectors**: Interface with external APIs to fetch data. Key connectors include:
    - `OpenAiConnector`: Connects with OpenAI's API for generating responses.
    - `CoinGeckoConnector`: Connects to CoinGecko for cryptocurrency data.
    - `SpotifyConnector`: Manages Spotify API connection for music and playback control.
    - `ImapConnector` and `SmtpConnector`: Handle email operations by connecting to IMAP and SMTP servers.
    - `OpenWeatherMapConnector`: Retrieves weather data from the OpenWeatherMap API.

Each component communicates through well-defined interfaces, ensuring modularity and maintainability.

## Project Setup with Poetry

This project uses [Poetry](https://python-poetry.org/) for dependency management and environment setup. Poetry ensures
consistent package management across environments.

### Prerequisites

Ensure you have Poetry installed before proceeding. You can install it using:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### System Dependencies

Install the following system dependencies for a smooth setup:

#### Debian-based Systems (e.g., Ubuntu, Raspbian)

```bash
sudo apt-get update
sudo apt-get install python3-dev portaudio19-dev ffmpeg
```

**Dependency Descriptions**:
- **`python3-dev`**: Contains header files and development libraries required to compile Python extensions.
- **`portaudio19-dev`**: Provides the necessary components for the `sounddevice` library, which is used for audio processing.
- **`ffmpeg`**: Required for handling audio processing within the project.

After installing system dependencies, set up the project with Poetry:

```bash
poetry install
```

If you encounter any issues, check error messages and ensure all system libraries are installed.

## Environment Variables

This project uses environment variables for configuration. These should be defined in a `.env` file in the root directory.
Here are the environment variables required:

```plaintext
PLATFORM=mac-os
OPENAI_API_KEY=your-api-key
PORCUPINE_ACCESS_KEY=your-api-key

LOG_LEVEL=INFO
USER_LANGUAGE=en
SOUND_THEME=default

USERNAME=your-name

SMTP_SERVER=smtp.example.com"
SMTP_USER=your-email@example.com
SMTP_PASSWORD=your-password
IMAP_SERVER=imap.example.com
IMAP_USER=your-email@example.com
IMAP_PASSWORD=your-password

OPEN_WEATHER_MAP_API_KEY=your-open-weather-map-api-key

SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=your_redirect_uri
```

**Note**: Ensure these environment variables are correctly set before running the application.

## How to Use

1. **Clone the repository**:

   ```bash
   git clone git@github.com:timullrich/rachel-ai.git
   cd rachel-ai
   ```

2. **Install dependencies**:

   After cloning, install all required dependencies:

   ```bash
   poetry install
   ```

   This command will create a virtual environment and install dependencies from the `pyproject.toml` file.

3. **Activate the virtual environment**:

   To activate the Poetry-created environment, use:

   ```bash
   poetry shell
   ```

4. **Run the project**:

   - **Silent Mode** (text input/output only):

     ```bash
     python main.py --silent
     ```

   - **Voice Mode** (with speech interaction):

     ```bash
     python main.py
     ```

   This flexibility allows you to either interact with Rachel AI via text or use voice commands.

## Adding Dependencies

Add new dependencies using Poetry:

```bash
poetry add <package_name>
```

This command updates the `pyproject.toml` and `poetry.lock` files.

## Deactivating the Environment

To exit the Poetry shell:

```bash
exit
```

## Manual Installation of PyTorch

If automatic installation fails, install PyTorch manually:

```bash
pip install torch==2.2.2 --index-url https://download.pytorch.org/whl/cpu
```

## Example Usage

Here’s an example of retrieving current weather data:

```bash
poetry run python -m src.weather_executor --city_name "Berlin"
```

This command fetches the current weather information for Berlin.

## Testing and Troubleshooting

Run unit tests to verify that executors and services function as expected:

```bash
poetry run pytest tests/
```

### Troubleshooting Tips
- **Dependency Errors**: Re-run `poetry install` and verify all system dependencies are installed.
- **Connection Issues**: Check that all API keys in the `.env` file are correct and active.
- **Email and API Errors**: Ensure that email and other API configurations match expected formats.

---

This README provides the necessary information to set up, configure, and use the Rachel AI project. For further details,
refer to the docstrings within each module.
