# Saathi: Solution Summary

This is the high-level summary of my thinking and proposal. Each section maps to a detailed doc. Read this first, then go deeper where needed.

---

## 1. The Company

*Full detail: [documentation/01-background.md](documentation/01-background.md)*

Seekho is India's largest short-form micro-learning platform: 25M MAU, 100M+ downloads, content in English, Hindi and Hinglish. Subscription model at ₹200/month, no ads, no free tier. $28M Series B in August 2025 (Bessemer, Lightspeed, Elevation, Goodwater), ~$120-130M valuation, FY24 revenue of ₹11.5 crore growing 475% YoY.

Seekho works because of trust, curation, and format. It is a trusted filter in a market where bad advice has real consequences.

---

## 2. The Assignment

*Full detail: [documentation/02-original-problem.md](documentation/02-original-problem.md)*

Seekho asked for an "AI Revision Coach": post-video recap, adaptive quiz, recommendation, and recall scheduling. I propose exactly this, but with a different framing. Instead of a coach that reacts after a video, I wanted to build a companion that knows who it's talking to before it says anything.

---

## 3. The Vision: Saathi

*Full detail: [documentation/03-ai-vision.md](documentation/03-ai-vision.md)*

**Saathi** (Hindi: companion) has two modes. **Proactive Mode** is the closed learning loop that activates after videos. This is what the prototype implements. **Conversational Mode** is a grounded chat interface (out of scope for now).

Seekho currently has Coach, which appears to be stateless, generic, and reactive. Saathi is the inverse: stateful, personalized, and proactive.

**My hypothesis about users:** I think they fall into two types. **Information Seekers** come for a specific need, watch 1-3 videos, and leave. **Aspiration Seekers** come with a longer-term goal, return regularly, but drop off when progress isn't visible. My central assumption is that everyone starts as an IS, and the growth lever is converting them to AS.

**What drives retention:** I believe Tier 2/3 users return for the feeling of moving forward, not leaderboards or points. They need to see themselves as different from their past self. They're not buying videos. They're buying the feeling of growth.

**How Saathi adapts:** Content type is the first gate: entertainment gets no loop, utility gets a recommendation only, aspiration activates the learning loop. Within aspiration content, the system classifies each user on two dimensions (type, maturity) to determine the intensity. Same video, different user, completely different experience. When the user opens the app, a separate session-start check runs first: if recalls are due they surface before anything else, and if the user completed a series last session they see a milestone. Neither of these is part of the per-video pipeline.

**The emotional north star:** Every touchpoint should answer one question from the user's perspective: am I moving forward?

**The data moat:** With Saathi running, Seekho starts collecting data no competitor can replicate: which concepts users forget, what converts Information Seekers into Aspiration Seekers, what triggers return after drop-off. That data compounds with scale and becomes the real long-term defensibility, not the content itself.

---

## 4. What This Prototype Builds

*Full detail: [documentation/04-scoped-problem.md](documentation/04-scoped-problem.md)*

The proactive learning loop: watch a video, classify the user, deliver a personalized recap, run a quiz, update knowledge state, show a progress update, recommend the next video, schedule recall. The loop is closed and every interaction makes the system smarter.

Design decisions: classify before acting, target weak concepts not generic summaries, keep everything under two minutes, no leaderboards, no pressure on new users.

---

## 5. How It Works

*Full detail: [documentation/05-solution-overview.md](documentation/05-solution-overview.md)*

The system runs in three phases. All LLM work happens in preprocessing. The session start and per-video pipeline are pure selection and scoring logic, fast with no LLM calls.

**Preprocessing (once per video, at ingestion):**

**1. Concept Extractor:** Maps the video transcript to the fixed concept taxonomy for its category (4-5 concepts each). Produces a concept profile with coverage scores per concept. Concepts below 0.2 coverage are excluded. Only skill-learning categories get concept mappings.

**2. Recap Bullet Generator:** For each concept in the profile, generates two recap bullets: one IS-flavored (low pressure, immediate usefulness) and one AS-flavored (richer, frames the concept as part of ongoing skill development). Both stored per concept. At interaction time, the system selects which version to show based on user type.

**3. Question Generator:** For each concept, generates questions at easy, medium, and hard difficulty. Multiple questions per level to support rotation. Stored in the video artifacts alongside the concept profile and recap bullets, used for both the in-session quiz and future recall.

**Session Start (once per session, before browsing):**

When a user opens the app, two checks run before normal browsing begins. If pending recalls are due, the top 3-5 surface first by priority (urgency x importance). The user can complete them or dismiss and go straight to browsing. If the user finished a content series in their previous session, a milestone summary shows after recalls (or immediately if none are due). Both checks are independent of the per-video pipeline.

**Per-Video Pipeline (fires at 80% watch completion):**

