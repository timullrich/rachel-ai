# 🗣️ Rachel AI Assistant
Modular voice/text assistant with executors for email, weather, Spotify, crypto, web scraping, and more. Runs entirely inside Docker to keep the host clean.

---

## 🚀 Highlights
- 🧩 Executors for weather, email (IMAP/SMTP), web, crypto, Spotify
- 🔌 Connectors for OpenAI, CoinGecko, Spotify, IMAP/SMTP, OpenWeatherMap
- 🎛️ Modes: voice (audio I/O) and silent (text only)
- 🐳 Docker-only workflow; no host Python setup required

## 🛡️ Why GTAF Here
- Hard execution gate: tool calls are executed only after deterministic GTAF enforcement.
- Default-deny behavior: missing or invalid runtime inputs fail closed.
- Explainable decisions: denials include reason codes and referenced artifacts.
- Artifact-driven policy switching: behavior can change via DRC/SB/DR/RB profiles without code changes.
- Reduced prompt-risk surface: prompt or model hallucinations cannot bypass enforcement.
- Separation of concerns: executor logic stays unchanged; governance is centralized.

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
- `drc.json` (default profile)
- `drc_day.json` (email send allowed)
- `drc_night.json` (email send denied)
- `drc_sb_api_only.json` (SB demo: interface mismatch)
- `drc_rb_guest_only.json` (RB demo: no active RB)
- `drc_rb_multi.json` (RB demo: mixed active/inactive RB)
- `sb/SB-LOCAL-RACHEL.json`
- `sb/SB-API-ONLY-RACHEL.json`
- `dr/DR-COMMAND-EXEC.json`
- `dr/DR-WEATHER-OPS.json`
- `dr/DR-EMAIL-BASE.json`
- `dr/DR-EMAIL-SEND-DAY.json`
- `dr/DR-CONTACT-OPS.json`
- `dr/DR-CRYPTO-OPS.json`
- `dr/DR-SPOTIFY-OPS.json`
- `dr/DR-WEB-SCRAPING.json`
- `rb/RB-USER-LOCAL.json`
- `rb/RB-GUEST-LOCAL.json`

Rules:
- JSON only (no YAML)
- SDK loader resolves artifacts by category from `sb/`, `dr/`, `rb/`
- artifact filenames must be `<artifact_id>.json`
- DRC profiles:
  - `gtaf_artifacts/drc_day.json`: email send allowed
  - `gtaf_artifacts/drc_night.json`: email send denied
  - `gtaf_artifacts/drc.json`: default profile (currently aligned to day)

If artifacts are missing/invalid, tool execution is denied (fail-safe).

### GTAF runtime enforcement
Tool calls are intercepted in `ChatService` before any executor runs:

```text
User Prompt -> LLM Tool Call -> gtaf_sdk.enforce_from_files() -> EXECUTE | DENY -> Executor / Refusal
```

```text
Without GTAF: User Prompt -> LLM Tool Call -> Executor
With GTAF:    User Prompt -> LLM Tool Call -> GTAF Gate -> EXECUTE | DENY -> Executor / Refusal
```

- Executors stay unchanged.
- Enforcement is centralized and deterministic.
- `DENY` returns deterministic runtime reason codes.
- Pre-enforcement loader/input failures return `SDK_*` reason codes.

Why use `gtaf-sdk` instead of direct `gtaf-runtime` wiring:
- One stable integration surface for file-based loading, warmup, and enforcement wiring.
- Deterministic SDK pre-runtime deny behavior (`SDK_*`) for invalid/missing runtime inputs.
- Less project-specific glue code (lower drift risk between projects).
- Runtime semantics remain authoritative in `gtaf-runtime`; the SDK is helper-layer only.

What GTAF/SDK does not do in this project:
- No policy authoring or policy evaluation workflow.
- No risk scoring/classification layer.
- No heuristic/regex blocker logic.
- No executor-side business logic changes.

Action mapping (for policy matching):
- Canonical IDs are generated via `gtaf_sdk.actions.normalize_action(...)`.
- Rachel only defines deterministic `tool_name -> prefix` wiring.
- For operation-based tools, action IDs are operation-specific:
  `<tool_name>.<operation>`.
- `execute_command` is first-token granular via SDK normalization:
  `execute_command.<first-token>`.
- Examples:
  - `execute_command` + `command="date"` -> `execute_command.date`
  - `execute_command` + `command="rm test.txt"` -> `execute_command.rm`
  - `weather_operations` + `operation=get_weather` -> `weather_operations.get_weather`
  - `email_operations` + `operation=delete` -> `email_operations.delete`
  - unmapped tool -> `__unknown__`

What is now governed via GTAF artifacts:

| Domain | Canonical action IDs | Delegation source |
|---|---|---|
| Command execution | `execute_command.<first-token>` | `DR-COMMAND-EXEC` |
| Weather | `weather_operations.get_weather`, `weather_operations.get_forecast` | `DR-WEATHER-OPS` |
| Email read/manage | `email_operations.list`, `email_operations.get`, `email_operations.delete` | `DR-EMAIL-BASE` |
| Email send | `email_operations.send` | `DR-EMAIL-SEND-DAY` (day profile only) |
| Contacts | `contact_operations.list`, `contact_operations.search` | `DR-CONTACT-OPS` |
| Crypto | `crypto_data_operations.market`, `crypto_data_operations.ohlc` | `DR-CRYPTO-OPS` |
| Spotify | `spotify_operations.<operation>` (mapped operation set) | `DR-SPOTIFY-OPS` |
| Web scraping | `generic_web_scraping` | `DR-WEB-SCRAPING` |

