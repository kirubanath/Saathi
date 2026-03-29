# Demo Overview

This demo showcases the proactive learning loop. It doesn't cover conversational mode, skill trees, or other parts of the full vision (see 03-ai-vision.md).

## What the Demo Needs to Answer

Is this system making decisions based on who the user is, or is it just calling an LLM?

## Format

Streamlit app with two panels side by side.

**Left panel:** What the learner sees. Saathi's messages, recap, quiz, progress update, recommendation. Warm and conversational.

**Right panel:** What the system is thinking. Content type classification, user state, knowledge state, concept profiles, scoring logic, recommendation reasoning. This panel is for evaluation only and would never appear in production.

The evaluator sees both the outcome and the reasoning behind it at the same time.

## Demo Users

**Priya (Aspiration Seeker):** Warming Up, 14 days, 3 videos watched in Career & Jobs. Knowledge state pre-loaded with weak spots (body_language 0.3, answering_structure 0.3, voice_modulation 0.7).

**Rahul (Information Seeker):** New, 3 days, 2 utility videos watched in Sarkari Kaam. Empty knowledge state.

## Step 0: Video Preprocessing

**What it shows:** Where all LLM work happens. Every artifact the four journeys use is generated here. The journeys themselves make no LLM calls.

**Flow:**

1. Transcript for the demo video loads. Right panel shows the raw text.
2. Concept extractor maps the transcript to the Career & Jobs concept taxonomy. Right panel shows the LLM call, the prompt, and the output concept profile: {body_language: 0.9, voice_modulation: 0.8, answering_structure: 0.6, handling_nervousness: 0.5}.
3. Recap bullet generator runs for each concept above the 0.2 coverage threshold. For each concept, two bullets are generated: IS-flavored and AS-flavored. Right panel shows both versions side by side.
4. Question generator runs per concept per difficulty level (easy, medium, hard). Right panel shows sample questions across concepts and difficulty levels.
5. All artifacts are stored. Right panel confirms what was written: concept profile, recap bullets keyed by concept and user type, questions keyed by concept and difficulty.

**What the evaluator should see:** The LLM is called here, not during user interactions. Every personalized response in the four journeys is the system selecting from what was generated in this step. The cost of running Saathi at interaction time is scoring and selection logic, not LLM inference.

## Four Journeys

Each journey runs independently. The evaluator selects a journey from the demo, watches it play out, and sees exactly what the system is doing at every step.

---

### Journey 1: The Core Loop (Priya)

**What it proves:** The full proactive learning loop works end to end. Every component does real work, not just the LLM.

**Video:** "How to speak confidently in interviews" (Career & Jobs, aspiration content).

**Flow:**

1. Priya's profile loads. Right panel shows her user type (AS), maturity (Warming Up), and current knowledge state with weak spots highlighted.
2. Content type identified as aspiration. Classifier determines: AS + aspiration = full loop.
3. Pre-generated concept profile for this video loads. Right panel shows: {body_language: 0.9, voice_modulation: 0.8, answering_structure: 0.6, handling_nervousness: 0.5}.
4. Recap engine ranks concepts by coverage x gap and selects the top 3 AS-flavored pre-generated bullets. Right panel shows why body_language and answering_structure are prioritized (high coverage, high gap). Left panel shows the 3 selected bullets.
5. Quiz engine serves 3 questions, one per targeted concept, at difficulty levels matching Priya's scores. Right panel shows the difficulty selection logic.
6. Priya answers. Response evaluator scores each question. Right panel shows results per concept.
7. Knowledge state updater applies EMA. Right panel shows before/after scores. Example: body_language 0.3 -> 0.51 (correct), answering_structure 0.3 -> 0.21 (wrong).
8. Progress update shown to Priya on the left: "Body Language: 30% -> 51%." Right panel shows the update logic.
9. Recommendation engine runs. Right panel shows the gap vector, relevance scores for candidate videos, and the softmax sampling. Left panel shows the recommended video with an explanation: "Based on what you just practiced, this will help you work on your answering structure."
10. Recall scheduler writes entries to the queue. Right panel shows the scheduled recall times per concept.

**What the evaluator should see:** The system classified Priya before doing anything. The recap targeted her weak spots, not the video's main topics. The quiz adapted to her level. The recommendation followed from her actual performance, not a generic "watch next." Every decision is visible in the right panel.

