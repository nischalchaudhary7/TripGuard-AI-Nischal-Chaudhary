# TripGuard AI

## Overview

TripGuard AI is a U.S. air-travel disruption intelligence MVP. A traveler enters an origin airport, destination airport, and travel date. The backend resolves the airports, collects real external data, converts source-specific responses into normalized disruption signals, calculates a deterministic risk score, and returns evidence, uncertainty notes, recommended actions, and an AI-generated or deterministic trip brief.

The application is intended to summarize disruption risk from available public data. It does not book travel, monitor a saved itinerary, authenticate users, or store assessment history.

## Architecture

```text
User Input
-> Airport Resolution
-> External Data Connectors
-> Normalized Signal Objects
-> Deterministic Risk Scoring
-> Evidence-Grounded AI Synthesis
-> React Dashboard
```

External APIs are the source of truth. Each external source is handled by its own connector and normalized into a common `Signal` model before scoring or synthesis. The assessment service collects available signals from each connector, tracks source coverage, and degrades gracefully when an individual source fails or is unavailable instead of fabricating data.

Key project areas:

- `backend/app/connectors`: source-specific connectors for OurAirports, NWS, AWC, and FAA NAS Status.
- `backend/app/core/models`: shared airport, signal, source coverage, and assessment models.
- `backend/app/core/scoring`: deterministic risk scoring rules.
- `backend/app/core/synthesis`: Gemini/OpenAI synthesis interface and deterministic fallback synthesis.
- `backend/app/services`: airport resolution, signal collection, confidence, caveats, and assessment orchestration.
- `frontend/src`: Vite React dashboard, typed API client, and evidence panels.

## Data Sources

- OurAirports: resolves U.S. airports, including IATA codes, airport names, coordinates, city, region, and ICAO identifiers when available.
- National Weather Service (NWS): retrieves active weather alerts and point forecasts, then selects alert and forecast evidence relevant to the requested travel date.
- Aviation Weather Center (AWC): retrieves METAR observations and TAF forecasts for aviation-specific weather evidence when relevant to the requested trip.
- FAA NAS Status: retrieves official FAA airport operational status information from `https://nasstatus.faa.gov/api/airport-status-information`. The endpoint returns XML. The backend parses the XML and converts relevant airport operational events into normalized `FAA_OPERATIONAL` signals. If FAA data cannot be reached or parsed, the application reports the source failure or unavailability and continues with remaining sources.

## Risk Scoring

The numerical risk score is deterministic, reproducible, and explainable. Gemini does not calculate or modify the score.

Scoring considers implemented factors including normalized signal severity, signal confidence, source category weight, time-horizon relevance already reflected in signal severity/confidence, corroboration across sources or multiple signals affecting the same airport, and high-risk overrides for severe verified events such as airport closures, ground stops, tornado warnings, blizzard warnings, or ice storm warnings.

Corroboration is applied as a bounded bonus rather than by repeatedly counting every piece of similar evidence as independent risk. This keeps the score explainable while reducing the chance of over-weighting the same underlying disruption.

## AI Usage

Gemini is used for evidence-grounded synthesis only. The configured Gemini model is `gemini-3.8-flash`.

When `AI_PROVIDER=gemini` and `GEMINI_API_KEY` is configured, Gemini receives resolved trip information, normalized signals, deterministic risk score and level, confidence, and caveats. It turns that verified evidence into concise traveler-facing explanations and recommended actions.

Gemini must not invent delays, cancellations, closures, weather events, FAA restrictions, incidents, risk scores, or signal severity. AI-generated risk claims must reference valid existing Signal IDs. The backend validates the structured Gemini output and falls back to deterministic synthesis if Gemini has no API key, times out, is rate limited, returns invalid output, references invalid Signal IDs, or fails for another reason.

The core risk assessment does not depend on Gemini being available.

## Date Relevance and Uncertainty

TripGuard is date-aware. NWS forecast periods are selected based on overlap with the requested travel date. Active alerts are included only when their effective window overlaps the travel date. AWC TAFs are included when their validity period is relevant to the requested date, and METAR observations are used for same-day travel only.

Current operational observations, active alerts, METARs, FAA operational events, and similar live signals are most useful for near-term travel. They should not be treated as predictions for distant future travel dates. Travel-date horizon affects operational relevance, forecast relevance, assessment confidence, and user-facing caveats.

## Aviation Weather Interpretation

AWC METAR and TAF evidence is deterministically translated into traveler-readable details where those details can be parsed from the raw report, including visibility, wind, precipitation/weather tokens, cloud ceiling, and important aviation conditions such as IFR/LIFR mentions or low-level wind shear.

