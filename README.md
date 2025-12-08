# 🗣️ Rachel AI Assistant
Modular voice/text assistant with executors for email, weather, Spotify, crypto, web scraping, and more. Runs entirely inside Docker to keep the host clean.

---

## 🚀 Highlights
- 🧩 Executors for weather, email (IMAP/SMTP), web, crypto, Spotify
- 🔌 Connectors for OpenAI, CoinGecko, Spotify, IMAP/SMTP, OpenWeatherMap
- 🎛️ Modes: voice (audio I/O) and silent (text only)
- 🐳 Docker-only workflow; no host Python setup required

---

## 🧭 Architecture (short)
| Component | Role | Examples |
|-----------|------|----------|
| Executors | Domain logic | `WeatherExecutor`, `EmailExecutor`, `WebScraperExecutor`, `CryptoDataExecutor`, `SpotifyExecutor` |
| Connectors | API access | `OpenAiConnector`, `CoinGeckoConnector`, `SpotifyConnector`, `ImapConnector`, `SmtpConnector`, `OpenWeatherMapConnector` |
| Entry | Start point | `main.py` (voice/silent) |

---

## ⚡ Quick Start (Docker only)
1. Clone  
   ```bash
   git clone git@github.com:timullrich/rachel-ai.git
   cd rachel-ai
   ```
2. Create `.env` from template  
   ```bash
   cp .env-example .env
   # fill in your keys/secrets
   ```
3. Build image  
   ```bash
   docker compose build app
   ```
4. Start a container shell  
   ```bash
   docker compose run --rm app
   ```
5. Run inside the container  
   ```bash
   python main.py --silent   # text only
   # or
   python main.py            # voice with audio I/O
   ```

---

## 🌍 Environment (.env)
```env
PLATFORM=mac-os
OPENAI_API_KEY=your-api-key
PORCUPINE_ACCESS_KEY=your-api-key

LOG_LEVEL=INFO
USER_LANGUAGE=en
SOUND_THEME=default
USERNAME=your-name

SMTP_SERVER=smtp.example.com
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
Secrets stay out of Git (`.env` is ignored).

---

## 🐳 Docker workflow
- Build (repeat after code/dependency changes):  
  ```bash
  docker compose build app
  ```
- Work inside:  
  ```bash
  docker compose run --rm app
  python main.py --silent  # or python main.py
  ```
- Volumes: project code and `resources` are mounted; edits are live.
- Base image: `python:3.12-slim` with PortAudio + FFmpeg; Python deps from `requirements.txt` (Torch CPU 2.2.2 included).

---

## 📦 Dependency management
- Single source: `requirements.txt`.
- To add a package (inside container or local venv):  
  ```bash
  pip install <pkg>
  pip freeze | grep <pkg> >> requirements.txt   # or edit file to pin version
  ```
- Torch already pinned (`torch==2.2.2` via CPU index). If install fails:  
  ```bash
  pip install torch==2.2.2 --index-url https://download.pytorch.org/whl/cpu
  ```
- Rebuild after dependency changes: `docker compose build app`.

---

## 🧪 Tests & troubleshooting
- Run tests (if present):  
  ```bash
  docker compose run --rm app python -m pytest tests/
  ```
- Common issues:
  - API keys: verify `.env`; wrong SMTP/IMAP creds cause mail failures.
  - Audio/PortAudio: bundled in image; if running outside Docker, install system packages.
  - Slow starts after dep changes: rebuild the image.

---

## 🧭 Handy commands
- Silent mode:  
  ```bash
  docker compose run --rm app python main.py --silent
  ```
- Voice mode:  
  ```bash
  docker compose run --rm app python main.py
  ```
- Weather executor:  
  ```bash
  docker compose run --rm app python -m src.weather_executor --city_name "Berlin"
  ```

---

Made with ⚙️ + ☕
