# Architecture

This document covers how Saathi is structured as a system: the components, the data stores, how they connect, and where the prototype differs from a production implementation. For the logic behind each component, see [05-solution-overview.md](05-solution-overview.md).

---

## System Diagrams

Three diagrams, one per system phase. The LLM layer only appears in ingestion. Session start and per-video are pure scoring, selection, and read/write logic with no LLM calls.

### Content Ingestion

Video ingestion is fully offline and async. It runs independently of any user interaction.

```mermaid
flowchart TD
    VU["Video Uploaded"]

    subgraph IngestionBackend["Content Pipeline - Async"]
        JQ["Job Queue"]
        PW["Preprocessing Worker - Concept Extraction, Recap, Questions"]
        JQ -.-> PW
    end

    subgraph IngestionExt["External Services"]
        LLM["LLM Provider - Anthropic / Gemini"]
    end

    subgraph IngestionStorage["Storage Layer"]
        OBJ[("Object Storage - Video Artifacts")]
    end

    VU -.->|async trigger| JQ
    PW -->|LLM calls| LLM
    PW -->|write artifacts| OBJ
```

### Per-Video Learning Loop

Fires at 80% watch completion. The full learning loop runs here: classification, recap, quiz, knowledge update, recommendation, and recall scheduling.

```mermaid
flowchart TD
    subgraph LLClient["Client"]
        W80["80 Percent Watch Completion"]
    end

    subgraph LLApi["API Layer - Stateless"]
        LB["Load Balancer"]
        FA["FastAPI Instance"]
        LB --> FA
    end

    subgraph LLEngine["Learning Engine"]
        USC["User State Classifier"]
        RE["Recap Engine"]
        QE["Quiz Engine"]
        EVAL["Response Evaluator"]
        KSU["Knowledge State Updater"]
        PU["Progress Update"]
        REC["Recommendation Engine"]
        RS["Recall Scheduler"]
        USC --> RE
        RE --> QE
        QE --> EVAL
        EVAL --> KSU
        KSU --> PU
        PU --> REC
        KSU --> RS
    end

    subgraph LLStorage["Storage Layer"]
        OBJ[("Object Storage - Video Artifacts")]
        UDB[("User Database - OLTP")]
    end

    W80 --> LB
    LB --> FA
    FA --> USC
    UDB -->|user state| USC
    OBJ -->|video artifacts| RE
    OBJ -->|video artifacts| REC
    KSU -->|state update| UDB
    RS -->|state update| UDB
```

### Session Start

Fires when the user opens the app. Surfaces pending recalls, runs the response through the evaluator, and updates the user's knowledge state and recall schedule.

```mermaid
flowchart TD
    subgraph SSClient["Client"]
        APP["User Opens App"]
    end

    subgraph SSApi["API Layer - Stateless"]
        LB2["Load Balancer"]
        FA2["FastAPI Instance"]
        LB2 --> FA2
    end

    subgraph SSFlow["Session Start"]
        RSURF["Recall Surface"]
        REVAL["Response Evaluator"]
        KSUR["Knowledge State Updater"]
        RSCHED["Recall Scheduler"]
        RSURF --> REVAL
        REVAL --> KSUR
        KSUR --> RSCHED
    end

    subgraph SSStorage["Storage Layer"]
        UDB2[("User Database - OLTP")]
    end

    APP --> LB2
    LB2 --> FA2
    FA2 --> RSURF
    UDB2 -->|user state| RSURF
    KSUR -->|state update| UDB2
    RSCHED -->|interval update| UDB2
```

---

## API Endpoints

FastAPI exposes five endpoints. They map directly to the three system phases.

**Session Start**

`POST /session/start`
Body: `{ user_id }`. Reads the user's recall queue from the database, filters by eligibility, ranks by priority, and returns the top 3-5 due recall entries. If nothing is due, returns an empty list and the client proceeds to normal browsing.

`POST /recall/answer`
Body: `{ user_id, recall_entry_id, answer_index }`. Passes the answer through the Response Evaluator, updates the knowledge state with recall alpha (0.15), and recalculates the recall interval. Returns whether the answer was correct and the updated concept score.

**Per-Video Learning Loop**

The loop is two calls because the quiz is interactive. The first call delivers the recap and quiz questions. The second call submits the answers.

`POST /video/complete`
Body: `{ user_id, video_id }`. Fires at 80% watch completion. Runs the User State Classifier, Recap Engine, and Quiz Engine in sequence. Returns the user's classified state, the selected recap bullets, and the quiz questions (including correct indices, which the client holds until the user submits).

`POST /quiz/submit`
Body: `{ user_id, video_id, answers: [{ concept, answer_index }] }`. Passes answers through the Response Evaluator, updates the knowledge state, writes the watch history entry, schedules recalls for quizzed concepts, and runs the Recommendation Engine. Returns the progress update and the recommended next video.

**Preprocessing**

`POST /admin/preprocess`
Body: `{ video_id, transcript }`. Runs the full preprocessing worker: concept extraction, recap generation, question generation. Writes all artifacts to object storage. This endpoint exists for the prototype only, as a way to trigger preprocessing manually before the demo. In production this is replaced by the async job queue.

---

## Technology Choices

| Layer | Prototype | Production |
|---|---|---|
| **Language** | Python | Python |
| **API** | FastAPI (local) | FastAPI (hosted) |
| **UI** | Streamlit, calls FastAPI over HTTP | Seekho's mobile client, calls FastAPI over HTTP |
| **User database** | SQLite via SQLAlchemy | Relational database, same SQLAlchemy ORM |
| **Object storage** | MinIO (local, S3-compatible) | Any S3-compatible object storage |
| **LLM provider** | Anthropic (Claude) | Gemini |

