# Demo Overview

This demo showcases the proactive learning loop. It doesn't cover conversational mode, skill trees, or other parts of the full vision (see 03-ai-vision.md).

## What the Demo Needs to Answer

Is this system making decisions based on who the user is, or is it just calling an LLM?

## What This Demo Proves

- System behavior changes based on user state, not content alone
- No LLM calls happen in the runtime path
- The learning loop compounds across sessions
- Recommendations are personalized by content type: gap-driven for aspiration content, series-entry distribution for entertainment and utility

## Format

Streamlit app with two panels side by side.

**Left panel:** What the learner sees. Saathi's messages, recap, quiz, progress update, recommendation. Warm and conversational.

**Right panel:** What the system is thinking. Content type classification, user state, knowledge state, concept profiles, scoring logic, recommendation reasoning. This panel is for evaluation only and would never appear in production.

The evaluator sees both the outcome and the reasoning behind it at the same time.

## How the Demo Works

The demo is a live, working system. Every output shown is computed in real time from real API calls. Nothing is pre-recorded or mocked at interaction time.

Seed data creates specific starting conditions before the demo begins. Priya and Rahul are pre-seeded in the database with defined knowledge states, watch histories, and recall queues. All aspiration video artifacts are pre-generated and loaded in MinIO. This setup runs once via the seed script before the demo starts.

Each journey is a staged scenario: a specific user watching a specific video, with the system responding in real time. The presenter advances through steps manually. The right panel shows the system's reasoning at each step.

The sidebar has a Reset button. Clicking it re-seeds both users and clears any state written during the current journey. This is how the presenter moves between journeys cleanly.

You can keep going after any journey. The system does not stop. Journey 4 ends the demo narrative, not the system. After the four journeys, an evaluator can click freely and the system keeps responding correctly. The journeys are sufficient to prove the system works, but they are not a ceiling.

Journey 3 branches. Priya receives two recommendation slots after Journey 1 (Slot 1: next in the same series she just watched, Slot 2: engine pick). The presenter clicks one. The demo shows that path in full. The other path can be described verbally or shown with a reset.

The presenter can answer quiz questions any way to demonstrate different outcomes. Answering all questions correctly produces larger positive score deltas, harder questions next session, and longer recall intervals. Answering incorrectly or skipping produces smaller updates and shorter intervals. The journeys are scripted around specific answers for narrative clarity, but the system responds correctly to any input.

Slot 1 is deterministic and will always return the same result for the same user state. Slot 2 is probabilistic. It uses softmax sampling over a scored pool, so the exact video picked can differ between runs even if the knowledge state has not changed. This is expected behavior and can be shown live to illustrate that the engine is not returning a hardcoded result.

## Demo Users

**Priya (Aspiration Seeker):** Warming Up, 14 days on platform. Her watch history includes 3 Career & Jobs videos from prior sessions (pre-seeded as abstract entries in the database, not from the demo video set). This is what produces her AS classification via Step 2 (depth signal: 3+ videos in the same aspiration category). Her knowledge state has pre-loaded weak spots: body_language=0.3, answering_structure=0.25, voice_modulation=0.7. For the demo journeys, she is watching the Interview Confidence series for the first time.

**Rahul (Information Seeker):** New, 3 days, 2 aspiration videos watched (1 Career & Jobs, 1 English Speaking), no single-category concentration. Classified IS via the new-user default (Step 3: fewer than 5 non-entertainment videos total). Empty knowledge state, no recall entries.

## Step 0: Video Preprocessing

**What it shows:** Where all LLM work happens. Only aspiration videos go through this pipeline. Utility and entertainment videos have metadata only. The journeys make no LLM calls.

**Video:** vid_001 (Body Language in Interviews, Career & Jobs aspiration, ep 1 of the Interview Confidence series).

**Flow:**

1. Transcript for vid_001 loads. Right panel shows the raw text.
2. Concept extractor maps the transcript to the Career & Jobs aspiration taxonomy. Right panel shows the LLM call, the prompt, and the output concept profile: {body_language: 0.9, handling_nervousness: 0.7}. Other Career & Jobs concepts are below the 0.2 threshold for this video and are excluded.
3. Recap bullet generator runs for each concept above threshold. For each concept, two bullets are generated: IS-flavored and AS-flavored. Right panel shows both versions side by side.
4. Question generator runs per concept per difficulty level (easy, medium, hard). Right panel shows sample questions across concepts and difficulty levels.
5. All artifacts are stored in MinIO. Right panel confirms what was written: concept profile, recap bullets keyed by concept and user type, questions keyed by concept and difficulty.

**What the evaluator should see:** The LLM is called here, not during user interactions. Every personalized response in the four journeys is the system selecting from what was generated in this step. This pipeline only runs for aspiration videos. Utility and entertainment videos skip it entirely. The cost of running Saathi at interaction time is scoring and selection logic, not LLM inference.

