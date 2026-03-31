# Saathi: Solution Summary

> Saathi is a stateful learning companion for Seekho that closes the loop after every video. It classifies users by type and learning maturity, targets their weakest concepts, runs a personalized quiz, and schedules spaced recalls. All LLM work happens offline at ingestion. Runtime is deterministic scoring and selection, no LLM calls.

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

## What Is Different

**vs. chatbots and conversational AI**
- Saathi initiates the learning interaction. It does not wait for the user to ask.
- Before saying anything, the system knows who the user is: their type, their maturity, their concept scores, their overdue recalls.
- The intelligence is the knowledge model, not the LLM. Even in conversational mode, the LLM generates language. What it says, when, and why is driven by a persistent model of the user built across every session.

**vs. generic quiz systems**
- Questions are selected based on this user's weakest concepts in this category, not the video's general topic.
- Difficulty adapts to the user's current score per concept, not a global difficulty setting.
- The quiz result updates a persistent knowledge model that changes every future interaction.

**vs. recommendation systems**
- Recommendations are scored against this user's current knowledge gaps, not content similarity or collaborative filtering.
- The goal is learning advancement, not watch time.

---

## What This Is NOT

- Not a generic chatbot. Saathi includes conversational mode in the full vision, but the intelligence driving it is a persistent knowledge model, not a stateless prompt. A chatbot reacts to what the user says. Saathi acts on what it knows about the user.
- Not an LLM wrapper. The LLM is a content generation tool used at ingestion. The engine that classifies users, scores knowledge, targets weak concepts, and schedules recalls is deterministic logic running on a live knowledge state.
- Not gamification. No points, no streaks, no leaderboards. Progress is shown through actual concept score movement.

---

## 4. What This Prototype Builds

*Full detail: [documentation/04-scoped-problem.md](documentation/04-scoped-problem.md)*

The proactive learning loop: watch a video, classify the user, deliver a personalized recap, run a quiz, update knowledge state, show a progress update, recommend the next video, schedule recall. The loop is closed and every interaction makes the system smarter.

Design decisions: classify before acting, target weak concepts not generic summaries, keep everything under two minutes, no leaderboards, no pressure on new users.

---

## Why This Matters for Seekho

- **Retention.** Aspiration Seekers drop off when progress is not visible. Saathi makes progress visible after every session. The recall loop gives users a concrete reason to return.
- **IS to AS conversion.** Every IS user is a potential AS user. The adjacent recommendation pool surfaces aspiration content to IS users without pressure. The system tracks engagement signals to detect when conversion is happening.
- **No content changes required.** Saathi runs entirely on existing videos and transcripts. Seekho does not need to reshoot, re-edit, or re-categorize anything.
- **Learning behavior data.** Watch behavior tells you what users clicked. Learning behavior tells you what they actually retained, which concepts they struggle with, and what brings them back. That data does not exist anywhere else and compounds with scale.

---

## 5. How It Works

*Full detail: [documentation/05-solution-overview.md](documentation/05-solution-overview.md)*

The system runs in three phases. All LLM work happens in preprocessing. The session start and per-video pipeline are pure selection and scoring logic, fast with no LLM calls.

**Preprocessing (once per video, at ingestion):**

**1. Concept Extractor:** Maps the video transcript to the fixed concept taxonomy for its category (4-5 concepts each). Produces a concept profile with coverage scores per concept. Concepts below 0.2 coverage are excluded. Only aspiration categories get concept mappings.

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

**10. Recommendation Engine:** Outputs at most two slots. Slot 1 is series continuation: if the user is mid-series, the next episode fills Slot 1 via direct lookup with no scoring. If the series is finished, Slot 1 is empty. Slot 2 pool is built from series representatives (one per series). Never-started and mid-series representatives carry no penalty. Aspiration completed series re-enter as episode 1 with a revisit penalty based on average series quiz score and time decay from completion. Utility and entertainment completed series are excluded entirely. Aspiration Slot 2: two-stage bucket sampling. First roll a bucket (80% same-category, 15% adjacent, 5% discovery), then sample within the chosen bucket proportional to gap-weighted relevance using softmax with user-maturity temperature. Entertainment: 40/30/30 split, no gap scoring. Utility: 50/30/20 split, no gap scoring.

**11. Recall Scheduler:** Writes recall entries for concepts that were quizzed. Only for AS Warming Up and Established users. Base intervals by score, correct doubles, wrong halves (min 12 hours). At session start, top 3-5 due recalls surface first by priority (urgency x importance). Questions drawn from the pre-generated bank, scoped to watched videos.

---

## 6. Architecture

*Full detail: [documentation/06-architecture.md](documentation/06-architecture.md)*

The system has three distinct phases, each with its own diagram in the architecture doc.

**Content Ingestion (offline, async):** A video upload triggers a job on a queue. A preprocessing worker picks it up, calls the LLM layer, and writes all artifacts to object storage. This is the only place LLM calls happen. The job queue decouples ingestion from user interactions entirely.

