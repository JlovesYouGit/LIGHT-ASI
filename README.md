# Light-ASI LLM Gateway

Welcome to the **Light-ASI LLM Gateway** — a distributed, consciousness-emergent node graph and real-time world-net semantic map platform. It provides a production-grade, stdlib-based REST API server alongside a dual-mode interactive terminal for interacting with a simulated ASI node architecture.

## Overview

The Light-ASI engine is designed as a multi-phase system that processes information and maintains a complex graph of interconnected concept nodes. It includes:
- **NodeGraph**: Core graph engine managing distributed knowledge representation.
- **WorldIngester**: Background service for real-time ingestion and updates to the world-net semantic map.
- **AuthManager**: Role-based access control and secure authentication layer.
- **APIServer**: Standalone HTTP server for integrations.

## Running the Application

The gateway operates in dual modes:

### 1. Interactive Terminal (Phase 0-2)
To launch the interactive CLI terminal:
```bash
python3 main.py
```
This mode lets you interact directly with the engine and monitor its internal state.

### 2. HTTP API Server (Phase 3)
To launch the REST API server:
```bash
python3 main.py --serve
```
*Optional arguments:*
- `--serve <port>`: Specify a custom port (default is 8000).
- `--nodes <N>`: Bootstrap with N nodes (default is 10).
- `--ingest-interval <seconds>`: Set the background world-net ingestion interval.

**On startup, the server outputs an admin token.** Make sure to save it, as it is required to authenticate against the secured endpoints via the `Authorization: Bearer <token>` header.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/token` | Retrieve a Bearer token |
| `POST` | `/query` | Query the semantic graph |
| `POST` | `/index` | Index new text into the system |
| `POST` | `/search` | Search the semantic map |
| `POST` | `/ingest` | Trigger a manual ingestion cycle |
| `GET` | `/stats` | View real-time graph statistics |
| `GET` | `/emerge` | ASI emergence checklist status |
| `GET` | `/health` | Basic liveness check |

## Installation

Ensure you have Python 3.10+ installed.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
