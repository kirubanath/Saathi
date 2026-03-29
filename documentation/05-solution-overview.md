# Solution Overview

This document describes each component of the proactive learning loop, with formulas and examples. For the full AI vision, see [03-ai-vision.md](03-ai-vision.md). For the scoped problem, see [04-scoped-problem.md](04-scoped-problem.md).

---

## How the Loop Runs

**Trigger:** The proactive loop fires when a user reaches 80% watch completion on a video. Most users who get to 80% have absorbed the content. Waiting for 100% loses users who skip the last few seconds.

**Session entry:** When a user opens the app and has pending recall questions, recalls surface first (top 3-5 by priority). After recalls are completed or dismissed, the user browses and watches normally.

**Full sequence after trigger:** Classify user state -> extract concepts -> generate recap -> run quiz -> evaluate responses -> update knowledge state -> show progress update -> generate recommendation -> schedule recall.

---

## Components

### 1. User State Classifier

Reads user history and session context to determine how Saathi behaves. Runs first, before anything else.

**Content types:**

Every Seekho category falls into one of three content types. This is a category-level classification, authored editorially.

- **Entertainment**: Not skill-learning. Crime, Horror, Cricket, Ramayan, Devotion, History. No concept mapping, no proactive loop. Saathi only offers recommendations.
- **Utility**: Skill-learning categories where users typically come for a specific, one-time answer. Sarkari Kaam, Mobile Tricks, Life Hacks. The content is useful but doesn't build toward a long-term skill. Concept mapping exists but the full loop is suppressed for IS users.
- **Aspiration**: Skill-learning categories where users build toward a longer-term goal. English Speaking, Career & Jobs, Business, Share Market, Exam Prep, Coding. The content compounds across sessions. This is where the full proactive loop runs.

Some categories could go either way (Finance could be utility or aspiration depending on the video). The default is set at the category level. Individual videos can override if needed, but for this prototype the category-level label is sufficient.

**Three dimensions:**

**User Type** (from watch history):

- **Information Seeker (IS):** 70%+ of watched content is utility, or fewer than 3 total videos watched.
- **Aspiration Seeker (AS):** 70%+ of watched content is aspiration, or 3+ videos in the same aspiration category.
- **Converting:** Mixed pattern. 30-70% aspiration content, or an IS user who has recently watched aspiration content for the first time.

**Maturity** (from tenure): New (0-7 days), Warming Up (1-4 weeks), Established (1+ month).

