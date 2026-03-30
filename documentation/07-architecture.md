# Architecture

This document covers how Saathi is structured as a system: the components, the data stores, how they connect, and where the prototype differs from a production implementation. For the logic behind each component, see [05-solution-overview.md](05-solution-overview.md).

---

## System Diagram

Three phases. Two data stores. One LLM layer that only runs offline.

```mermaid
flowchart TD
    ART[("Video Artifacts\nS3")]
    UD[("User Database")]

    subgraph Offline["Offline: Video Ingestion"]
        TR["Transcript"] --> LLC["LLM Layer"]
        LLC --> PRE["Preprocessing Pipeline\nConcept Extraction, Recap Generation, Question Generation"]
    end

    subgraph SessionStart["Session Start"]
        OPEN["User opens app"] --> SURF["Recall Surface"]
        SURF --> RA["Recall Answered"]
    end

    subgraph PerVideo["Per-Video: 80% Watch Completion"]
        W80["80% watch completion"] --> USC["User State Classifier"]
        USC --> ENG["Recap + Quiz + Recommendation Engines"]
        ENG --> KSU["Knowledge State Updater + Recall Scheduler"]
    end

    PRE --> ART
    ART --> ENG
    UD --> SURF
    RA --> UD
    UD --> USC
    KSU --> UD
```

The LLM layer only appears in the offline phase. Everything in session start and per-video is selection, scoring, and read/write logic. No LLM calls happen at interaction time.

---

## Technology Choices

These apply to the whole system, not to any single component.

- **Language:** Python throughout.
- **LLM provider:** Anthropic (Claude) for the prototype. Seekho's production stack uses Gemini. The LLM layer is the single provider integration point, so swapping it requires no changes to the pipeline.
- **UI:** Streamlit for the demo. In production, Saathi's output surfaces inside Seekho's existing mobile client.
- **Data:** JSON files on disk for the prototype. S3 and a relational database in production.

---

## LLM Layer

The LLM layer is a single `LLMClient` class. The preprocessing pipeline only ever calls `LLMClient`. It never references a provider directly.

Internally, `LLMClient` routes to a provider-specific wrapper based on a config value set at startup:

```
LLMClient
├── AnthropicWrapper   (prototype)
└── GeminiWrapper      (production)
```

Each wrapper implements the same interface: takes a prompt, returns a structured response. The pipeline code does not change when the provider changes. Only the config does.

For the prototype, `LLMClient` is instantiated with `provider=anthropic`. For Seekho's production stack, it is instantiated with `provider=gemini`.

---

## Components

Each component has a single responsibility. The table below covers what it reads, its prototype implementation, and what changes in production.

| Component | Reads | Writes | Prototype | Production |
|---|---|---|---|---|
| **Preprocessing Pipeline** | Transcript | Video artifacts | Manual Python script, triggered by hand | Event-driven, triggers on video ingestion |
| **User State Classifier** | User database | Nothing (output passed in memory) | Python function, called inline | Same logic, called as part of backend service |
| **Recap Engine** | Video artifacts, user database | Nothing (output passed in memory) | Python function, reads JSON files | Same logic, reads from S3 and database |
| **Quiz Engine** | Video artifacts, user database | Nothing (output passed in memory) | Python function, reads JSON files | Same logic, reads from S3 and database |
| **Response Evaluator** | Quiz answers, correct indices from video artifacts | Nothing (output passed in memory) | Python function, fully deterministic | Identical, no changes needed |
| **Knowledge State Updater** | Quiz results, current user scores | User database | Python function, writes to JSON file | Same logic, writes to database |
| **Progress Update** | Before and after scores from knowledge state update | Nothing (rendered to UI) | String generated in Python, shown in Streamlit | Same logic, response sent to mobile client |
| **Recommendation Engine** | Video artifacts, user database | Nothing (output passed in memory) | Python function, reads JSON files | Same logic, reads from S3 and database |
| **Recall Scheduler** | Quiz results, concept scores | User database (recall queue) | Python function, appends to JSON file | Same logic, writes rows to database |

The component logic does not change between prototype and production. What changes is where they read from and write to.

---

## Data Layer

Three stores. Saathi owns two of them.

### Video Artifacts (S3)

Written once by the preprocessing pipeline. Never updated after that. Contains the concept profile, recap bullets, and questions for every video.

S3 (or equivalent object storage) is the right fit because these files are written once and read many times. The read pattern is high volume and predictable. The write pattern is rare and offline.

In the prototype, these live in `video_artifacts.json` on disk. The access pattern is identical: written during preprocessing, read during session interactions.

### Raw Videos

Seekho's existing storage. Saathi does not own or manage this. The preprocessing pipeline reads a transcript as its input, not the raw video file.

### User Database

Everything about a user lives here: knowledge state, watch history, and recall queue. One record per user.

A relational database is the right fit because user state is written frequently and needs to be reliable. When a quiz completes, knowledge state, watch history, and recall entries all update together. These writes need to be atomic: either all of them save or none of them do. A JSON file on disk cannot guarantee this under concurrent access.

In the prototype, user state lives in `users.json` and the recall queue in `recall_queue.json`. Both are read and written synchronously within a single process, so concurrency is not an issue at demo scale.

The recall queue is not a separate system. It is a list of entries inside the user record, each carrying enough state to surface, filter, and reschedule without external logic.

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

Priority is derived at read time, not stored. At session start, eligible entries are filtered (time since last recall >= interval) and ranked by `urgency x importance`. The top 3-5 are surfaced. No priority score is ever written to the queue. This means if a concept score changes between sessions, the ranking automatically reflects it.

---

## Write Events

There are exactly two moments that write to the user database.

**After every quiz completes (per-video pipeline):**

1. Knowledge state updated with new concept scores
2. Watch history entry written for the video
3. New recall entries written for each concept quizzed

All three happen together as a single write. Atomic in production, sequential in the prototype.

**After a recall is answered (session start):**

1. Recall interval adjusted (doubled if correct, halved if wrong, minimum 12 hours)
2. Knowledge state updated with recall alpha (0.15)
3. Recall entry status updated and next `due_at` recalculated

These are separate from the per-video writes and only happen during the session start recall flow.

---

## Deployment

**Prototype**

A single Streamlit process running locally. All components are Python functions called inline within the same process. Data is read from and written to JSON files on disk. The preprocessing pipeline is a separate script run manually before the demo. No network calls except to the Anthropic API during preprocessing.

**Production**

The preprocessing pipeline runs as an async worker triggered on video ingestion. A new video entering Seekho's catalog queues a preprocessing job. The worker runs the pipeline and writes artifacts to S3. No human trigger required.

The per-video pipeline and session start logic run as a backend service. The mobile client sends events (80% watch completion, session open) and receives structured responses. The backend reads from S3 and the user database, runs the pipeline logic, and writes updates back to the database.

The Streamlit demo UI is replaced by Seekho's existing mobile client. Saathi's output is a structured response the client renders. The pipeline logic itself does not change.