Raw METAR/TAF text remains available in the dashboard for technical inspection.

## Confidence

Assessment confidence is deterministic. It considers source availability, whether operational sources such as AWC or FAA are unavailable or failed, signal confidence, and travel-date horizon. Confidence is capped lower for trips farther into the future because live operational data becomes less predictive.

The UI presents confidence as a percentage and traveler-readable label: Low, Medium, or High.

## Frontend Experience

The frontend is a responsive React dashboard with:

- origin and destination route search using airport codes and simple suggestions
- route swap
- Today and Tomorrow quick date selection
- overall risk summary and numerical risk score
- confidence label and percentage
- recommended actions
- deterministic "Why this score?" explanation
- AI Trip Brief or deterministic evidence summary
- trip risk timeline for departure and arrival airports
- grouped disruption signals
- expandable forecast and evidence details
- raw METAR/TAF technical details
- live data/source coverage
- uncertainty caveats
- copy summary functionality
- responsive layout

## Setup

Use Python 3.11 or newer for the backend and Node.js/npm for the frontend.

Create the backend environment file from the template:

```bash
cp .env.example backend/.env
```

On Windows PowerShell, the equivalent is:

```powershell
Copy-Item .env.example backend/.env
```

Then edit `backend/.env` locally. Never commit real secrets.

Install backend dependencies:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[dev]"
```

Install frontend dependencies:

```bash
cd frontend
npm install
```

## Environment Variables

Supported environment variables:

- `AI_PROVIDER`: `gemini`, `openai`, or `none`.
- `GEMINI_API_KEY`: Gemini API key for synthesis. Store only in `backend/.env`; never commit it.
- `GEMINI_MODEL`: Gemini model name. The project default is `gemini-3.8-flash`.
- `OPENAI_API_KEY`: optional OpenAI synthesis provider key.
- `OPENAI_MODEL`: optional OpenAI model name. The project default is `gpt-4o-mini`.
- `HTTP_TIMEOUT_SECONDS`: outbound HTTP timeout for external sources.
- `FAA_NAS_STATUS_URL`: FAA NAS Status XML endpoint. The backend default is `https://nasstatus.faa.gov/api/airport-status-information`.
- `VITE_API_BASE_URL`: frontend API base URL. It must match the backend port, for example `http://localhost:8001`.

`backend/.env` is for local secrets and runtime settings. `.env.example` must contain placeholders only. Gemini/API secrets remain server-side and must never be exposed in React frontend code.

## Run Backend

Port `8000` is the standard local backend example:

```bash
cd backend
.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

Health check:

```bash
curl http://localhost:8000/api/health
```

Another backend port may be used. If the backend runs on port `8001`, set the frontend API URL to match:

```bash
VITE_API_BASE_URL=http://localhost:8001
```

## Run Frontend

```bash
cd frontend
npm run dev
```

Vite normally starts at:

```text
http://localhost:5173
```

If port `5173` is occupied, Vite may automatically choose another development port such as `5174`.

## Tests

Backend tests:

```bash
cd backend
pytest
```

Frontend build verification:

```bash
cd frontend
npm run build
```

## Example Assessment

Because TripGuard uses live/current operational data, use today or tomorrow for the clearest demonstration. Replace `travel_date` with today's or tomorrow's date in `YYYY-MM-DD` format.

```bash
curl -X POST http://localhost:8000/api/assessments \
  -H "Content-Type: application/json" \
  -d "{\"origin\":\"DFW\",\"destination\":\"DEN\",\"travel_date\":\"YYYY-MM-DD\"}"
```

## Assumptions and Limitations

- Airport resolution is U.S.-focused and uses airports with IATA codes from OurAirports.
- Airport/city matching is intentionally simple for the MVP.
- Public data availability depends on upstream services.
- Live operational information has limited predictive value for distant future travel dates.
- The application has no authentication, database, user accounts, or persistent assessment history.

## Security

Real secrets belong in `backend/.env`. `.env` must not be committed and must not be included in the submission ZIP. `.env.example` contains placeholders only. Gemini credentials remain server-side. API keys must never be exposed in frontend code.

## Production Improvements

- Cache external responses with appropriate TTLs.
- Add retries with exponential backoff.
- Add rate limiting.
- Add structured logging and observability.
- Add richer airport autocomplete and disambiguation.
- Add historical disruption baselines.
- Add persistent assessment history.
- Add production deployment and configuration hardening.
- Broaden operational data coverage.
