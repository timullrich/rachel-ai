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

GTAF_DRC_PATH=/app/gtaf_artifacts/drc.json
GTAF_ARTIFACTS_DIR=/app/gtaf_artifacts
GTAF_SCOPE=local:rachel
GTAF_COMPONENT=chat-service
GTAF_INTERFACE=tool-calls
GTAF_SYSTEM=rachel-local-agent
```
Secrets stay out of Git (`.env` is ignored).

### GTAF artifacts
Place evaluated GTAF artifacts in `gtaf_artifacts/`:
- `drc.json`
- `sb/SB-LOCAL-RACHEL.json`
- `dr/DR-COMMAND-EXEC.json`
- `rb/RB-TIM-LOCAL.json`

Rules:
- JSON only (no YAML)
- SDK loader resolves artifacts by category from `sb/`, `dr/`, `rb/`
- artifact filenames must be `<artifact_id>.json`

If artifacts are missing/invalid, tool execution is denied (fail-safe).

### GTAF runtime enforcement
Tool calls are intercepted in `ChatService` before any executor runs:

```text
User Prompt -> LLM Tool Call -> gtaf_sdk.enforce_from_files() -> EXECUTE | DENY -> Executor / Refusal
```

- Executors stay unchanged.
- Enforcement is centralized and deterministic.
- `DENY` returns deterministic runtime reason codes.
- Pre-enforcement loader/input failures return `SDK_*` reason codes.

Action mapping (for policy matching):
- Canonical IDs are generated via `gtaf_sdk.actions.normalize_action(...)`.
- Rachel only defines deterministic `tool_name -> prefix` wiring.
- For command-style tools, SDK normalization uses the first command token
  (`<prefix>.<first-token>`).
- Examples:
  - `execute_command` with `{\"command\":\"date\"}` -> `execute_command.date`
  - `execute_command` with `{\"command\":\"rm test.txt\"}` -> `execute_command.rm`
  - `weather_operations` with no command-arg -> `weather_operations`
  - unmapped tool -> `__unknown__`

Quick local validation:
1. Start app:
   ```bash
   docker compose run --rm app python main.py --silent
   ```
2. Allowed example:
   - Prompt: `Wie spät ist es?`
   - Expected: `GTAF EXECUTE: execute_command.date`
3. Denied example:
   - Prompt: `Lösche bitte die Datei test.txt`
   - Expected: `GTAF DENY: execute_command.rm reason=DR_MISMATCH`
   - Expected user-facing response: refusal, action not delegated.

Common GTAF reason codes:

| Reason code | Meaning |
|---|---|
| `OK` | Action is permitted and execution continues. |
| `DR_MISMATCH` | Action does not match any delegated decision in DR artifacts. |
| `DRC_NOT_PERMITTED` | DRC result is not `PERMITTED`. |
| `MISSING_REFERENCE` | Referenced SB/DR/RB artifact is missing. |
| `EXPIRED` | DRC or referenced artifact is outside validity window. |
| `SCOPE_LEAK` | Scope mismatch between context and artifacts. |
| `OUTSIDE_SB` | Component/interface is outside the defined system boundary. |
| `RB_REQUIRED` | Delegation mode requires active RB, but no active RB exists. |
| `INVALID_DRC_SCHEMA` | DRC structure is invalid. |
| `UNSUPPORTED_GTAF_VERSION` | DRC GTAF reference version is unsupported by runtime. |
| `INTERNAL_ERROR` | Runtime failed internally and denied fail-safe. |
| `SDK_INVALID_DRC` | SDK failed before runtime: invalid DRC input file. |
| `SDK_ARTIFACT_NOT_FOUND` | SDK failed before runtime: referenced artifact file missing. |
| `SDK_INVALID_JSON` | SDK failed before runtime: malformed JSON artifact/DRC file. |
| `SDK_INVALID_ARTIFACT` | SDK failed before runtime: invalid artifact structure/content. |
| `SDK_DUPLICATE_ARTIFACT_ID` | SDK failed before runtime: duplicate artifact IDs. |
| `SDK_LOAD_ERROR` | SDK failed before runtime: generic runtime input load error. |

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
- Local plugin support:
  - `gtaf-runtime` is mounted to `/opt/plugins/gtaf-runtime` and installed first.
  - `gtaf-sdk-py` is mounted to `/opt/plugins/gtaf-sdk-py` and installed second.

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
  docker compose run --rm app python -m unittest discover -s tests -p 'test_*.py' -v
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