## Four Journeys

Each journey is a staged scenario. The presenter resets between journeys using the sidebar button.

---

### Journey 1: The Core Loop (Priya, vid_001)

**What it proves:** The full proactive learning loop works end to end. Every component does real work.

**Video:** vid_001, Body Language in Interviews (Career & Jobs, aspiration, ep 1 of Interview Confidence series). Priya is watching this for the first time.

**Flow:**

1. Priya's profile loads. Right panel shows her user type (AS), maturity (Warming Up), and current knowledge state with weak spots highlighted.
2. Content type identified as aspiration. Classifier walks through the cascade: Step 2 fires (3+ Career & Jobs videos in history). Result: AS. Right panel shows each step explicitly.
3. Pre-generated concept profile for vid_001 loads from MinIO. Right panel shows: {body_language: 0.9, handling_nervousness: 0.7}.
4. Recap engine ranks concepts by coverage x gap. body_language (0.9 x 0.7 = 0.63) ranks first, handling_nervousness (0.7 x 0.7 = 0.49) ranks second. Top 2 AS-flavored bullets selected. Left panel shows the bullets. Right panel shows the ranking.
5. Quiz engine serves 2 questions, one per targeted concept. body_language (score 0.30) is in the 0.2-0.5 range, gets a medium question. handling_nervousness (score 0.55 assumed prior) gets a medium question. Right panel shows the difficulty selection logic.
6. Priya answers. Response evaluator scores each question. Right panel shows results.
7. Knowledge state updater applies EMA. Right panel shows before/after scores.
8. Progress update shown to Priya. Right panel shows the update logic.
9. Recommendation engine runs. Slot 1 check: vid_001 is ep 1 of the Interview Confidence series and Priya has not watched ep 2 or ep 3, so Slot 1 = vid_002 (next episode in the same series). Right panel shows the series lookup. Slot 2: gap-based scoring runs, right panel shows the gap vector and softmax sampling. Left panel shows both slots.
10. Recall scheduler writes entries for quizzed concepts. Right panel shows the scheduled recall times.

**What the evaluator should see:** The system classified Priya before doing anything. The recap targeted her weak spots, not the video's general topic. The quiz adapted to her level. Slot 1 is the next episode in the same series she just watched, not a category-level suggestion. Slot 2 is driven by her knowledge gaps. Every decision is visible in the right panel.

---

### Journey 2: Same Video, Different User (Rahul, vid_001)

**What it proves:** The classifier is real. Two users watching the same video get completely different responses.

**Counterfactual proof.** Same input. Different state. Different output. This is how you verify the system is making real decisions, not following a static path.

**Video:** vid_001, the same video as Journey 1.

**Flow:**

1. Rahul's profile loads. Right panel shows his user type (IS), maturity (New), and empty knowledge state. Classifier walks through the steps: Step 1 skipped (utility% is 0%), Step 2 skipped (no single-category concentration), Step 3 fires (fewer than 5 non-entertainment videos total). Result: IS.
2. Content type identified as aspiration. Classifier determines: IS + aspiration = soft recap only, no quiz.
3. The same pre-generated concept profile loads from MinIO. Right panel shows it is identical to Priya's.
4. Recap engine selects the top 2 IS-flavored pre-generated bullets. Right panel shows why: IS user gets the softer-toned version, 2 bullets, no quiz follows.
5. No quiz. No knowledge state update from quiz. No recall scheduled. Right panel explicitly shows these steps being skipped and why.
6. Recommendation engine runs. Slot 1 check: vid_001 is ep 1 of Interview Confidence and Rahul has not watched ep 2, so Slot 1 = vid_002 (next episode in the same series). Right panel shows the series lookup — same series result as Priya in Journey 1. Slot 2: IS temperature is higher, pool is explored more broadly. Left panel shows both slots with a warm nudge tone.

**What the evaluator should see:** Same video, same concept profile, completely different experience. Rahul is not overwhelmed. The Slot 1 result is the same as Priya's because it is a pure series lookup, not personalised by user type. The difference is in the loop: Rahul gets no quiz and no recall. The right panel makes the decision logic transparent at every step.

---

### Journey 3: The Loop Compounds (Priya follows a recommendation)

**What it proves:** The system adapts to actual performance. The loop is not a one-shot trick.

**Setup:** Continues from Journey 1 state. Priya has two recommendation slots. The presenter picks one.

**Path A (Slot 1 — series continuation):** Priya watches vid_002 (Answering Questions with Structure, ep 2 of Interview Confidence). This is heavier on answering_structure and voice_modulation, exactly where her gap widened after Journey 1.

