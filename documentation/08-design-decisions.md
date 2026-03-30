# Design Decisions

This document explains the reasoning behind key choices in Saathi's design.

- [05-solution-overview.md](05-solution-overview.md) describes what the system does
- [06-architecture.md](06-architecture.md) describes how the system is structured

This document covers why it is designed this way. Each section states the decision, the reasoning, and the tradeoffs. Where relevant, what was considered and rejected is included.

---

## 1. Design Principles

Four invariants that shaped every decision below.

**No LLM in the runtime path.** All user interactions are deterministic, fast, and independent of LLM availability. Every personalized response is a selection from pre-generated artifacts, not live inference.

**System-driven, not user-driven.** The system decides what to surface based on the user's knowledge state. Users browse and watch. The system closes the loop.

**Knowledge state as the central abstraction.** Every personalization decision, recap targeting, quiz difficulty, recall priority, recommendation ranking, flows from per-concept scores. Without a live knowledge model, none of the loop's personalization is possible.

**Separation of generation and interaction.** LLMs generate content offline at ingestion time. Runtime is selection and scoring logic only.

---

## 2. LLM Usage: Offline Only

All LLM calls happen during video preprocessing. None happen during user interactions.

The core reason is scale. At Seekho's scale, putting LLM calls in the runtime path means millions of concurrent inference requests, direct exposure to provider rate limits and latency spikes, and per-interaction cost that compounds with usage. Moving all generation offline eliminates this entirely.

The secondary benefits follow naturally: interactions are fast, costs are predictable, the system works even if the LLM provider is unavailable, and the preprocessing artifacts are inspectable and testable before any user sees them.