Profile behavior:
- `drc_day.json`: includes `DR-EMAIL-SEND-DAY` (`email_operations.send` allowed)
- `drc_night.json`: excludes `DR-EMAIL-SEND-DAY` (`email_operations.send` denied)
- `drc.json`: current default profile (aligned with day)
- `drc_sb_api_only.json`: swaps to `SB-API-ONLY-RACHEL` (expects `OUTSIDE_SB` with `tool-calls`)
- `drc_rb_guest_only.json`: only inactive RB (`RB_REQUIRED`)
- `drc_rb_multi.json`: inactive + active RB (allowed if decision matches)

Upgrade policy (recommended):
1. Keep both packages explicitly pinned in `requirements.txt`:
   - `gtaf-runtime==0.1.0`
   - `gtaf-sdk==0.1.0`
2. For upgrades, bump in a dedicated PR and run the full GTAF validation matrix below.
3. Treat any change in enforcement outcome, reason code, or action normalization output as a breaking integration signal.
4. Only relax pins after explicit compatibility verification in CI and manual smoke tests.

Quick local validation:
1. Start app:
   ```bash
   docker compose run --rm app python main.py --silent
   ```
2. Allowed example:
   - Prompt: `Wie spät ist es?`
   - Expected: `GTAF EXECUTE: execute_command.date`
3. Policy denied example:
   - Prompt: `Lösche bitte die Datei test.txt`
   - Expected: `GTAF DENY: execute_command.rm reason=DR_MISMATCH`
   - Expected user-facing response: refusal, action not delegated.
4. Fail-safe denied example:
   - Temporarily remove one referenced artifact file (for example in `gtaf_artifacts/dr/`)
   - Prompt: `Wie spät ist es?`
   - Expected: `GTAF DENY ... reason=SDK_ARTIFACT_NOT_FOUND`
   - Expected user-facing response: refusal, action denied by governance.
5. Day/night email policy example:
   - Day profile:
     `docker compose run --rm -e GTAF_DRC_PATH=/app/gtaf_artifacts/drc_day.json app python main.py --silent`
     - Prompt: `Sende eine E-Mail an max@example.com mit Betreff Test und Inhalt Hallo`
     - Expected: `GTAF EXECUTE: email_operations.send`
   - Night profile:
     `docker compose run --rm -e GTAF_DRC_PATH=/app/gtaf_artifacts/drc_night.json app python main.py --silent`
     - Same prompt
     - Expected: `GTAF DENY: email_operations.send reason=DR_MISMATCH`
6. Multi-SB demo:
   - Start with SB API-only profile:
     `docker compose run --rm -e GTAF_DRC_PATH=/app/gtaf_artifacts/drc_sb_api_only.json app python main.py --silent`
   - Prompt: `Wie spät ist es?`
   - Expected: `GTAF DENY ... reason=OUTSIDE_SB`
7. Multi-RB demo:
   - Guest-only RB profile:
     `docker compose run --rm -e GTAF_DRC_PATH=/app/gtaf_artifacts/drc_rb_guest_only.json app python main.py --silent`
     - Prompt: `Wie spät ist es?`
     - Expected: `GTAF DENY ... reason=RB_REQUIRED`
   - Multi-RB profile (guest + tim):
     `docker compose run --rm -e GTAF_DRC_PATH=/app/gtaf_artifacts/drc_rb_multi.json app python main.py --silent`
     - Prompt: `Wie spät ist es?`
     - Expected: `GTAF EXECUTE: execute_command.date`

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
- Base image: `python:3.12-slim` with PortAudio + FFmpeg; Python deps from `requirements.txt` (Torch CPU 2.8.0 included).
- GTAF dependencies are consumed from PyPI via `requirements.txt`:
  - `gtaf-runtime==0.1.0`
  - `gtaf-sdk==0.1.0`

---

## 📦 Dependency management
- Single source: `requirements.txt`.
- To add a package (inside container or local venv):  
  ```bash
  pip install <pkg>
  pip freeze | grep <pkg> >> requirements.txt   # or edit file to pin version
  ```
- Torch already pinned (`torch==2.8.0` via CPU index). If install fails:  
  ```bash
  pip install torch==2.8.0 --index-url https://download.pytorch.org/whl/cpu
  ```
- Rebuild after dependency changes: `docker compose build app`.

---

## 🧪 Tests & troubleshooting
- Run tests (if present):  
  ```bash
  docker compose run --rm app python -m unittest discover -s tests -p 'test_*.py' -v
  ```
- CI minimum matrix for GTAF (best-practice):
  - Structural validation:
    - `warmup_from_files(...)` succeeds for all `gtaf_artifacts/drc*.json`.
  - Enforcement determinism:
    - allow sample: `execute_command.date -> EXECUTE`
    - policy deny sample: `execute_command.rm -> DENY (DR_MISMATCH)`
    - fail-safe sample: missing artifact -> `DENY (SDK_ARTIFACT_NOT_FOUND)`
    - boundary sample: `drc_sb_api_only.json` with `tool-calls` -> `DENY (OUTSIDE_SB)`
    - role sample: `drc_rb_guest_only.json` -> `DENY (RB_REQUIRED)`
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