**Session Context** (from what they just watched or what they're returning to):

- Utility content: IS behavior, suppress full loop, gentle nudge only.
- Aspiration content: Full loop activates if user is AS or Converting.
- Series completion: User finished a content series, opportunity for a milestone progress update.
- Recall return: User opened the app with pending recalls. Recalls surface first before normal browsing.

The classifier also affects the recommendation engine's temperature parameter (more exploration for new users, more targeting for established ones).

**Loop behavior by user type and context:**


Content type is the first gate. If the content is entertainment or utility, the proactive loop does not run regardless of who the user is. The loop only activates on aspiration content, and then user type determines the intensity.

**Entertainment content (any user):** No loop. Recommendation only.

**Utility content (any user):** No recap, no quiz, no recall. Single recommendation with a warm message: "People who found this useful also liked..." The content answered a specific need. Don't quiz someone on how to link Aadhaar.

**Aspiration content (varies by user type):**

| User Type                      | What Saathi Does                                                                                                                 |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------- |
| IS (any maturity)              | Soft recap only (2 bullets, no quiz). Gentle nudge toward more content in this area: "Liked this? Here's where this topic goes." |
| Converting                     | Full recap. Shorter quiz (top 2 concepts instead of 3). Encouraging progress update even for small gains.                        |
| AS (New)                       | Full recap. Easy quiz only (difficulty capped at medium regardless of score). Build confidence first.                             |
| AS (Warming Up or Established) | Full loop: recap, quiz, progress update, recommendation, recall scheduled.                                                       |

**Special session contexts (any user type, any content type):**

- **Series completion:** User finished a content series. Milestone progress update summarizing growth across the series, then recommendation for what's next.
- **Recall return:** User opened the app with pending recalls. Recalls surface first (top 3-5 by priority). After completion or dismissal, normal browsing resumes.


The IS nudge is deliberately low-pressure. Rahul watches a Sarkari Kaam video about linking Aadhaar, gets his answer, and Saathi says: "Got it! Here's another one people found useful." No quiz, no score, no pressure. If he then watches an aspiration video, Saathi introduces itself gently with a soft recap and no quiz. The goal is to not scare away a user who is still deciding whether this platform is for them.

Demo users: Priya (AS, Warming Up, 14 days, pre-loaded weak spots in body_language and answering_structure at 0.3) and Rahul (IS, New, 3 days, empty knowledge state).

---

### 2. Concept Extractor

Maps video transcripts to a fixed concept taxonomy per category. Does not invent new concepts.

Seekho already categorizes every video on the platform. The app has ~40 categories: English Speaking, Career & Jobs, Business, Share Market, Exam Prep, Coding, Sarkari Kaam, Finance, Marketing, AI, Part Time Income, Instagram, Youtube, Astrology, Wellness, Editing, Mobile Tricks, Self-Growth, Agriculture, Startups, Fitness & Gym, Photography, Computer, and others including content categories like Crime, Horror, Devotion, Ramayan, and Cricket.

Not all of these are skill-learning categories. The proactive loop of concept extraction, quiz and recall only applies to categories where there are learnable concepts to track. Entertainment and content categories (Crime, Horror, Cricket, Ramayan, Devotion) don't get concept mappings. For these, Saathi's behavior is limited to recommendations.

For each skill-learning category, I define 4-5 concepts that represent the core learnable skills within it. This concept mapping is authored per category and is what Saathi uses to track mastery. The video's category comes directly from Seekho's existing classification, so I don't need to infer or assign it.

For this prototype, I pick 4 of Seekho's categories to demonstrate the structure. Only Career & Jobs is fully detailed: body_language, voice_modulation, answering_structure, handling_nervousness, preparation. The other 3 (English Speaking, Business, Share Market) are named but their concept breakdowns are not fleshed out. In production, every skill-learning category would get its own concept mapping following the same pattern.

Each video gets a concept profile: a dictionary of concept_key to coverage_score (0-1). Concepts with coverage below 0.2 are excluded from the profile. A video that briefly mentions body language should not trigger quiz questions on it. Example for a Career & Jobs video: {body_language: 0.9, voice_modulation: 0.8, answering_structure: 0.6, handling_nervousness: 0.5}. Profiles are deterministic. The concept mapping is fixed per category intentionally to prevent concept fragmentation and keep knowledge state stable across videos.

This level of precise profiling is possible because Seekho's content is short and focused.

---

### 3. Recap Engine

Generates a personalized recap weighted toward the user's weakest concepts, not a generic video summary. The recap is the "teach" moment in the loop. It reinforces the right takeaways from the video before the quiz tests whether they stuck.

**Targeting:**

Score each concept by (video coverage x user gap). Top 3 become the recap focus.

```
recap_priority[c] = concept_profile[c] x (1 - knowledge_state[c])
```

So if Priya's weakest concepts are body_language (score 0.3, gap 0.7) and answering_structure (score 0.3, gap 0.7), and the video covers body_language at 0.9 and answering_structure at 0.6, body_language gets the higher recap priority (0.9 x 0.7 = 0.63 vs 0.6 x 0.7 = 0.42). The recap focuses there first.

If the video covers fewer than 3 concepts above the 0.2 coverage threshold, the recap generates that many bullets. A 2-concept video gets 2 bullets.

For a new user (all scores at 0.0, all gaps at 1.0), the formula reduces to just video coverage. The recap targets whatever the video covers most, which is a reasonable default when there's no personalization signal yet.

**Input to LLM:**

- Video transcript
- Top 3 targeted concepts with their coverage scores
- User's current scores on those concepts (so the LLM knows whether to explain simply or assume some baseline)
- User's maturity level (New, Warming Up, Established)

**Output:**

Up to 3 bullets, one per targeted concept. Each bullet is 1-2 sentences. The tone is warm and conversational, appropriate for Tier 2/3 users. Think "advice from someone you trust" not "textbook excerpt."

**Example for Priya** (body_language at 0.3, answering_structure at 0.3) after watching "How to speak confidently in interviews":

> • Your body language speaks before you do. Sit upright, keep your hands calm, and make eye contact when answering.
> • When you get a question, pause for a second before answering. Structure your response: what you did, how you did it, and what happened.
> • Nervousness is normal. The interviewer is not judging your anxiety, they are judging your answers. Take a deep breath before your first response.

**Example for Rahul** (IS, new, empty state) watching the same video:

Rahul gets the IS nudge, not the full recap. See the loop behavior table in User State Classifier for what he sees instead.

The recap and quiz intentionally target the same concepts. The recap primes the user on what matters from this video. The quiz immediately tests whether they absorbed it. This is deliberate: teach then test on the same material.

---

### 4. Quiz Engine

Serves MCQs from a lazy-loaded question bank keyed by (video_id, concept, difficulty, question_index). First access generates questions via LLM and stores them permanently. All subsequent accesses reuse them.

The quiz targets the top 3 concepts by (video coverage x user gap). These are the same concepts the recap just covered. This is intentional: the recap primes the user on what matters, the quiz immediately tests whether they absorbed it. 1 question per concept. If the video covers fewer than 3 concepts above threshold, the quiz covers all of them. This gives a maximum of 3 questions per quiz session, keeping the total interaction under 2 minutes.

Difficulty is set by the user's current concept score:

- Score < 0.2: Easy (recognition)
- Score 0.2-0.5: Medium (application)
- Score > 0.5: Hard (synthesis)

This makes the system deterministic and measurable while keeping LLM usage minimal. The architecture supports multiple questions per concept if finer assessment resolution is needed later. The knowledge state formula (quiz_score = correct/total per concept) handles it naturally.

---

### 5. Response Evaluator

Deterministic MCQ evaluation. Compares selected answer index against stored correct index. Returns 1 (correct) or 0 (wrong) per question. No LLM at evaluation time.

If a user skips a question, it is scored as 0. The system cannot assume knowledge from silence. If the user skips the entire quiz, no quiz scores are recorded. The knowledge state only receives the passive watch bump and no recall is scheduled for those concepts.

Results are aggregated per concept: `quiz_score = correct_answers / total_questions` for that concept. With 1 question per concept in the current design, this is binary (1.0 or 0.0). This feeds directly into the Knowledge State Updater.

---

### 6. Knowledge State Updater

Maintains per-user, per-concept mastery scores (0-1) using Exponential Moving Average (EMA).

**Video Watch (passive):**

```
new_score = min(1.0, score + 0.05 x completion_rate)
```

Watching is a weak signal. Small bump, capped at 1.0 to prevent overflow. Doesn't confound quiz-driven learning.

**Quiz (active learning):**

```
quiz_score = correct_answers / total_questions  (per concept)
new_score = current_score + 0.3 x (quiz_score - current_score)
```

Example with body_language at 0.3: correct answer (quiz_score = 1.0) gives 0.3 + 0.3 x 0.7 = 0.51. Wrong answer (quiz_score = 0.0) gives 0.3 + 0.3 x (-0.3) = 0.21. The asymmetry is preserved: a correct answer moves the needle more than a wrong answer pulls it back, because the EMA target is bounded at 1.

**Recall (retention test):**

```
new_score = current_score + 0.15 x (result - current_score)
```

Recall uses a single question per concept, so result stays binary (1 or 0). Smaller alpha (0.15 vs 0.3) because recall tests existing knowledge, not new learning.

Scores never decay passively. They only drop when a quiz or recall test fails.

If the user skips the quiz entirely, only the passive watch bump applies. No recall is scheduled since there is no quiz-driven signal to test retention against.

---

### 7. Progress Update

After the knowledge state is updated, Saathi shows the user what changed. This is what makes the emotional north star ("Am I moving forward?") tangible.

The progress update shows which concepts improved and by how much. Example: "Body Language: 30% -> 51%". Accompanied by a short grounding message: "You're getting stronger at reading body language cues in interviews."

The update is shown only when at least one concept score increased. If the user got everything wrong and scores dropped, the update shifts to encouragement. It acknowledges the effort and frames the quiz as a learning moment, not a failure. Example: "These were tough questions. The good news is Saathi now knows exactly where to focus your next session."

This is a lightweight component. It reads the before/after scores from the knowledge state updater and generates a 1-2 line message. No complex logic.

---

### 8. Recommendation Engine

Selects the next video to recommend. The output is a single video with a brief explanation of why it was chosen. Example: "Based on what you just practiced, this video will help you work on your answering structure." The user sees one clear next step, not a list to choose from. The selection uses gap-weighted relevance scoring and softmax sampling.

**Step 1:** Build the candidate pool: 80% from the same category the user just watched, 15% from adjacent categories (editorial adjacency map), and 5% pulled at random from the full catalog.

The adjacent 15% is how IS users get gentle aspiration nudges. The random 5% is the discovery bucket: it gives genuinely new content a seat at the table regardless of category or user history. Without it, the system is fully controlled and users never stumble across something unexpected. All three buckets go into the same pool and compete on equal footing through the scoring steps below.

The editorial adjacency map defines which categories are related. Examples with real Seekho categories:

- Career & Jobs <> English Speaking (communication for career advancement)
- Career & Jobs <> Exam Prep (career pathway)
- Business <> Share Market (financial/business skills)
- Business <> Marketing (business growth)
- Business <> Startups (entrepreneurship)
- Finance <> Share Market (financial literacy)
- Sarkari Kaam <> Exam Prep (government job preparation)
- English Speaking <> Business (professional development)

This map is authored editorially and maintained as the category set evolves. For this prototype, only the adjacency between the 4 demo categories (Career & Jobs, English Speaking, Business, Share Market) is active.

*Future: collaborative filtering.* Right now the 5% is random. As Saathi accumulates user behavior data, this slot can be replaced with a collaborative signal: "users with a similar learning pattern to yours also watched X." This is how YouTube surfaces content outside your usual patterns without needing to understand the content itself. The architecture doesn't change, just what fills that 5%.

**Step 2:** Compute the gap vector: `gap[c] = 1 - assumed_score[c]`

Where:

```
assumed_score[c] = knowledge_state[c]   if the user has engaged with this category
                 = 0.5                  if the category is completely unseen
```

This is a heuristic local to the recommendation engine only. The stored knowledge state is not changed. It stays at 0.0 and only moves when real quiz data arrives. Without this heuristic, every concept in an unseen adjacent category would have gap=1, making all adjacent videos score identically high and the formula unable to differentiate between them. A neutral prior of 0.5 lets the gap formula still rank adjacent videos by their concept mix. Once the user actually engages and quiz data arrives, the real knowledge state takes over and the assumed_score is no longer used for that category.

**Step 3:** Score each video: `relevance = sum(concept_profile[c] x gap[c])`. This is a dot product of video coverage and user gaps. It captures how well the video targets your current weak spots, weighted by how much each concept the video covers.

Example: Priya with gaps of body_language=0.8, voice_modulation=0.2, answering_structure=0.6, handling_nervousness=0.4. Video A (heavy on body_language and answering_structure) scores 1.36. Video B (heavy on voice_modulation) scores 0.92. Video A wins because it targets her actual weak spots.

**Step 4:** For already-watched videos, apply a revisit penalty on top of relevance:

```
final_score = relevance x (1 - quiz_score_at_watch) x time_decay(days)
```

Where `time_decay(d) = 1 - exp(-d/30)`.

For new videos, `final_score = relevance` (no penalty).

If the user watched a video but skipped the quiz, use a default `quiz_score_at_watch = 0.5` (neutral). This means the revisit penalty is moderate. The video isn't heavily suppressed (the user might benefit from another try) but also doesn't surface as strongly as a video they genuinely struggled with.

The relevance score already handles "does this video still address your gaps" using current knowledge state, so step 4 only adds two things relevance can't capture: how badly you struggled when you watched it (`1 - quiz_score_at_watch`), and whether enough time has passed (`time_decay`). Both need to be meaningfully non-zero for a revisit to be worth recommending. A video you aced gets heavily suppressed regardless of time. A video you bombed yesterday barely surfaces. A video you bombed a month ago and still haven't mastered scores high.

**Step 5:** Sample from softmax with temperature varying by user state:

```
prob(video) proportional to exp(final_score / τ)
```

τ values: AS Established = 0.3 (sharp targeting), AS Warming Up = 0.5, IS Warming Up = 0.8, IS New = 1.2 (broad exploration), first session = 1.5. This prevents recommendation ruts.

---

### 9. Recall Scheduler

**The queue**

Every time a quiz completes on a concept, the recall scheduler writes an entry into that user's recall queue:

```json
{
  "user_id": "priya_001",
  "concept_key": "body_language",
  "source_video_id": "vid_003",
  "due_at": "2026-03-30T10:00:00Z",
  "interval_hours": 18,
  "missed_count": 0,
  "status": "pending",
  "last_question_id": null
}
```

The `last_question_id` tracks which question was most recently served for this concept, so recall can rotate through available questions and avoid repeats.

Over time a user builds up many entries across many concepts. The queue is fully per-user and computed dynamically each session.

**Intervals**

Base interval by concept score at quiz time: score < 0.4 = 18 hours, 0.4-0.6 = 30 hours, > 0.6 = 48 hours. Correct recall doubles the interval. Wrong recall halves it (minimum 12 hours).

Example: body_language at 0.51 after quiz. Base = 18 hours. First recall correct: next interval = 36 hours. Next recall wrong: interval = 9 hours, clamped to 12.

**Surfacing: ranking and daily cap**

A user who watches multiple videos per day can accumulate many due recalls quickly. At the start of each session, the system queries all due entries for that user and ranks them by priority:

```
priority = urgency x importance
urgency  = days_overdue + 1
importance = 1 - current_concept_score
```

Overdue recalls rank first. Among same-day recalls, weaker concepts rank higher. Only the top 3-5 are surfaced per session. The rest stay in the queue and surface in future sessions.

**Missed recalls**

If a recall was due but the user didn't open the app, the concept score is not penalized. They didn't fail, they just weren't present. The entry is rescheduled to the next session with the same interval. If a recall has been missed 3 or more times, the interval is halved so it becomes more urgent and surfaces sooner.

**Recall questions**

Recall questions are drawn from the existing quiz question bank, filtered by `(concept_key, difficulty)` and scoped to videos the user has already watched. Only questions generated from transcripts the user has seen are eligible. Pulling from unwatched videos would mean the question references content they've never encountered. As the user watches more videos covering a concept, the eligible pool grows. Recall samples from this pool, using `last_question_id` to avoid repeating the most recently seen question for that concept.

The ideal long-term approach is concept cards: short, authored descriptions of each concept that serve as stable generation inputs for recall questions independent of any video. But authoring these for 19 concepts requires real editorial effort and is noted as a limitation below.

---

## Knowledge State Architecture

The knowledge state is per-user, per-category, not per-video. This is a deliberate choice.

A concept like body_language is stable across many videos within Career & Jobs. The user's mastery should be a single score that grows over time, not fragmented across individual videos. Each skill-learning category on Seekho gets a fixed set of 4-5 concepts. I use the LLM to map videos to these concepts, not the reverse. The number of categories is already defined by Seekho's platform. The concept mapping just needs to be authored for each skill-learning category.

The full user state has three parts: profile, knowledge state, and watch history. The recall queue is defined separately in the Recall Scheduler section.

**User Profile:**

Stores classification inputs. The classifier reads this to determine user type, maturity, and session context.

```json
{
  "user_id": "priya_001",
  "user_type": "AS",
  "maturity": "warming_up",
  "first_seen": "2026-03-15",
  "total_videos_watched": 8
}
```

**Knowledge State:**

Nested by category, then by concept. New users start at 0.0 for all concepts. Scores never decay passively. A category only appears here once the user has engaged with it (watched a video and completed a quiz). Until then, the recommendation engine uses the 0.5 neutral prior for gap calculations.

```json
{
  "user_id": "priya_001",
  "knowledge": {
    "Career & Jobs": {
      "body_language": 0.51,
      "voice_modulation": 0.7,
      "answering_structure": 0.35,
      "handling_nervousness": 0.55,
      "preparation": 0.0
    },
    "English Speaking": {
      "vocabulary": 0.3,
      "pronunciation": 0.2,
      "grammar": 0.0,
      "fluency": 0.0
    }
  },
  "last_updated": "2026-03-28T14:30:00Z"
}
```

**Watch History:**

Stores per-video engagement data. The recommendation engine reads this for the revisit penalty (quiz_score_at_watch, days since watch). The recall question pool uses this to scope eligible questions to watched videos.

```json
{
  "user_id": "priya_001",
  "history": [
    {
      "video_id": "vid_003",
      "category": "Career & Jobs",
      "content_type": "aspiration",
      "watched_at": "2026-03-28T14:00:00Z",
      "completion_rate": 0.92,
      "quiz_scores": {
        "body_language": 1.0,
        "answering_structure": 0.0
      }
    },
    {
      "video_id": "vid_007",
      "category": "Career & Jobs",
      "content_type": "aspiration",
      "watched_at": "2026-03-27T11:00:00Z",
      "completion_rate": 0.85,
      "quiz_scores": {
        "voice_modulation": 1.0,
        "handling_nervousness": 1.0
      }
    }
  ]
}
```

Each component reads from different parts of this state. The classifier reads the profile. The recap and quiz engines read knowledge state for gap calculations. The recommendation engine reads both knowledge state and watch history. The recall scheduler writes to its own queue (defined in its section above).

---

## Metrics

Metrics are organized in four tiers, from what Seekho cares about most (business outcomes) down to what the engineering team needs to keep the system calibrated. Each metric includes what to look at when the number is bad.

All metrics should be segmented by user type (IS/AS/Converting), maturity (New/Warming Up/Established), and category where relevant. Averages across all users hide the real story.

### Tier 1: Business Metrics

These connect Saathi to the numbers Seekho reports to investors. If these don't move, nothing else matters.

**Subscription Retention (Saathi-engaged vs not):** Compare 30-day retention rate for users who completed at least one full loop (recap + quiz + recall) against users who only watched videos. This is the core proof that Saathi adds value beyond content alone. If Saathi-engaged users don't retain better, the system is not solving the right problem.

**IS to AS Conversion Rate:** % of IS users who shift to AS content patterns within 3-5 sessions. This is the growth lever described in 03-ai-vision. If this is low, the recommendation engine's adjacent category nudges or the soft recap for IS users on aspiration content may not be working. Check recommendation acceptance rate and time to first aspiration content (Tier 2) to diagnose.

**Revenue per User (Saathi-engaged vs not):** Average subscription duration x Rs 200/month. If Saathi increases retention, this compounds directly into revenue. Segment by user type to understand which users Saathi helps most.

### Tier 2: Product Metrics

These tell us whether users are engaging with Saathi as designed. Bad numbers here explain bad Tier 1 numbers.

**Quiz Completion Rate:** % of users who complete the quiz when offered (not skipped). If this is low, the quiz is either too hard, feels irrelevant, or appears at the wrong time. Segment by user type and maturity. A low rate for AS (New) users specifically might mean the difficulty cap at medium is still too aggressive.

**Quiz Skip Rate:** The inverse. Track this separately because it is a strong negative signal. High skip rates on specific categories may indicate the concept mapping for that category is weak or the questions feel disconnected from the video.

**Recall Response Rate:** `scheduled recalls completed / recalls scheduled`. Tests whether the habit loop is embedding. If users ignore recalls, the recall timing or format may need adjustment. Also check if missed recalls correlate with churn.

**Recommendation Acceptance Rate:** `recommended videos watched / videos recommended`. Tests whether recommendations feel relevant. If low, check whether it's the same-category 80% that's failing (gap formula issue) or the adjacent 15% (adjacency map issue) or the discovery 5% (expected to be lower).

**Time to First Aspiration Content:** Sessions until an IS user watches their first aspiration video. Measures whether the nudge mechanism (15% adjacent pool, IS soft recap) is working. If this is high, IS users are staying in utility loops and never getting exposed to aspiration content.

**Session Return Rate:** % of users who return within 48 hours of a session where they completed the full loop. This is the most direct measure of whether the habit loop (quiz + recall schedule + progress update) is creating a reason to come back.

### Tier 3: Learning Metrics

These tell us whether users are actually learning. Good Tier 2 numbers with bad Tier 3 numbers mean users are engaging but not improving, which will eventually kill retention.

**Concept Score Delta:** `score_after - score_before` per concept per session. Direct measurement of learning velocity. If this is consistently near zero, the quiz questions may be too easy (users already know the material) or the EMA alpha (0.3) may be too conservative. Segment by difficulty level to check.

**Recall Accuracy:** `correct recall questions / total recall questions`. Tests whether knowledge survived between sessions. If low across the board, the spaced repetition intervals may be too long. If low only for specific concepts, those concepts may need more in-session reinforcement or better recap coverage.

**Recall Lift:** `recall_score - initial_quiz_score` on the same concept. Positive means the user retained or improved since the original quiz. Negative means they forgot. This is the purest signal that spaced repetition is working. If consistently negative, the recall intervals need to be shorter or the recall questions need to be more distinct from the original quiz questions (see limitation 7).

**Concept Graduation Rate:** Sessions until a concept score crosses 0.6 for the first time. Lower is better. Indicates whether the system is moving users forward at a reasonable pace. If this is very high for a specific concept, the concept may be too broad (body_language collapsing too many sub-skills) or the content covering it may not be effective.

### Tier 4: System Health

Engineering metrics. These help debug the system when Tier 2 or Tier 3 numbers look wrong.

**Difficulty Calibration:** % of quizzes where the difficulty band matched the user's score at the time. If a user at score 0.15 gets a medium question, that's a miscalibration. Target >= 80%. Below that, check whether concept scores are being updated correctly or whether the difficulty thresholds (0.2, 0.5) need adjustment.

**Question Bank Coverage:** % of (video_id, concept, difficulty) combinations that have at least one generated question. Low coverage means the question bank is still sparse and users may see the same questions repeatedly. Track this especially for recall, where the pool is scoped to watched videos.

**Concept Extractor Consistency:** For videos covering the same topic, do concept profiles look similar? If two Career & Jobs videos about body language produce wildly different coverage scores, the LLM prompt needs refinement. Spot-check by sampling profiles for related videos.

**Recall Queue Health:** Average queue depth per active user, and % of recalls that have been missed 3+ times. A growing backlog of stale recalls means users are not returning or the daily cap (3-5) is too restrictive for heavy users.

---

## Demo Dataset

**taxonomy.json:** 4 demo categories from Seekho's actual category list, with concept keys fully defined for Career & Jobs (5 concepts). The other 3 (English Speaking, Business, Share Market) are named but not detailed. In production, every skill-learning category would have its own 4-5 concept mapping.

**users.json:** Two profiles. Priya (AS, warming up, pre-loaded knowledge state with weak spots) and Rahul (IS, new, empty state). Together they show how Saathi adapts to fundamentally different users on the same video.

**videos.json:** 5 videos. 4 aspiration (career_and_jobs) and 1 utility (sarkari_kaam). One transcript-backed video serves as the primary demo.

**question_bank.json:** Starts empty, populated lazily at runtime. Keyed by (video_id, concept, difficulty, question_index).

**transcripts/interview_confidence.txt:** ~800 words covering all four Career & Jobs demo concepts. Fed to Concept Extractor and Quiz Engine.

---

## Limitations

**1. The system always targets weakness.**

Every recap, quiz, and recommendation is pointed at weak spots. This is right for learning velocity but will feel exhausting over time. Real learning systems mix challenge with consolidation. A better approach would introduce a "confidence boost" mode where Saathi occasionally serves easier questions on strong concepts and recommends content the user is likely to enjoy, not just content they need.

**2. The IS/AS classification can lag or be wrong.**

The classifier infers user type purely from watch history. Someone who binges utility content during a bad week gets misclassified as IS and has the full loop suppressed. There's no self-correction until behavior shifts over multiple sessions. A short onboarding signal ("I'm trying to improve my English") would be far more reliable, but that flow doesn't exist yet.

**3. The concept taxonomy requires manual authoring for every category.**

Seekho has ~40 categories. Each skill-learning category needs a manually authored concept breakdown (4-5 concepts each), and within a concept like body_language, sub-skills like eye contact, posture, and gestures collapse into a single score. This is fine for the prototype but becomes a bottleneck at scale. A semi-automated approach where the LLM proposes concept breakdowns and a human reviews them would reduce the effort significantly.

**4. Recall questions are borrowed from the quiz bank, not purpose-built.**

Recall pulls from questions generated during quizzes, scoped to videos the user has watched. This means the questions are video-specific in framing rather than concept-general. Worse, if a user has only watched one video covering a concept, there is exactly one question per difficulty level available for recall. They see the same question every time until they watch more. The fix is concept cards: short authored descriptions per concept that serve as stable inputs for generating recall questions independent of any video.

**5. There is no concept of goal completion.**

An Aspiration Seeker who achieves their goal (got the job, feels confident in English) has no way to signal it. The system has no notion of "graduated" and will keep recommending the same category indefinitely. Skill trees (see 03-ai-vision.md) solve this: when all concepts in a category cross a mastery threshold, the user has graduated from that skill tree. Until then, an explicit user signal or behavioral inference (high scores plus declining engagement) would serve as a stopgap.