---

### Journey 2: Same Video, Different User (Rahul)

**What it proves:** The classifier is real. Content type and user state change the entire experience. Two users watching the same video get completely different responses.

**Video:** Same video as Journey 1.

**Flow:**

1. Rahul's profile loads. Right panel shows his user type (IS), maturity (New), and empty knowledge state.
2. Content type identified as aspiration. Classifier determines: IS + aspiration = soft recap only, no quiz.
3. The same pre-generated concept profile loads. Right panel shows it is identical to Priya's.
4. Recap engine selects the top 2 IS-flavored pre-generated bullets. Right panel shows why: IS user gets the softer-toned version, 2 bullets instead of 3, no quiz follows.
5. No quiz. No knowledge state update from quiz. No recall scheduled. Right panel explicitly shows these steps being skipped and why.
6. Recommendation engine runs. Right panel shows the scoring. Left panel shows the recommendation with a warm nudge: "Liked this? Here's where this topic goes."

**What the evaluator should see:** Same video, same concept profile, completely different experience. Rahul is not overwhelmed. The system recognized he's new and exploring, and adjusted accordingly. The right panel makes the decision logic transparent: the classifier suppressed the full loop, not a hardcoded rule.

---

### Journey 3: The Loop Compounds (Priya, Video 2)

**What it proves:** The system gets smarter with each interaction. The loop is not a one-shot trick. This is what makes the data moat argument real.

**Setup:** Continues from Journey 1. Priya follows the recommendation and watches video 2.

**Flow:**

1. Priya's updated knowledge state loads (post-Journey 1). Right panel shows her scores have shifted: body_language is now 0.51, answering_structure dropped to 0.21.
2. Video 2 is a different Career & Jobs video, heavier on answering_structure. Content type: aspiration. Classifier: AS + aspiration = full loop.
3. Pre-generated concept profile for video 2 loads. Right panel shows the new profile, heavier on answering_structure than video 1.
4. Recap engine targets differently now. Because answering_structure dropped to 0.21 (high gap), it dominates the recap. Right panel shows the changed targeting scores compared to Journey 1.
5. Quiz engine serves questions. answering_structure gets an easy question this time (score below 0.2), not medium like in Journey 1. Right panel shows the difficulty shift.
6. Priya answers correctly this time. Knowledge state updates: answering_structure 0.21 -> 0.45.
7. Progress update reflects the recovery: "Answering Structure: 21% -> 45%. Nice comeback."
8. Recommendation engine runs again. The gap vector has shifted. The next recommendation is different from both Journey 1's recommendation and from what it would have been without the quiz data. Right panel shows the full scoring comparison.

**What the evaluator should see:** Everything changed because Priya's knowledge state changed. The recap focused on different concepts. The quiz difficulty adjusted. The recommendation shifted. This is the system learning across sessions, not repeating the same behavior. The right panel makes the compounding visible by showing before/after comparisons at every step.

---

### Journey 4: Day 2 Recall (Priya)

**What it proves:** The habit loop works. The system brings users back and tests whether learning stuck.

**Setup:** Simulated next-day return. Priya opens the app 24 hours after Journey 1.

**Flow:**

1. Priya's profile loads. The system checks her recall queue. Right panel shows pending recalls ranked by priority (urgency x importance). body_language and answering_structure are both due.
2. Top recall surfaces. Left panel shows a single question on body_language (from the quiz bank, scoped to videos she watched, different from the original quiz question if the pool allows). Right panel shows which question was selected and why.
3. Priya answers. Response evaluator scores it. Knowledge state updater applies the recall alpha (0.15, smaller than quiz alpha of 0.3). Right panel shows the update.
4. If correct: recall interval doubles. Next recall for body_language scheduled further out. If wrong: interval halves (min 12 hours), concept score drops slightly. Right panel shows the new schedule.
5. Remaining recalls surface (up to the daily cap). After completion, Priya is free to browse normally.

**What the evaluator should see:** The system remembered what Priya learned yesterday and tested whether it stuck. The recall didn't repeat the exact quiz question. The interval adjusted based on performance. This is spaced repetition integrated into the product, not bolted on. The right panel shows the queue mechanics: how recalls were ranked, why this question was chosen, how the interval changed.
