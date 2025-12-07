# 🗣️ Rachel AI Assistant
Ein modularer Sprach- und Text-Assistent mit ausführbaren Tools (E-Mails, Wetter, Spotify, Krypto, Web-Scraping). Läuft lokal mit Poetry oder als Docker-Container.

---

## 🚀 Was du bekommst
- 🧩 **Executors**: Wetter, E-Mail (IMAP/SMTP), Web-Scraper, Crypto, Spotify u.a.
- 🔌 **Connectors**: OpenAI, CoinGecko, Spotify, IMAP/SMTP, OpenWeatherMap.
- 🎛️ **Modi**: Voice-Mode mit Audio I/O oder Silent-Mode nur Text.
- 🐳 **Container-Ready**: Dockerfile + Compose für reproduzierbare Runs.

---

## 🧭 Architektur (kurz)
| Baustein | Rolle | Beispiele |
|----------|-------|-----------|
| **Executors** | Fachlogik pro Domäne | `WeatherExecutor`, `EmailExecutor`, `WebScraperExecutor`, `CryptoDataExecutor`, `SpotifyExecutor` |
| **Connectors** | API-Anbindung | `OpenAiConnector`, `CoinGeckoConnector`, `SpotifyConnector`, `ImapConnector`, `SmtpConnector`, `OpenWeatherMapConnector` |
| **Entry** | Startpunkt | `main.py` (Voice/Silent) |

---

## ⚡ Quick Start
1. Repo holen  
   ```bash
   git clone git@github.com:timullrich/rachel-ai.git
   cd rachel-ai
   ```
2. `.env` anlegen (siehe „Umgebungsvariablen“).
3. Wähle einen Run-Modus:
   - **Docker Compose** (kein lokales Python nötig): siehe unten.
   - **Poetry lokal**: System-Pakete + `poetry install`, siehe unten.
4. Starten:
   ```bash
   # Silent (Text only)
   python main.py --silent

   # Voice (Audio I/O)
   python main.py
   ```

---

## 🌍 Umgebungsvariablen (.env)
Mindestens:
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
Halte geheime Werte aus dem Repo (siehe `.dockerignore`/`.gitignore`).

---

## 🐳 Run mit Docker Compose
Kein lokales Python nötig; Code und `resources` werden ins Container-Workspace gemountet.

1. Image bauen (bei Code/Dependency-Änderungen erneut):
   ```bash
   docker compose build app
   ```
2. Shell starten (lädt `.env`, TTY offen):
   ```bash
   docker compose run --rm app
   ```
3. Im Container ausführen:
   ```bash
   python main.py            # oder: python main.py --silent
   ```

Dockerfile enthält Systemdeps (PortAudio, FFmpeg) und Python-Abhängigkeiten aus `requirements.txt` (Torch CPU 2.2.2 inkl.).

---

## 💻 Run lokal mit Poetry
1. System-Pakete (Debian/Ubuntu):
   ```bash
   sudo apt-get update
   sudo apt-get install python3-dev portaudio19-dev ffmpeg
   ```
2. Poetry installieren (falls fehlt):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```
3. Dependencies ziehen:
   ```bash
   poetry install
   ```
4. Shell aktivieren & starten:
   ```bash
   poetry shell
   python main.py --silent   # oder python main.py
   ```

---

## 📦 Dependency-Management
- Primär: `pyproject.toml`/`poetry.lock` (`poetry add <pkg>`).
- Docker-Build nutzt `requirements.txt` (gepinnte Liste, inkl. Torch). Bei neuen Dependencies nach Poetry-Änderungen die Datei synchron halten (`poetry export -f requirements.txt --without-hashes > requirements.txt`).
- Falls Torch-Installation hakt:
  ```bash
  pip install torch==2.2.2 --index-url https://download.pytorch.org/whl/cpu
  ```

---

## 🧪 Tests & Troubleshooting
- Tests (falls vorhanden):
  ```bash
  poetry run pytest tests/
  ```
- Häufige Stolpersteine:
  - **Audio/PortAudio fehlt**: System-Pakete nachinstallieren (`portaudio19-dev`, `ffmpeg`).
  - **API-Keys**: `.env` prüfen; falsche SMTP/IMAP-Zugangsdaten führen zu Mail-Fehlern.
  - **Docker-Langsamkeit**: bei großen Änderungen `docker compose build app` neu ausführen.
  - **Dualer Dependency-Stand**: `pyproject` vs. `requirements.txt` synchronisieren.

---

## 🧭 Nützliche Beispiele
- Silent-Mode lokal:
  ```bash
  python main.py --silent
  ```
- Wetter-Executor direkt:
  ```bash
  poetry run python -m src.weather_executor --city_name "Berlin"
  ```

---

Made with ⚙️ + ☕