**4. User State Classifier:** Reads profile and watch history, outputs content type, user type, and maturity. Content type is the first gate: entertainment and utility get a recommendation only. Aspiration activates the full pipeline. User type (IS, Converting, AS) and maturity (New, Warming Up, Established) determine intensity within aspiration content.

**5. Recap Engine:** Selects pre-generated bullets ranked by coverage x user gap. IS users see the top 2 IS-flavored bullets. AS and Converting users see the top 2 or 3 AS-flavored bullets. No LLM at this step.

**6. Quiz Engine:** Selects questions from the pre-generated bank for the same concepts the recap covered. One question per concept. Difficulty set by the user's current score. Capped at medium for AS New and Converting. No LLM at this step.

**7. Response Evaluator:** Deterministic. Correct index check. No LLM. Skipped questions scored as 0. Skipped quiz means no recall scheduled.

**8. Knowledge State Updater:** EMA-based per-concept scores. Quiz alpha = 0.3, recall alpha = 0.15. Passive watch bump capped at 0.8. No passive decay.

**9. Progress Update:** Shows the user what changed after the quiz. "Body Language: 30% to 51%." Shifts to encouragement if scores dropped. Shown for AS and Converting users only.

**10. Recommendation Engine:** Outputs a single video with an explanation of why. Gap-weighted relevance scoring with softmax sampling. Temperature varies by user state. 80/15/5 same-category/adjacent/discovery pool split. 0.5 neutral prior for unseen categories.

**11. Recall Scheduler:** Writes recall entries for concepts that were quizzed. Only for AS Warming Up and Established users. Base intervals by score, correct doubles, wrong halves (min 12 hours). At session start, top 3-5 due recalls surface first by priority (urgency x importance). Questions drawn from the pre-generated bank, scoped to watched videos.

---

## 6. The Demo

*Full detail: [documentation/06-demo-overview.md](documentation/06-demo-overview.md)*

Streamlit app, two panels. Left shows what the learner sees. Right shows what the system is thinking. Two users: Priya (AS, weak spots pre-loaded) and Rahul (IS, empty state). Same video, completely different experience.

Step 0 runs first: the preprocessing worker runs on the demo transcript, generating concept profiles, IS and AS recap bullets per concept, and questions per concept and difficulty. This is where the only LLM calls happen. The right panel shows the LLM being called, the outputs, and the stored artifacts. The four journeys that follow make no LLM calls.

Four journeys: (1) Priya's full loop, showing how the pipeline selects and scores from pre-generated artifacts. (2) Rahul on the same video, classifier suppresses the loop, IS bullets and warm nudge only. (3) Priya follows the recommendation and watches video 2, everything adapts because her knowledge state changed. (4) Priya returns the next day, recalls surface first, spaced repetition in action. Journey 3 is the key one. It proves the system gets smarter with each interaction, not just that it works once.

---

## 7. Architecture

*Full detail: [documentation/07-architecture.md](documentation/07-architecture.md)*

The system has three distinct phases, each with its own diagram in the architecture doc.

**Content Ingestion (offline, async):** A video upload triggers a job on a queue. A preprocessing worker picks it up, calls the LLM layer, and writes all artifacts to object storage. This is the only place LLM calls happen. The job queue decouples ingestion from user interactions entirely.

**Per-Video Learning Loop (at 80% watch completion):** The user event hits a load balancer, routes to a stateless FastAPI instance, and runs the full learning engine: User State Classifier, Recap Engine, Quiz Engine, Response Evaluator, Knowledge State Updater, Progress Update, Recommendation Engine, and Recall Scheduler. The learning engine reads video artifacts from object storage and reads and writes user state to the user database. No LLM calls.

**Session Start:** The user opens the app, the request hits the same API layer, and the session start flow runs: surface pending recalls, evaluate responses, update knowledge state, and recalculate recall intervals. All reads and writes go to the user database.

**Prototype stack:** Streamlit calls FastAPI over HTTP. FastAPI owns all pipeline logic and data access. User state lives in SQLite. Video artifacts live in MinIO, which runs locally and implements the same API as any production object store.

**Production stack:** Same FastAPI backend, hosted behind a load balancer. SQLite replaced by a relational database. MinIO replaced by production object storage. Preprocessing replaced by an async worker triggered via job queue. Every swap is a config change, not a code change.

**LLM layer:** A single `LLMClient` class routes to the right provider wrapper based on config. Prototype uses Anthropic. Production uses Gemini. The pipeline never references a provider directly.

**Why this scales:** The interaction path has no LLM calls. FastAPI instances are stateless and scale horizontally. Rate limits and inference latency from the LLM provider only affect the offline ingestion pipeline, not users.

---

## 8. Design and Implementation

*Full detail: [documentation/08-design-document.md](documentation/08-design-document.md)*

*To be completed.*
