# BurnerPass

**Self-destructing credential sharing API built with Django REST Framework and Flutter.**

BurnerPass is an ephemeral secret-sharing application that allows users to share sensitive information through single-use links.

Instead of leaving API keys, temporary passwords, SSH tokens, or recovery codes in chat histories and email threads, BurnerPass encrypts secrets and makes them available for a limited time. Once a secret is accessed, it is marked as burned and cannot be retrieved again through the API.

## Features

- **Encrypted Secret Storage:** Encrypts sensitive payloads using Fernet before storing them in the database.
- **Single-Use Secret Access:** Secrets can be revealed only once through the burn endpoint.
- **Configurable Expiration:** Set a time-to-live (TTL) between 1 and 168 hours.
- **Atomic Secret Consumption:** Uses database transactions and row locking to prevent concurrent requests from successfully consuming the same secret.
- **Non-Destructive Status Check:** Allows clients to check secret availability without consuming it.
- **Ciphertext Clearing:** Clears the stored ciphertext after successful secret consumption.
- **Automated Cleanup:** Includes a Django management command to remove expired and burned records.
- **Mobile Deep Links:** Generates shareable API URLs and Flutter deep links from the backend.

## System Architecture

```text
        FLUTTER CLIENT
     (Dart + Provider)
              |
              | REST / JSON
              |
              v
       DJANGO REST API
              |
      +-------+--------+
      |                |
      v                v
   Fernet          PostgreSQL
  Encryption       / SQLite
      |
      v
 Encrypted Secret
   (Ciphertext)
```

### Secret Lifecycle

1. The sender submits a secret and expiration time.
2. The backend encrypts the secret using Fernet.
3. The encrypted payload and metadata are stored in the database.
4. The backend generates a unique secret ID and shareable links.
5. The recipient checks the secret's availability.
6. The recipient submits a burn request.
7. The backend locks the database record, decrypts the secret, clears the stored ciphertext, and marks it as burned.

## Cryptography

BurnerPass uses the `cryptography` Python package and its Fernet implementation for symmetric authenticated encryption.

### How Fernet Works

Fernet provides:

- AES-128-CBC encryption for confidentiality.
- HMAC-SHA256 authentication to detect tampering.
- A timestamp embedded in the encrypted token.

The same secret key is used for both encryption and decryption.

### `app/crypto.py`

The cryptography module separates encryption logic from the API views.

It provides helper functions such as:

```python
encrypt_secret(plaintext)
decrypt_secret(ciphertext)
```

**Encryption flow:**

```text
Plaintext Secret
       |
       v
Fernet Encryption
       |
       v
Encrypted Token
       |
       v
Database Storage
```

**Decryption flow:**

```text
Stored Ciphertext
       |
       v
Fernet Decryption
       |
       v
Plaintext Secret
       |
       v
Return to Recipient
```

The Fernet key is loaded from an environment variable rather than hardcoded into the application.

> Fernet encryption protects stored payloads, but the encryption key must remain secret. If the key is compromised, stored ciphertext may be decrypted.

## Tech Stack

| Component | Technology |
|---|---|
| Backend | Python, Django |
| API | Django REST Framework |
| Cryptography | Fernet |
| Database | SQLite, PostgreSQL |
| Frontend | Flutter, Dart |
| State Management | Provider |
| API Communication | HTTP, JSON |

## Project Structure

```text
burnerpass/
├── manage.py
├── requirements.txt
├── .env
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── app/
    ├── crypto.py
    ├── models.py
    ├── serializers.py
    ├── urls.py
    ├── views.py
    └── management/
        └── commands/
            └── purge_expired.py
```

| File | Responsibility |
|---|---|
| `crypto.py` | Fernet encryption and decryption |
| `models.py` | Secret database model |
| `serializers.py` | Request validation and response serialization |
| `views.py` | API endpoints and secret lifecycle |
| `urls.py` | API route configuration |
| `purge_expired.py` | Expired secret cleanup |

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/SANS002/burnerpass.git
cd burnerpass
```

### 2. Create a virtual environment

Linux / macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Generate a Fernet key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Create a `.env` file in the project root:

```env
DJANGO_SECRET_KEY=your-django-secret-key
FERNET_KEY=your-generated-fernet-key
```

Never commit your `.env` file or encryption key to GitHub.

### 5. Apply migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Start the development server

```bash
python manage.py runserver
```

The API will be available at:

```text
http://127.0.0.1:8000/
```

## API Reference

### 1. Create a Secret

**Endpoint**

```http
POST /api/v1/secrets/create/
```

**Request**

```json
{
  "secret_text": "example-sensitive-value",
  "ttl_hours": 24
}
```

`ttl_hours` is optional. The default is 24 hours, with a supported range of 1–168 hours.

**Response — 201 Created**

```json
{
  "secret_id": "550e8400-e29b-41d4-a716-446655440000",
  "burn_url": "http://127.0.0.1:8000/api/v1/secrets/550e8400-e29b-41d4-a716-446655440000/burn/",
  "deep_link": "burnerpass://reveal/550e8400-e29b-41d4-a716-446655440000",
  "expires_at": "2026-11-25T10:30:00Z",
  "message": "Secret encrypted and stored."
}
```

### 2. Check Secret Status

Checks whether a secret is available without consuming it.

**Endpoint**

```http
GET /api/v1/secrets/<uuid:secret_id>/status/
```

**Response — 200 OK**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "is_accessible": true,
  "expires_at": "2026-11-25T10:30:00Z"
}
```

Returns `410 Gone` if the secret has expired or has already been burned.

### 3. Burn and Reveal a Secret

Consumes the secret and returns its plaintext value.

**Endpoint**

```http
POST /api/v1/secrets/<uuid:secret_id>/burn/
```

**Response — 200 OK**

```json
{
  "secret_text": "example-sensitive-value",
  "detail": "Secret revealed and permanently destroyed."
}
```

Returns `410 Gone` if the secret has expired or has already been consumed.

## Database Maintenance

BurnerPass includes a custom Django management command to remove expired secrets and burned records.

Run manually:

```bash
python manage.py purge_expired
```

The command can also be scheduled using cron or another task scheduler.

## Security Considerations

- Secret payloads are encrypted before database storage.
- The Fernet key is stored separately from the database.
- Secret IDs are generated using UUIDv4.
- Database transactions and row locking help prevent concurrent secret consumption.
- The status endpoint does not reveal the secret.
- Ciphertext is cleared after successful consumption.

**Important:** BurnerPass is designed to minimize the persistence of sensitive data. Clearing ciphertext from a database record does not guarantee secure physical erasure from database files, backups, logs, or memory. Production deployments should use PostgreSQL for reliable row locking and configure HTTPS, secure key management, restricted logging, and appropriate database access controls.

## Future Improvements

- Add automated tests for concurrent burn requests.
- Add rate limiting and abuse protection.
- Improve secret expiration and cleanup scheduling.
- Add production deployment configuration.
- Complete Flutter deep-link handling and secret reveal flow.