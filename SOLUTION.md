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

**How Saathi adapts:** Content type is the first gate: entertainment gets no loop, utility gets a recommendation only, aspiration activates the learning loop. Within aspiration content, the system classifies each user on three dimensions (type, maturity, session context) to determine the intensity. Same video, different user, completely different experience.

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

Nine components:

**1. User State Classifier:** Three-dimensional classification (type x maturity x session context). Runs first. Determines the loop behavior: IS users get a soft nudge, Converting users get a shorter loop, AS users get the full experience. Entertainment categories get no loop at all.

**2. Concept Extractor:** Maps transcripts to a fixed concept set per Seekho category (4-5 concepts each). Only skill-learning categories get concept mappings. Entertainment categories like Crime or Cricket are excluded. Concepts below 0.2 coverage excluded. Profiles are deterministic. Prototype details Career & Jobs; other categories follow the same pattern.

**3. Recap Engine:** Up to 3-bullet recap for AS users, 2-bullet soft recap for IS/Converting. Weighted by (video coverage x user gap). LLM-generated from transcript, guided by targeted concepts. Teaches before the quiz tests.

**4. Quiz Engine:** Lazy-loaded question bank keyed by (video_id, concept, difficulty, question_index). Top 3 concepts by (coverage x gap), 1 question each. LLM generates once, reuses forever.

**5. Response Evaluator:** Deterministic. Correct index check. No LLM. Skipped questions scored as 0. Skipped quiz means no recall scheduled.

**6. Knowledge State Updater:** EMA-based per-concept scores. Quiz alpha = 0.3, recall alpha = 0.15. Passive watch capped at 1.0. Asymmetric: success rewarded more than failure penalized. No passive decay.

**7. Progress Update:** Shows the user what changed after quiz. "Body Language: 30% -> 51%." Makes the emotional north star tangible. Shifts to encouragement if scores dropped.

**8. Recommendation Engine:** Outputs a single video with an explanation of why. Gap-weighted relevance scoring with softmax sampling. Temperature varies by user state. 80/15/5 same-category/adjacent/discovery split. 0.5 neutral prior for unseen categories.

**9. Recall Scheduler:** Per-user recall queue with priority ranking. Base intervals by score. Correct doubles interval, wrong halves it (min 12 hours). Daily cap of 3-5 questions. Questions drawn from quiz bank scoped to watched videos.

---

## 6. The Demo

*Full detail: [documentation/06-demo-overview.md](documentation/06-demo-overview.md)*

Streamlit app, two panels. Left shows what the learner sees. Right shows what the system is thinking. Two users: Priya (AS, weak spots pre-loaded) and Rahul (IS, empty state). Same video, completely different experience.

Four journeys: (1) Priya's full loop through all 9 components. (2) Rahul on the same video, classifier suppresses the loop, soft recap and warm nudge only. (3) Priya follows the recommendation and watches video 2, everything adapts because her knowledge state changed. (4) Priya returns the next day, recalls surface first, spaced repetition in action. Journey 3 is the key one. It proves the system gets smarter with each interaction, not just that it works once.

---

## 7. Architecture

*Full detail: [documentation/07-architecture.md](documentation/07-architecture.md)*

*To be completed.*

---

## 8. Design and Implementation

*Full detail: [documentation/08-design-document.md](documentation/08-design-document.md)*

*To be completed.*