Every swap between prototype and production is a config change. SQLAlchemy abstracts the database dialect so only the connection string changes. MinIO implements the S3 API so only the endpoint and credentials change. The LLM swap is handled by the LLM layer, covered below.

---

## LLM Layer

A single `LLMClient` class is the only interface the preprocessing pipeline uses. It never references a provider directly.

Internally, `LLMClient` routes to a provider-specific wrapper based on a config value set at startup:

```
LLMClient
├── AnthropicWrapper   (prototype)
└── GeminiWrapper      (production)
```

Each wrapper implements the same interface: takes a prompt, returns a structured response. Switching providers is a config change, not a code change.

The LLM layer is only called during preprocessing. No component in the session start or per-video pipeline makes an LLM call.

---

## Components

| Component | Reads | Writes | Prototype | Production |
|---|---|---|---|---|
| **Preprocessing Worker** | Transcript | Object storage | Manual Python script | Async worker triggered via job queue |
| **User State Classifier** | User database | Nothing (passed in memory) | FastAPI reads SQLite | FastAPI reads relational database |
| **Recap Engine** | Object storage, user database | Nothing (passed in memory) | FastAPI reads MinIO and SQLite | FastAPI reads object storage and database |
| **Quiz Engine** | Object storage (question objects including correct indices), user database | Nothing (passed in memory) | FastAPI reads MinIO and SQLite | FastAPI reads object storage and database |
| **Response Evaluator** | User answer and correct index (both passed in memory from Quiz Engine) | Nothing (passed in memory) | Fully deterministic | Identical |
| **Knowledge State Updater** | Quiz or recall results, current scores | User database | FastAPI writes to SQLite | FastAPI writes to relational database |
| **Progress Update** | Before and after knowledge scores | Nothing (rendered to UI) | FastAPI returns string, Streamlit renders | FastAPI returns string, mobile client renders |
| **Recommendation Engine** | Object storage, user database | Nothing (passed in memory) | FastAPI reads MinIO and SQLite | FastAPI reads object storage and database |
| **Recall Scheduler** | Quiz results, concept scores | User database | FastAPI writes to SQLite | FastAPI writes to relational database |
| **Recall Surface** | User database | Nothing (passed in memory) | FastAPI reads SQLite | FastAPI reads relational database |

Component logic does not change between prototype and production. What changes is where they read from and write to.

---

## Data Layer

Three stores. Saathi owns two of them.

### Object Storage

Written once by the preprocessing worker at ingestion. Never updated after that. Contains the concept profile, recap bullets, and questions for every video.

MinIO runs locally for the prototype and exposes the same S3-compatible API as any production object store. In production, the endpoint URL and credentials point to the actual object store. No code changes.

### Raw Videos

Seekho's existing storage. Saathi does not own or manage this. The preprocessing worker takes a transcript as input, not the raw video file.

### User Database

Knowledge state, watch history, and recall queue all live in one database. One record per user.

SQLite serves as the database for the prototype. SQLAlchemy is the ORM. In production, only the connection string changes.

The recall queue lives in the same database as a set of entries per user. At session start, one query fetches all pending entries for that user. Filtering by eligibility and ranking by priority happen in application code. Priority is derived at read time, not stored. If a concept score changes between sessions, the ranking automatically reflects it.

```json
{
  "user_id": "priya_001",
  "knowledge": { ... },
  "watch_history": [ ... ],
  "recall_queue": [
    {
      "concept_key": "body_language",
      "source_video_id": "vid_003",
      "due_at": "2026-03-30T10:00:00Z",
      "interval_hours": 18,
      "missed_count": 0,
      "status": "pending",
      "last_question_id": null
    }
  ]
}
```

---

## Write Events

There are exactly two moments that write to the user database.

**After every quiz completes (per-video pipeline):**

1. Knowledge state updated with new concept scores
2. Watch history entry written for the video
3. New recall entries written for each concept quizzed

All three happen as a single atomic write.

**After a recall is answered (session start):**

1. Recall interval adjusted (doubled if correct, halved if wrong, minimum 12 hours)
2. Knowledge state updated with recall alpha (0.15)
3. Recall entry status updated and next `due_at` recalculated

---

## Deployment

**Prototype**

Two local processes: Streamlit and FastAPI. Streamlit is the demo UI. FastAPI owns all pipeline logic and data access. Data lives in SQLite and MinIO. The preprocessing worker is a separate Python script run manually before the demo, writing artifacts to MinIO and seeding SQLite with demo users.

**Production**

FastAPI runs hosted behind a load balancer. Seekho's mobile client replaces Streamlit. SQLite is replaced by a relational database and MinIO by production object storage. The preprocessing worker runs as an async job triggered on video ingestion via a job queue.

---

## Scaling

The interaction path has no LLM calls. Every user request hits the load balancer, routes to a stateless FastAPI instance, reads from the database and object storage, runs scoring and selection logic, and writes back. This path scales horizontally by adding FastAPI instances. It has no dependency on LLM provider availability, rate limits, or inference latency.

The database handles concurrent writes through connection pooling and row-level locking. Two users updating their own records never block each other.

Preprocessing scales via the job queue. A video upload triggers a job. Workers process jobs in parallel. LLM rate limits apply here but preprocessing is offline and async so it does not affect the interaction path.

**Conversational mode is a different problem.**

The full Saathi vision includes real-time conversation between users and an AI. Every message in that flow is an LLM call. At Seekho's scale that means millions of concurrent requests, direct exposure to provider rate limits and inference latency, and per-request cost that compounds with usage. The proactive loop in this prototype avoids this entirely by moving all LLM work offline. Conversational mode needs a separate architecture discussion before it is built.

---

*← [Solution Overview](05-solution-overview.md)* | *[Demo Overview →](07-demo-overview.md)*