**Path B (Slot 2 — engine pick):** Priya watches the gap-scored recommendation from Journey 1 (either vid_005 from Career Foundations or vid_006 from English Speaking). The system chose this based on her post-Journey-1 gap vector.

The demo shows Path A in full. Path B follows the same loop structure but with a different concept profile.

**Flow (Path A):**

1. Priya's updated knowledge state loads (post-Journey 1). Right panel shows her shifted scores.
2. vid_002 is loaded. Content type: aspiration. Classifier: AS + aspiration = full loop.
3. Pre-generated concept profile for vid_002 loads. Right panel shows the new profile, heavier on answering_structure.
4. Recap engine targets differently now. answering_structure dropped after Journey 1, pushing its gap up. Right panel shows the changed ranking compared to Journey 1.
5. Quiz engine serves questions. Difficulty adapts to her post-Journey-1 scores, not the same levels as Journey 1. Right panel shows the shift and why.
6. Priya answers. Knowledge state updates.
7. Progress update reflects the change. Right panel shows before/after.
8. Recommendation engine runs for the next two slots. Slot 1: is vid_002 the last episode of Interview Confidence? No, vid_003 remains. So Slot 1 = vid_003. Slot 2: gap vector has shifted, scoring produces a different result from Journey 1. Right panel shows the full comparison.

**What the evaluator should see:** The system adapted in both directions across journeys. Concepts that dropped got easier questions. Concepts that improved got harder ones. The recap priorities shifted. The next Slot 1 is still the same series, now one episode further. This is the data moat argument: every interaction makes the next one more targeted.

---

### Journey 4: Day 2 Recall (Priya)

**What it proves:** The habit loop works. The system brings users back and tests whether learning stuck.

**Setup:** Simulated next-day return. Priya opens the app 24 hours after Journey 1.

**Flow:**

1. Priya's profile loads. Session start fires first. The system checks her recall queue. Right panel shows pending recalls ranked by priority (urgency x importance). body_language and handling_nervousness are both due.
2. Top recall surfaces. Left panel shows a single question on body_language, drawn from the quiz bank for videos she has already watched. Right panel shows which question ID was selected and confirms it is different from the question served in Journey 1 (the `last_question_id` field prevents back-to-back repetition).
3. Priya answers. Response evaluator scores it. Knowledge state updater applies the recall alpha (0.15, smaller than quiz alpha of 0.3). Right panel shows the update.
4. If correct: recall interval doubles. Next recall for body_language scheduled further out. If wrong: interval halves (min 12 hours), concept score drops slightly. Right panel shows the new schedule.
5. Remaining recalls surface (up to the daily cap). After completion, Priya is free to browse.

**What the evaluator should see:** The system remembered what Priya learned yesterday and tested whether it stuck. The recall did not repeat the exact quiz question. The interval adjusted based on performance. This is the return trigger: spaced repetition integrated into the product. After Journey 4, the demo narrative is complete. The full loop has been shown: watch, classify, recap, quiz, update, recommend, return, recall. The system continues to work if you keep clicking.

---

### Journey 5: The Content Type Gate (Rahul, vid_008)

**What it proves:** The content type gate is real. Watching a utility video produces a completely different system response from watching aspiration content. No learning loop fires. Recommendation logic switches to a different formula entirely.

**Video:** vid_008, How to Get Your PAN Card (Sarkari Kaam, utility, ep 1 of Government Documents series). Rahul watches this.

**Flow:**

1. Rahul's profile loads. Right panel shows his user state (IS, New).
2. Content type identified as utility. Right panel shows the classifier stopping at the content type gate: no concept taxonomy, no recap bullets, no quiz, no recall. The learning loop is off.
3. No recap. No quiz. No knowledge state update. Right panel explicitly shows all these steps being skipped, with the reason: utility content does not carry concept data and has no educational loop.
4. Recommendation engine runs. Slot 1: vid_008 is ep 1 of the Government Documents series and Rahul has not watched ep 2, so Slot 1 = vid_009. Right panel shows the series lookup.
5. Slot 2: utility bucket formula applies. Pool is built from series representatives (one per remaining series). Right panel shows the 50/30/20 split: 50% same utility category (Voter Services representative = vid_012), 30% other utility (Phone Basics representative = vid_014), 20% aspiration (any aspiration entry point). Right panel shows which bucket was sampled and which representative was selected.
6. Left panel shows the result with warm nudge tone: no quiz, no progress message, just the two recommendation slots.

**What the evaluator should see:** The system did not call an LLM. It did not run a quiz. It made one classification decision (utility) and then ran a bucket-based recommendation. The right panel shows the 50/30/20 distribution and how the pool was constructed from series representatives. This is the same engine doing less work, not a different path — the content type gate is a filter applied at the start of the same pipeline.

---

*← [Architecture](06-architecture.md)* | *[Design Decisions →](08-design-decisions.md)*
