# AI Manga Backend

FastAPI-based backend for the Spell AI manga generation platform. The service exposes public REST/WebSocket APIs for clients, schedules background jobs via Cloud Tasks, and persists state in PostgreSQL.

## Architecture Overview

- **FastAPI** application served on Cloud Run.
- **Cloud Tasks** used to execute seven-phase generation pipelines asynchronously.
- **PostgreSQL (Cloud SQL)** stores session state, phase outputs, preview versions, and feedback.
- **Cloud Storage** keeps preview payloads; signed URLs are issued per phase.
- **Firebase Hosting** fronts the public client; all public traffic hits the backend through Hosting rewrites.

## Requirements

- Python 3.11+
- Google Cloud project with Cloud Tasks, Cloud Storage, Cloud Run, and Secret Manager enabled
- PostgreSQL 15 instance reachable from the application

### Google Cloud client libraries

The backend requires the following official libraries at runtime:

- `google-cloud-tasks`
- `google-cloud-storage`
- `google-auth`

They are included in `pyproject.toml`, but verify the installation inside your virtual environment:

```bash
pip install google-cloud-tasks google-cloud-storage google-auth
```

> 本番環境では、`pip install -e .` の実行後に `pip list | grep google-` で導入済みか確認してください。Cloud Runイメージではビルド時に必ず導入されるよう、CI/CDで同コマンドを実行することを推奨します。

## Getting Started

1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -e .
   ```
3. Copy configuration template:
   ```bash
   cp .env.example .env
   ```
   Update database URL, Cloud Tasks, and Firebase credentials.
4. Apply migrations (requires running PostgreSQL):
   ```bash
   alembic upgrade head
   ```
5. Launch the development server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
   ```

## Key Commands

- `alembic revision --autogenerate -m "message"` – create a new migration.
- `alembic upgrade head` – apply migrations.
- `uvicorn app.main:app` – run the service.

## Environment Variables

Refer to `.env.example`. Important values:

- `DATABASE_URL` – SQLAlchemy async connection string.
- `CLOUD_TASKS_QUEUE` / `CLOUD_TASKS_LOCATION` / `CLOUD_TASKS_SERVICE_URL` – Cloud Tasksキュー設定。
- `CLOUD_TASKS_PROJECT` – 利用するGCPプロジェクトID（本番: `comic-ai-agent-470309`）。
- `GCS_BUCKET_PREVIEW` & `SIGNED_URL_TTL_SECONDS` – preview storage configuration.
- `FIREBASE_*` – service account credentials (used for signed requests).
- `AUTH_SECRET_KEY` – HMACベースのアクセストークン署名に使用する機微情報。Google Secret Managerなどで安全に管理し、ローカル開発では`.env`に直接記載しないよう注意してください。
- `ACCESS_TOKEN_EXPIRES_MINUTES` / `REFRESH_TOKEN_EXPIRES_DAYS` – 認証トークンの有効期限を制御します（省略時は既定値）。
- `VERTEX_PROJECT_ID` / `VERTEX_LOCATION` – Vertex AIを呼び出す際のプロジェクト・リージョン。
- `VERTEX_TEXT_MODEL` / `VERTEX_IMAGE_MODEL` – 使用するGeminiテキストモデル/Imagenモデルの指定。

### Secret Manager integration

`deploy/fetch-secrets.sh` を用いると、Google Secret Managerに保管したシークレットを `.env.gcp` などのローカルファイルへ書き出せます。利用前に `PROJECT_ID` と必要であれば `SECRET_PREFIX` を設定してください。

```bash
PROJECT_ID=my-gcp-project SECRET_PREFIX=spell-backend ./deploy/fetch-secrets.sh .env.gcp
```

### OpenAPI client generation

- GitHub Actions: `.github/workflows/openapi-sdk.yml` が `docs/05.API_openapi.yaml` に変更があった場合にTypeScript/Pythonクライアントを自動生成し、アーティファクトとして保存します。
- ローカル: `scripts/generate_openapi_clients.sh` を実行するとDocker上のOpenAPI Generatorで同じクライアントを生成できます。

```bash
./scripts/generate_openapi_clients.sh
```

Detailed deployment instructions (Cloud Run + Firebase Hosting integration) will be added alongside CI/CD scripts.