**Per-Video Learning Loop (at 80% watch completion):** The user event hits a load balancer, routes to a stateless FastAPI instance, and runs the full learning engine: User State Classifier, Recap Engine, Quiz Engine, Response Evaluator, Knowledge State Updater, Progress Update, Recommendation Engine, and Recall Scheduler. The learning engine reads video artifacts from object storage and reads and writes user state to the user database. No LLM calls.

**Session Start:** The user opens the app, the request hits the same API layer, and the session start flow runs: surface pending recalls, evaluate responses, update knowledge state, and recalculate recall intervals. All reads and writes go to the user database.

**Prototype stack:** Streamlit calls FastAPI over HTTP via a thin `api_client` module (httpx). FastAPI owns all pipeline logic and data access. User state lives in SQLite. Video artifacts live in MinIO, which runs locally and implements the same API as any production object store. The demo showcases this architecture live. Every interaction in the Streamlit UI flows through the API layer, same as a production client would.

**Production stack:** Same FastAPI backend, hosted behind a load balancer. SQLite replaced by a relational database. MinIO replaced by production object storage. Preprocessing replaced by an async worker triggered via job queue. Every swap is a config change, not a code change.

**LLM layer:** A single `LLMClient` class routes to the right provider wrapper based on config. Prototype uses Anthropic. Production uses Gemini. The pipeline never references a provider directly.

**Why this scales:** The interaction path has no LLM calls. FastAPI instances are stateless and scale horizontally. Rate limits and inference latency from the LLM provider only affect the offline ingestion pipeline, not users.

---

## 7. The Demo

*Full detail: [documentation/07-demo-overview.md](documentation/07-demo-overview.md)*

Streamlit app calling the FastAPI server over HTTP, two panels, navigated via top-level tabs. Left panel shows what happens on the client side. "Learner sees this" cards (blue border) show what the learner actually sees in production, and event cards (grey border) provide narrative context. Right panel shows what the system is thinking, rendered as code/JSON blocks with orange borders. A light/dark mode toggle and a prominent Reset Demo button sit in the top right. Back/Next navigation at every step lets the presenter move forward and backward freely. Two users: Priya (AS, weak spots pre-loaded) and Rahul (IS, empty state). Same video, completely different experience. Every data point shown is computed by the FastAPI backend. The demo showcases the full production-like architecture.

What the demo proves: system behavior changes based on user state not content alone, no LLM calls happen in the interaction path, the learning loop compounds across sessions, and recommendations are personalized by content type (gap-driven for aspiration, series-entry distribution for entertainment and utility).

All aspiration video artifacts are pre-generated and loaded into MinIO before the demo starts, so the journeys work immediately. Each aspiration journey (1, 2, 3) has a pre-start card with a **Start Journey** button on the left and a **Preprocess** button on the right. Clicking Preprocess runs the pipeline live for that journey's video, showing the transcript, LLM calls, concept profile, recap bullets, and stored artifacts in the right panel. The journeys use the pre-existing artifacts either way, so the demo runs without an API key if preprocessing is never triggered. Journey 4 (recall) and Journey 5 (utility) have no preprocessing button. Journeys 1, 2, 3, and 5 end at the recommendation step. Journey 4 ends after recalls are complete.

Five journeys: (1) Priya's full loop on vid_001, showing how the pipeline classifies, recaps, quizzes, and recommends. The recommendation shows two slots: Slot 1 is the next episode in the same series she just watched, Slot 2 is the gap-scored engine pick. (2) Rahul on the same video, a counterfactual proof: same input, different state, different output. Rahul gets IS bullets and a warm nudge only, no quiz or recall. (3) Priya follows one of the two recommendation slots from Journey 1 and watches the next video. Everything adapts because her knowledge state changed. Journey 3 branches depending on which slot Priya clicks. (4) Priya returns the next day: the demo passes a simulated timestamp of 24 hours later to the session start call so the recall entries from Journey 1 surface as due. Spaced repetition in action. (5) Rahul watches a utility video, the content type gate fires, no learning loop runs, and the recommendation uses the 50/30/20 bucket formula instead of gap scoring. Journey 3 is the key one. It proves the system gets smarter with each interaction, not just that it works once.

A Sandbox tab sits alongside the five journeys. The presenter selects any user, any video, and any completion rate and runs the full pipeline on demand via the same API calls. All runs write to the live database; click Reset Demo to restore seed state after experimenting. This handles the inevitable evaluator question, "what happens with this combination?", with a live answer instead of a verbal one.

---

## 8. Design Decisions

*Full detail: [documentation/08-design-decisions.md](documentation/08-design-decisions.md)*

The key decisions and their reasoning: why all LLM calls are offline, why EMA uses separate alphas for quiz and recall, why the taxonomy is fixed at 4-5 concepts per category, why recall scheduling uses simple intervals over SM-2, why the user state classifier is rule-based, and why the quiz splits into two API calls. Known limitations and future directions are covered in the final section.

---

*Next: [Documentation Index](documentation/00-index.md)*
