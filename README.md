# EXAMGUARS 1.0

EXAMGUARS is a Windows desktop examination client built with Python 3.12+, PySide6/Qt WebEngine, SQLite, and RSA-PSS signatures.

## Security scope

EXAMGUARS enforces an HTTPS website allowlist **inside its own browser** and records focus changes in a local SQLite database. It displays warnings without deleting answers or scores. Because answers belong to the external LMS, EXAMGUARS cannot read, autosave, or submit them; when the warning threshold is reached, it records a critical event but does not claim that the LMS attempt was submitted. It does not lock Windows, install global keyboard hooks, inspect screen contents, or terminate other processes. A process name is an observation, not proof of misconduct. Use Windows Assigned Access/kiosk policies separately when OS-level kiosk restrictions are required.

Exam configurations are rejected unless their schema and signature validate against `config/trusted_public_key.pem`. The committed `config/exam.egconfig` is an unsigned template and intentionally cannot start an exam. The signing private key must stay in a controlled administrator environment and must not be included in the client installer.

## Setup on an administrator computer

Use Python 3.12 or newer:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Generate a 3072-bit RSA key pair once. The command prompts for an encryption passphrase and refuses to overwrite existing keys:

```powershell
python -m core.digital_signature generate
```

Back up `keys/private_key.pem` securely. Do not copy it to a student computer or installer. `config/trusted_public_key.pem` is the public trust anchor and can be distributed with the signed configuration.

Run the app and open **Quản trị viên**. On first use, create a unique administrator password containing 5 to 10 characters. Fill in the exam parameters and choose the private-key file/passphrase to sign `config/exam.egconfig`. The public key in `config/trusted_public_key.pem` must correspond to that private key. The initial template uses `lms.example.edu`; replace it with the real HTTPS exam URL and exact allowed domains.

The administrator dashboard shows locally recorded session counts and audit events and exports CSV reports. Ending an exam session requires the administrator password. Students enter their student ID and name locally; they then sign into the LMS inside the exam browser. No Central Server address or student server account is required. Each PC stores its own logs, so export and collect those reports manually if needed.

## Run and test

```powershell
python main.py
python -m unittest discover -s tests -v
python -m unittest central_server.tests.test_api -v
```

SQLite data and rotating application logs are stored under `%LOCALAPPDATA%\EXAMGUARS` on Windows. The database path can be overridden in tests by passing a path to `DatabaseService`.

## Central Server backend (phase 2)

The project now includes a FastAPI Central Server with PostgreSQL deployment
support, SQLite local development, Alembic migrations, RBAC, short-lived JWT
access tokens, rotated refresh tokens, teacher-owned course sections/exams,
RSA-PSS signed `.egconfig` publication, student session/event APIs,
idempotent submission receipts, device revocation, and release metadata.

The server has a separate dependency manifest and setup guide:

```powershell
python -m pip install -r central_server\requirements-test.txt
python -m alembic -c central_server\alembic.ini upgrade head
python -m central_server.app.bootstrap_admin
python -m uvicorn central_server.app.main:app --host 127.0.0.1 --port 8000
```

See [Central Server setup](./central_server/DEPLOYMENT.md)
and the [API contract](./central_server/API.md).
The configured server-account password policy is 5–10 characters as requested;
this is weak for internet exposure. Deployment requires operator-provisioned
database/JWT/TLS/signing secrets. No secret or signing key is generated or
stored in the repository.

The Central Server backend and teacher portal are separate optional components.
The current desktop client does not connect to them and runs external-LMS
exams with local focus warnings only. The backend can separately manage
built-in exams and store submissions, but using it requires a server deployment
and a desktop integration change. Docker/Nginx deployment templates are
available, but Docker deployment and production operations have not been
validated.

## Build and install

After generating and validating a real signed configuration:

```powershell
.\installer\build.bat
```

The build script installs declared dependencies, runs the test suite, verifies the signed configuration, and creates `dist\EXAMGUARS`. Open `installer\EXAMGUARS.iss` with Inno Setup to create the installer. Neither `keys\private_key.pem` nor the `keys` directory is packaged.

## Current integration points

- `core/configuration.py`: schema validation and fail-closed signature verification.
- `core/digital_signature.py`: offline RSA-PSS/SHA-256 key and signature helpers.
- `core/security.py`: URL policy and PBKDF2 password helpers.
- `core/session.py`: exam-session lifecycle.
- `core/browser.py`: HTTPS host restrictions on navigation and web requests.
- `core/monitoring.py`, `services/process_service.py`: asynchronous, read-only process observations.
- `services/database.py`: shared SQLite persistence, admin authentication, and session/event storage.
- `services/api.py`: optional asynchronous HTTPS event reporting; no endpoint is assumed when unset.
- `core/reporting.py`: CSV audit export.

This is not a certified replacement for Safe Exam Browser. Validate it in a managed test environment and deploy appropriate Windows kiosk policy separately before high-stakes examinations.
