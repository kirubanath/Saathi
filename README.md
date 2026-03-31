# Saathi

An AI-powered learning companion proposal for [Seekho](https://seekho.ai), a micro-learning platform with 25M+ monthly active users in India.

Saathi turns passive video watching into an active, personalized learning loop. It figures out who the user is, tracks what they know, targets their weak spots, and gives them a reason to come back. All LLM work happens offline at ingestion; the runtime interaction path is pure deterministic logic with zero LLM calls.

> **Scope:** This prototype implements the proactive learning loop, one piece of the larger Saathi vision. Conversational mode, real-time adaptation, and multi-modal interactions are described in the documentation but outside this prototype's scope.

---

## Quick Start

### Prerequisites

- **Python 3.11+**
- **Docker** (for MinIO object storage)
- **Anthropic API key** (only needed if you want to re-run LLM preprocessing; the demo ships with pre-generated artifacts and works without one)

### Setup (recommended if you have uv)

```bash
uv sync
source .venv/bin/activate
cp .env.example .env
```

### Setup (Alternative)

```bash
# Clone and enter the project
git clone <repo-url> && cd Saathi

# Create and activate virtual environment
python -m venv .venv

source .venv/bin/activate

# Install the project (editable mode)
pip install -e .

# Copy environment config
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY if you want to re-run preprocessing
```

### Launch

```bash
saathi demo
```

This single command will:
1. Start **MinIO** via `docker compose` (pulls the image on first run)
2. **Seed the database** with 2 users and 15 videos (first run only)
3. **Preprocess** all 7 aspiration videos via LLM (first run only; skipped if artifacts already exist in MinIO)
4. Start the **FastAPI server** at `http://localhost:8000`
5. Launch the **Streamlit demo** at `http://localhost:8501`

The demo calls the FastAPI server over HTTP, showcasing the full production-like architecture. Press `Ctrl+C` to stop everything.

---

## Navigating the Demo

### Layout

The demo uses a two-panel layout at every step. The **left panel** shows the learner's experience: recap bullets, quiz questions, progress updates, recommendations. The **right panel** shows what the system is thinking: classification logic, knowledge state, scoring, reasoning. Both are computed live from the FastAPI backend. Nothing is mocked.

### Controls

- **Navigation bar** at the top switches between Journeys 1–5 and the Sandbox
- **Back / Next** buttons at the bottom of every step let you move freely through a journey
- **Reset Demo** (top right) restores both users to their seed state. Click this if you want to reset the entire demo and restore all the parameters.
- **Light / Dark mode** toggle in the top right

### The Five Journeys

Run them in order. Each journey builds on the previous one.

| Journey | User | Video | What It Shows |
|---------|------|-------|---------------|
| **J1: Core Loop** | Priya (AS, Warming Up) | vid_001, Interview Confidence Ep 1 | The full pipeline end to end: classify, recap, quiz, knowledge update, progress message, recall scheduling, recommendation |
| **J2: Same Video, Different User** | Rahul (IS, New) | vid_001 (same video as J1) | Counterfactual proof. Same input, different user state, completely different output. No quiz, no recall, softer tone |
| **J3: Loop Compounds** | Priya | vid_002, Interview Confidence Ep 2 | Priya follows a J1 recommendation. Everything adapts: recap targeting shifts, quiz difficulty changes, recommendations update |
| **J4: Day 2 Recall** | Priya | *(no new video)* | Simulates 48 hours later. Recall entries from J1 surface as due. Spaced repetition in action |
| **J5: Content Type Gate** | Rahul | vid_008, How to Get Your PAN Card (utility) | Utility content skips the learning loop entirely. Recommendation uses a different bucket formula (50/30/20) |

**Aspiration journeys (J1, J2, J3)** have a **Preprocess** button on the pre-start screen. Clicking it runs the LLM preprocessing pipeline live for that video, showing transcripts, LLM calls, and artifacts. The journeys work without clicking it since all artifacts are pre-seeded.

**Journey 3 branches.** Priya gets two recommendation slots after J1: Slot 1 (series continuation) and Slot 2 (engine pick). The demo follows Slot 1 for this demo.

### Sandbox

The last tab. Select any user, any video, and any completion rate, then click **Run Pipeline**. The full loop runs in one shot and all outputs display at once. Answers "what happens if I try this combination?" with a live result. All runs write to the live database. Click **Reset Demo** to restore seed state after experimenting.

### Tips

- **Quiz answers matter.** Answer correctly to see larger score jumps, harder future questions, and longer recall intervals. Answer wrong to see the opposite. The system responds correctly to any input.
- **Slot 2 is probabilistic.** It uses softmax sampling, so the exact video can differ between runs even with identical state. This is expected.
- **Completion rate gate.** In the Sandbox, setting completion below 80% skips recap, quiz, and recall, but the watch bump and recommendations still run.

---

## Solution Overview

**[SOLUTION.md](SOLUTION.md)** is the standalone summary of the full proposal: the problem, the vision, all 11 engine components with their formulas, the architecture, and what the demo proves. Start there for the complete picture in one document.

---

## Documentation

All detailed documentation lives in [`documentation/`](documentation/). Suggested reading order:

| #  | Document | What It Covers |
|----|----------|---------------|
| 01 | [Background](documentation/01-background.md) | What Seekho is, why it works, and the problem as I see it |
| 02 | [Original Problem](documentation/02-original-problem.md) | The assignment as given, plus how I interpreted it |
| 03 | [AI Vision](documentation/03-ai-vision.md) | My hypotheses, the opportunity, and what Saathi is as the answer |
| 04 | [Scoped Problem](documentation/04-scoped-problem.md) | What the prototype builds: inputs, constraints, scope |
| 05 | [Solution Overview](documentation/05-solution-overview.md) | Three phases, 11 components, all formulas and data structures |
| 06 | [Architecture](documentation/06-architecture.md) | System design, API endpoints, tech stack, production scaling |
| 07 | [Demo Overview](documentation/07-demo-overview.md) | What the demo proves, 5 journeys, two demo users |
| 08 | [Design Decisions](documentation/08-design-decisions.md) | Key decisions, tradeoffs, alternatives rejected, known limitations |

---

## CLI Commands

| Command | What it does |
|---------|-------------|
| `saathi demo` | Starts MinIO + seeds DB + starts FastAPI + launches Streamlit |
| `saathi seed` | Seeds the database and preprocesses videos (MinIO must be running) |
| `saathi seed --force-preprocess` | Same as above, but re-runs LLM preprocessing even if artifacts exist |
| `saathi reset` | Copies `saathi_seed.db` over `saathi.db` (restores initial state) |
| `saathi reset --force-preprocess` | Resets DB and re-runs LLM preprocessing |

**Without installing** (run directly):

```bash
python cli.py demo
python cli.py seed
python cli.py reset
```

---

## Running Components Independently

If you need to run services separately (e.g., for development):

```bash
# Start MinIO (required by all other components)
docker compose up -d

# Start FastAPI server
source .venv/bin/activate
uvicorn api.app:app --host 0.0.0.0 --port 8000

# Start Streamlit demo (FastAPI must be running)
streamlit run demo/app.py
```

---

## Running Tests

```bash
source .venv/bin/activate
pytest
```

The test suite (79 tests across 10 files) covers:
- **Database operations:** CRUD for users, knowledge state, watch history, recall queue
- **Engine components:** classifier, recap engine, quiz engine, knowledge updater, recommender, recall scheduler
- **Full loop integration:** end-to-end video completion and quiz flows
- **API endpoints:** all FastAPI routes via TestClient (HTTP-level tests)
- **Storage:** MinIO read/write round-trips
- **LLM client:** provider integration (auto-skipped if no API key is set)

MinIO must be running for storage tests. All other tests use in-memory SQLite.

---

## Project Structure

```
.
├── README.md
├── SOLUTION.md                  # Concise standalone summary
├── pyproject.toml               # Package metadata and dependencies
├── requirements.txt             # Dependency list (mirrors pyproject.toml)
├── docker-compose.yml           # MinIO service definition
├── cli.py                       # CLI entry point (saathi demo/seed/reset)
├── .env.example                 # Environment variable template
│
├── documentation/               # 8 detailed documents (see table above)
│   ├── 00-index.md              #   Reading order and document map
│   ├── 01-background.md         #   What Seekho is, the problem
│   ├── 02-original-problem.md   #   The assignment and interpretation
│   ├── 03-ai-vision.md          #   Hypotheses, Saathi as the answer
│   ├── 04-scoped-problem.md     #   Prototype scope and constraints
│   ├── 05-solution-overview.md  #   Three phases, 11 components, formulas
│   ├── 06-architecture.md       #   System design, APIs, scaling
│   ├── 07-demo-overview.md      #   5 journeys, two demo users
│   └── 08-design-decisions.md   #   Tradeoffs and known limitations
│
├── api/                         # FastAPI server
│   ├── app.py                   #   ASGI app with CORS and lifespan
│   ├── routes.py                #   All endpoints (video/complete, quiz/submit, etc.)
│   └── schemas.py               #   Pydantic request/response models
│
├── engine/                      # Core learning engine
│   ├── loop.py                  #   Orchestrates video-complete and quiz flows
│   ├── classifier.py            #   User state classifier (rule-based)
│   ├── recap_engine.py          #   Concept-ranked recap bullet selection
│   ├── quiz_engine.py           #   Difficulty-adaptive question selection
│   ├── evaluator.py             #   Binary answer evaluation
│   ├── knowledge_updater.py     #   EMA-based per-concept score updates
│   ├── recommender.py           #   Gap-scored recommendation with series logic
│   ├── recall_scheduler.py      #   Spaced repetition scheduling
│   └── progress_update.py       #   User-facing progress messages
│
├── preprocessing/               # Offline LLM pipeline
│   ├── pipeline.py              #   Orchestrator with idempotency checks
│   ├── concept_extractor.py     #   LLM-based concept coverage scoring
│   ├── recap_generator.py       #   LLM-generated recap bullets
│   └── question_generator.py    #   LLM-generated quiz questions
│
├── db/                          # Database layer
│   ├── base.py                  #   SQLAlchemy engine and session factory
│   ├── models.py                #   ORM models (User, Video, WatchHistory, RecallQueue)
│   ├── operations.py            #   CRUD helpers
│   └── init_db.py               #   Table creation script
│
├── storage/                     # Object storage abstraction
│   ├── base.py                  #   StorageClient ABC and factory
│   └── minio_client.py          #   MinIO implementation
│
├── llm/                         # LLM client abstraction
│   ├── base.py                  #   LLMClient ABC and factory
│   ├── anthropic_client.py      #   Anthropic implementation
│   └── prompts.py               #   Prompt templates for preprocessing
│
├── config/                      # Configuration
│   ├── settings.py              #   Env-based settings loader
│   └── taxonomy.py              #   Concept taxonomy and category adjacency
│
├── data/                        # Seed data and transcripts
│   ├── seed_db.py               #   Seeds SQLite with users and videos
│   ├── seed_users.py            #   User profile definitions
│   ├── reset_db.py              #   Restores DB to seed state
│   ├── transcripts_raw.py       #   Raw transcript text
│   ├── write_transcripts.py     #   Writes transcript .txt files
│   └── seed_transcripts/        #   7 aspiration video transcripts
│
├── demo/                        # Streamlit demo (calls API over HTTP)
│   ├── app.py                   #   Entry point (tabs, theme toggle, reset)
│   ├── api_client.py            #   httpx wrapper for all FastAPI endpoints
│   ├── pages/                   #   Journey pages + sandbox
│   │   ├── journey_core.py      #     J1: Priya full loop
│   │   ├── journey_compare.py   #     J2: Rahul counterfactual
│   │   ├── journey_compound.py  #     J3: Priya compounds
│   │   ├── journey_recall.py    #     J4: Day 2 recall
│   │   ├── journey_utility.py   #     J5: Utility content gate
│   │   └── sandbox.py           #     Free-form exploration
│   └── components/              #   Shared UI components
│       ├── html_blocks.py       #     Cards, nav, code blocks
│       ├── user_panel.py        #     Learner-facing panels
│       ├── system_panel.py      #     System reasoning panels
│       ├── state_display.py     #     Knowledge charts and JSON
│       └── preprocessing_panel.py #   LLM pipeline viewer
│
└── tests/                       # 79 tests across 10 files
    ├── test_api_endpoints.py    #   HTTP-level API tests (11)
    ├── test_db_operations.py    #   DB CRUD tests (14)
    ├── test_knowledge_updater.py #  EMA update tests (13)
    ├── test_recall_scheduler.py #   Interval logic tests (11)
    ├── test_recommender.py      #   Recommendation tests (8)
    ├── test_classifier.py       #   Classification tests (8)
    ├── test_full_loop.py        #   End-to-end loop tests (6)
    ├── test_storage_client.py   #   MinIO round-trip tests (5)
    ├── test_llm_client.py       #   LLM client tests (3)
    └── test_bootstrap.py        #   Smoke test (1)
```

---

## Troubleshooting

**Port already in use:**
`saathi demo` handles this automatically. It scans for free ports starting from 8000 (FastAPI) and 8501 (Streamlit), and wires them together. No manual steps needed. If you are running components independently (see section above), you need to handle ports yourself:

```bash
# Start FastAPI on a different port
uvicorn api.app:app --host 0.0.0.0 --port 8001

# Start Streamlit on a different port, telling it where FastAPI is
SAATHI_API_URL=http://localhost:8001 streamlit run demo/app.py --server.port 8502
```

**MinIO won't start:**
Check Docker is running (`docker info`). If port 9000 is taken, stop the conflicting container. MinIO data persists in `minio_data/`.

**"Could not reach API server" in the demo:**
The FastAPI server must be running before Streamlit. If using `saathi demo`, it starts automatically. If running manually, start FastAPI first.

**Preprocessing fails with API key errors:**
Preprocessing requires a valid `ANTHROPIC_API_KEY` in `.env`. If you don't have one, the demo still works. All artifacts are pre-generated and stored in MinIO. Only click "Re-run Pipeline (LLM)" if you specifically want to regenerate artifacts.

**Tests fail on storage tests:**
MinIO must be running (`docker compose up -d`) for `test_storage_client.py`.