The tradeoff is that responses cannot adapt to specific real-time context. The recap a user sees is selected from pre-generated bullets, not written for them in the moment. In practice this is acceptable. The selection logic is personalized (it targets the user's weak concepts at their current score level), even if the underlying text was generated at ingestion time.

Calling the LLM at quiz or recap time was the obvious alternative and was rejected early. It would introduce inference latency into every interaction, hallucination risk into the evaluation path, and unpredictable per-session cost.

---

## 3. Knowledge State: EMA with Separate Alphas

Per-user, per-concept mastery scores from 0 to 1, updated using Exponential Moving Average.

Two alpha values are used intentionally. Quiz interactions use alpha 0.3. Recall interactions use alpha 0.15.

```
quiz:   new_score = current_score + 0.3 × (quiz_score - current_score)
recall: new_score = current_score + 0.15 × (result - current_score)
```

The difference reflects confidence in the signal. A quiz happens immediately after watching a video: attention is high, the content is fresh, and the signal is strong. A recall happens hours or days later and tests whether knowledge stuck, not whether the user understood something just explained to them. A smaller alpha means the recall result updates the score more conservatively. A correct recall is a stronger endorsement of mastery than an immediate quiz answer, but a wrong recall should also move the score less aggressively downward.

The passive watch bump is separate from both:

```
new_score = min(0.8, score + 0.1 × completion_rate × concept_score)
```

Watching is a weak signal. The bump is small and capped at 0.8. The cap means passive engagement alone cannot produce a high mastery score. Without it, a user who watches many videos but never quizzes would accumulate high scores with no evidence of actual learning.

No passive decay is applied. Scores only drop when a quiz or recall test fails. Applying passive decay would degrade the knowledge state based on the passage of time alone, which is not a fair signal. If a user has not been tested recently, the system does not know whether they have forgotten anything.

EMA was chosen over binary mastery (too coarse, a single wrong answer erases all prior learning) and full Bayesian knowledge tracing (too complex to calibrate without historical data, better suited for a later version).

---

## 4. Fixed Concept Taxonomy

Each aspiration category maps to 4-5 fixed concepts. Utility and entertainment categories get no concept mapping.

The reason for fixing the taxonomy is consistent tracking. If concepts were derived dynamically from each video, two videos covering the same skill would produce incompatible concept names and there would be no way to accumulate a user's knowledge state across videos in the same category. The taxonomy is what makes per-concept scores meaningful over time.

The 4-5 concept limit is deliberate. More concepts produce a sparser knowledge state, fewer updates per concept per session, which makes EMA noisier and recommendations harder to target. Fewer concepts lose meaningful distinctions within a category.

Concepts below 0.2 coverage in a given video are excluded from that video's concept profile. A video that barely mentions a concept should not trigger a quiz question on it or schedule a recall for it.

A fully dynamic approach via embeddings was considered and rejected. It would make the knowledge state uninterpretable (scores mapped to embedding dimensions rather than human-readable concepts) and would make it impossible to explain to a user why they are being shown a particular video.

---

## 5. Multiple-Choice Questions and Deterministic Evaluation

All quiz and recall questions are multiple-choice with a stored correct index. The Response Evaluator compares the user's selected index against the stored one. No LLM is involved in evaluation.

Multiple-choice enables deterministic evaluation: instant, free, and producing a clean binary signal (correct or incorrect) that feeds directly into the EMA update. There is no ambiguity in scoring and no latency.

The tradeoff is that the format cannot assess open-ended responses or deep reasoning. This is acceptable. The goal of the quiz is to test recognition and recall of key concepts, not to evaluate the user's ability to explain them. Open-ended evaluation would require LLM calls in the runtime path, which the system explicitly avoids.

Questions are generated at three difficulty levels (easy, medium, hard) per concept at ingestion time. Multiple questions per level support rotation across quiz and recall sessions without repeating.

---

## 6. Recommendation: 2-Slot Output with Per-Content-Type Formulas

The recommendation engine always outputs at most two slots, not a single video.

**Slot 1 is series continuation.** If the user is mid-series, the next episode in that series fills Slot 1 with no scoring: it is a direct lookup by series ID and position. This is separated from the discovery engine entirely because series progression is deterministic and should never compete with gap-scored candidates. If the series is finished, Slot 1 is empty and only Slot 2 is shown.

**Slot 2 is the engine pick.** The formula that fills Slot 2 depends on the content type of the video just watched, because the same scoring approach does not apply across all three types.

For aspiration content, gap-based scoring is the right fit. The system has a concept taxonomy, per-user knowledge scores, and a clear learning objective. Scoring on knowledge gaps (rather than content similarity or collaborative filtering) keeps the recommendation tied to what the user needs to learn, not what similar users watched.

The pool is built from series representatives rather than individual videos. Each series contributes one candidate based on watch status: episode 1 if never started (no penalty), the next unwatched episode if mid-series (no penalty, it is always a new video), or episode 1 as a revisit candidate if the series is complete (revisit penalty applied). Completed aspiration series are not excluded. A series the user finished with poor quiz performance is genuinely worth surfacing again, and the revisit penalty handles suppression naturally.

The revisit penalty for completed series uses the average quiz score across all episodes and time decay from when the last episode was watched: `final_score = relevance x (1 - avg_series_quiz_score) x time_decay(days_since_completion)`. A recently completed, well-scored series is suppressed. An old, poorly-scored series resurfaces.

The candidate pool splits 80/15/5: 80% of series representatives from the same category, 15% from adjacent categories via an editorial adjacency map, and 5% random. The adjacent 15% is the mechanism by which IS users get exposure to aspiration content without pressure.

Softmax sampling over greedy ranking prevents the system from surfacing the same video every time the user's knowledge state is stable. Temperature varies by user state:

- AS Established: 0.3 (sharp targeting, the user is working on a skill)
- AS Warming Up: 0.5
- IS Warming Up: 0.8
- IS New: 1.2 (broader exploration, the user is still forming preferences)
- First session: 1.5

For entertainment and utility content, gap scoring is not applicable. There is no concept taxonomy for these types and the user is not building a knowledge model. A simplified distribution is used instead. Completed series are excluded from the pool entirely for these content types. There is no knowledge state to revisit and no learning value in re-surfacing a finished entertainment or utility series. Never-started and mid-series representatives follow the same logic as aspiration.

Entertainment distribution: 40% same entertainment category, 30% other entertainment categories, 30% aspiration content.

Utility distribution: 50% same utility category, 30% other utility categories, 20% aspiration content.

The aspiration bucket in both entertainment and utility distributions serves the same role as the adjacent 15% in the aspiration formula. It is how entertainment and utility users first encounter skill-building content.

Pure collaborative filtering was rejected because it ignores the learning goal. Greedy top-1 ranking was rejected because it produces repetitive recommendations for users with stable knowledge states. A single formula applied to all content types was rejected because gap scoring is meaningless without a concept taxonomy.

---

## 7. Recall Scheduling: Interval-Based, No Penalty for Misses

Recall entries are scheduled at one of three base intervals determined by the concept score at quiz time:

- Score below 0.4: 18 hours
- Score 0.4 to 0.6: 30 hours
- Score above 0.6: 48 hours

Lower scores surface sooner. Concepts the user has not mastered need more frequent reinforcement than concepts they are already strong on.

Correct recall doubles the interval. Wrong recall halves it, with a minimum of 12 hours. Success moves the concept further out; failure brings it back sooner.

Missed recalls are not penalized. If the user does not open the app, the recall entry stays pending and reschedules to the next session at the same interval. After 3 consecutive misses, the interval halves so the concept surfaces sooner. The user did not fail the recall by being absent, and degrading their knowledge state based on absence would be both unfair and counterproductive to retention.

Recall is only scheduled for AS Warming Up and Established users. IS users and AS New users do not receive recalls. IS users are not in a return habit, so surfacing recalls would be premature. AS New users are still building their knowledge base and the priority is acquisition, not retention testing.

SM-2 (the Anki algorithm) was considered and not adopted. It tracks per-item ease factors and review counts across many sessions and was designed for explicit flashcard study, not a loop embedded in a short-form video product. The simplified interval system is sufficient for this use case and is far easier to inspect and tune.

---

## 8. User State Classifier: Rule-Based Cascade

The classifier uses a five-step rule cascade, not a machine learning model. All steps evaluate the user's last 10 non-entertainment videos. The first matching step wins.

Step 1 checks utility dominance: if utility content makes up 50% or more of recent history, classify IS regardless of any aspiration signal. Step 2 checks aspiration depth: if the user has 3 or more videos in the same aspiration category in the last 10, classify AS. Step 3 is the new-user default: if the user has fewer than 5 non-entertainment videos total, classify IS. Step 4 checks aspiration breadth: if 70% or more of recent videos are aspiration content across multiple categories, classify AS. Step 5 is the converting fallback: everything else that has not matched by this point.

The order matters. Step 1 catches utility-heavy users before Step 2 misclassifies them as AS. Step 2 fires before Step 3 so a new user who immediately concentrates in one category is correctly classified as AS rather than defaulting to IS. Step 5 captures users in active transition.

A rule-based approach was chosen over an ML model for two reasons. First, there is no training data. The system is being built from scratch and there is no historical ground truth for which users are IS versus AS. Second, the rule-based classifier is transparent. In the demo, the right panel shows the classifier walking through each step explicitly. An ML model would not provide this visibility, which matters for evaluating whether the system is making real decisions.

The tradeoff is that hard thresholds can misclassify edge cases and the classifier does not adapt between updates. These are acceptable at this stage. The right approach is to collect behavioral data after launch and use it to train a more adaptive model once ground truth exists.

---

## 9. Quiz Split Into Two API Calls

The per-video pipeline uses two API calls.

`POST /video/complete` runs the classifier, recap engine, and quiz engine. It returns the recap bullets and quiz questions to the client. The client presents the quiz and collects answers.

`POST /quiz/submit` receives the answers, runs the Response Evaluator, updates the knowledge state, writes the watch history entry, schedules recalls, and runs the Recommendation Engine. It returns the progress update and the next recommended video.

Splitting is necessary because the quiz is interactive. The user must read the questions and choose answers before the evaluator can run. A single endpoint cannot handle this without holding a server-side connection open for the duration of the quiz, which does not scale.

The correct indices are included in the question objects returned by `/video/complete` and held by the client until submission. In the prototype this is fine. In production, correct indices would be withheld from the client response and only applied server-side during `/quiz/submit`.

---

## 10. Recall Queue in the User Record

The recall queue lives inside the user record rather than in a separate table.

The reason is query simplicity. At session start, one read fetches the full user record including all pending recalls. No join, no separate query, no risk of inconsistency between two stores.

Priority is calculated at read time, not stored. `priority = urgency × importance`, where `urgency = days_overdue + 1` and `importance = 1 - current_concept_score`. Storing priority would make it stale the moment the knowledge state changes. Calculating at read time means the recall ranking always reflects the user's actual current scores.

---

## 11. Prototype and Production: Config-Level Separation

The same application code runs in both prototype and production. What changes is configuration only.

SQLAlchemy abstracts the database dialect. The prototype uses SQLite. Production switches to a relational database by changing the connection string. MinIO implements the S3 API. The prototype runs MinIO locally. Production switches to any S3-compatible object store by changing the endpoint and credentials. The `LLMClient` routes to a provider wrapper based on a config value. Prototype uses Anthropic. Production uses Gemini.

The intent is that every prototype-to-production swap is one line in a config file, not a code change. This reduces the risk of the prototype and production diverging in behavior, which is the most common failure mode when prototype code is "ported" to production.

---

## 12. Known Limitations

**The system always targets weakness.** Every recap, quiz, and recommendation points at weak spots. This is right for learning velocity but will feel exhausting over time. Real learning systems mix challenge with consolidation. A better approach would occasionally serve easier questions on strong concepts and recommend content the user is likely to enjoy, not just content they need.

**The concept taxonomy takes time to scale.** Each skill-learning category needs a concept breakdown authored and reviewed before the pipeline can run. The process is LLM-assisted but human review is required before it goes live. Sub-skills also collapse into a single score: body language, for example, folds together eye contact, posture, and gestures. For the prototype with 4 categories this is manageable. Across Seekho's full catalog of 40 categories, the review bottleneck becomes the constraint.

**Recall question diversity is limited by watch history.** Questions are generated from specific video transcripts. If a user has only watched one video covering a concept, the recall pool is limited to that video's questions. Even with multiple questions per difficulty level, a small pool means repetition. The pool only grows as the user watches more videos covering the concept. Concept cards (short authored descriptions per concept, independent of any video) would solve this by providing a stable generation input regardless of watch history.

**No feedback loop from user behavior to content artifacts.** All preprocessing artifacts are set at ingestion and never updated. They reflect editorial judgment at the time a video was processed, not what happens when users engage with it. In practice these drift. A video tagged as having 0.9 coverage of a concept may consistently produce low quiz scores on it, which means the coverage score is wrong. A question labeled easy may have a 30% success rate, which means it is medium or hard. The signals to correct this already exist: quiz accuracy per concept per video, recall performance, and recommendation acceptance. What is missing is a pipeline that feeds them back into the artifacts. This is the most important missing piece for a production system.

**IS-to-AS conversion is passive.** The classifier detects user type from behavior but does not actively move IS users toward AS. The adjacent 15% recommendation pool is the only nudge. A more explicit conversion model that tracks how close an IS user is to the AS threshold and surfaces the right content to push them over it is a natural next step.

**No concept completion state.** There is no notion of finishing a topic. A user whose score reaches 0.9 on a concept still receives quiz questions and recommendations for it. The full solution is skill trees, described in [03-ai-vision.md](03-ai-vision.md). That design is not part of this prototype.

---

*Back to: [README](../README.md)*
