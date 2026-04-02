# Web Preview Stack

This repository now includes a migration preview for a FastAPI plus React web stack that can coexist with the current Dash application.

## Components

- `backend/`: FastAPI API for the restored workflow.
- `frontend/`: React + Vite browser client.
- `eit_dash/`: existing Dash application, kept intact while the new stack is developed.

## Run the preview backend

Install Python dependencies first:

```console
poetry install
```

Start the backend on `http://127.0.0.1:8000`:

```console
poetry run eit-dash run-api
```

You can also run the dedicated script directly:

```console
poetry run eit-dash-api
```

## Run the preview frontend

Install the frontend dependencies:

```console
cd frontend
npm install
```

Start the Vite dev server on `http://127.0.0.1:5173`:

```console
npm run dev
```

The Vite config proxies `/api` traffic to the local FastAPI backend.

## Current preview scope

The preview preserves the existing product shape while moving the workflow onto the new stack:

- top navigation, sidebar, footer, and process stepper restored in the React shell
- `load`, `preprocessing`, `analyze`, `about`, and `contact` routes available in the new UI
- `load` uses the FastAPI backend for file browsing, preview loading, signal selection, range trimming, and dataset cards
- `preprocessing` uses the FastAPI backend for stable-period selection, filtering, and saved preprocessing state
- `analyze` uses the FastAPI backend for Step 3 summary state, EELI calculation, and rendered output collections
- session bootstrap happens through REST
- Plotly figures are rendered in the browser from Python-generated payloads so the new UI can reuse the old Dash compute/render pipeline where parity matters most
