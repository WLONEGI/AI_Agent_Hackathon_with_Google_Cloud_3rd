# Local Environment Setup Guide

This guide explains how to set up and run the application locally using Docker Compose.

## Prerequisites

- Docker Desktop installed and running.
- Git.

## Setup Steps

1.  **Clone the repository** (if you haven't already).

2.  **Environment Variables**:
    - Copy `.env.example` to `.env` in the root directory.
    - Copy `frontend/.env.example` to `frontend/.env.local`.
    - Update the values in `.env` if necessary (e.g., Vertex AI credentials if you plan to use them).

3.  **Google Cloud Credentials**:
    - Place your Google Cloud service account key JSON file at `secrets/gcp-key.json` (create the directory if it doesn't exist).
    - This is required for the worker to access Vertex AI.

4.  **Build and Run**:
    ```bash
    docker compose up --build
    ```

5.  **Access the Application**:
    - Frontend: [http://localhost:3000](http://localhost:3000)
    - Backend API: [http://localhost:8000](http://localhost:8000)
    - MinIO Console: [http://localhost:9001](http://localhost:9001) (User/Pass: minioadmin/minioadmin)

## Services

- **Frontend**: Next.js application.
- **Backend**: FastAPI application.
- **Worker**: Arq worker for background tasks.
- **DB**: PostgreSQL database.
- **Redis**: Job queue and caching.
- **MinIO**: Local S3-compatible storage.

## Development

- The `backend` and `frontend` directories are mounted as volumes, so changes to the code should be reflected immediately (hot reload).
