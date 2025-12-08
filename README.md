# 🗣️ Rachel AI Assistant
Modularer Sprach- und Text-Assistent mit ausführbaren Tools (E-Mail, Wetter, Spotify, Krypto, Web-Scraping). Läuft komplett im Docker-Container – Host bleibt sauber.

---

## 🚀 Was du bekommst
- 🧩 **Executors**: Wetter, E-Mail (IMAP/SMTP), Web-Scraper, Crypto, Spotify u.a.
- 🔌 **Connectors**: OpenAI, CoinGecko, Spotify, IMAP/SMTP, OpenWeatherMap.
- 🎛️ **Modi**: Voice-Mode mit Audio I/O oder Silent-Mode nur Text.
- 🐳 **Container-Ready**: Dockerfile + Compose; keine lokale Python-Installation nötig.

---

## 🧭 Architektur (kurz)
| Baustein | Rolle | Beispiele |
|----------|-------|-----------|
| **Executors** | Fachlogik pro Domäne | `WeatherExecutor`, `EmailExecutor`, `WebScraperExecutor`, `CryptoDataExecutor`, `SpotifyExecutor` |
| **Connectors** | API-Anbindung | `OpenAiConnector`, `CoinGeckoConnector`, `SpotifyConnector`, `ImapConnector`, `SmtpConnector`, `OpenWeatherMapConnector` |
| **Entry** | Startpunkt | `main.py` (Voice/Silent) |

---

## ⚡ Quick Start (Docker-only)
1. Repo holen  
   ```bash
   git clone git@github.com:timullrich/rachel-ai.git
   cd rachel-ai
   ```
2. `.env` aus Vorlage anlegen  
   ```bash
   cp .env-example .env
   # Werte einsetzen (siehe unten)
   ```
3. Image bauen  
   ```bash
   docker compose build app
   ```
4. Container-Shell starten  
   ```bash
   docker compose run --rm app
   ```
5. Im Container ausführen  
   ```bash
   python main.py --silent   # Text only
   # oder
   python main.py            # Voice mit Audio I/O
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
Geheimnisse bleiben außerhalb des Repos (`.env` ist in `.gitignore`/`.dockerignore`).

---

## 🐳 Docker-Workflow
- Build (bei Code- oder Dependency-Änderungen erneut):
  ```bash
  docker compose build app
  ```
- Arbeiten im Container:
  ```bash
  docker compose run --rm app
  # danach: python main.py oder python main.py --silent
  ```
- Volumes: Code + `resources` sind gemountet, Änderungen sind direkt sichtbar.
- Base-Image: `python:3.12-slim` mit Systemdeps (PortAudio, FFmpeg) und Python-Abhängigkeiten aus `requirements.txt` (Torch CPU 2.2.2 inkl.).

---

## 📦 Dependency-Management
- Single Source: `requirements.txt` (gepinnte Liste für Docker).
- Neues Paket hinzufügen (im Container oder lokal):
  ```bash
  pip install <pkg>
  pip freeze | grep <pkg> >> requirements.txt   # oder manuell Version ergänzen
  ```
- Torch ist bereits pinnt (`torch==2.2.2` via CPU-Index). Falls Installation hakt:
  ```bash
  pip install torch==2.2.2 --index-url https://download.pytorch.org/whl/cpu
  ```
- Nach Änderungen an `requirements.txt` neu bauen: `docker compose build app`.

---

## 🧪 Tests & Troubleshooting
- Tests (falls vorhanden):
  ```bash
  docker compose run --rm app python -m pytest tests/
  ```
- Häufige Stolpersteine:
  - **API-Keys**: `.env` prüfen; falsche SMTP/IMAP-Zugangsdaten führen zu Mail-Fehlern.
  - **Audio/PortAudio**: Ist im Image enthalten; falls lokal nötig, entsprechend System-Pakete installieren.
  - **Langsame Starts nach Dependency-Änderung**: `docker compose build app` neu ausführen.

---

## 🧭 Nützliche Commands
- Silent-Mode:
  ```bash
  docker compose run --rm app python main.py --silent
  ```
- Voice-Mode:
  ```bash
  docker compose run --rm app python main.py
  ```
- Wetter-Executor direkt:
  ```bash
  docker compose run --rm app python -m src.weather_executor --city_name "Berlin"
  ```

---

Made with ⚙️ + ☕
