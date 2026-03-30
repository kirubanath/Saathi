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

## Demo Users

**Priya (Aspiration Seeker):** Warming Up, 14 days. Has watched ep 1 of the Interview Confidence series (vid_001) and ep 1 of the Career Foundations series (vid_004), both Career & Jobs. This gives her the AS classification via depth signal (3+ in one category). Knowledge state pre-loaded with weak spots (body_language 0.3, answering_structure 0.25, voice_modulation 0.7). She is mid-series in both Career & Jobs series, so Slot 1 is always populated in her recommendations.

**Rahul (Information Seeker):** New, 3 days, 2 aspiration videos watched (1 Career & Jobs, 1 English Speaking), no single-category concentration. Empty knowledge state.

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
4. Recap engine ranks concepts by coverage x gap and selects the top 3 AS-flavored pre-generated bullets. Right panel shows the ranking: body_language (0.9 x 0.70 = 0.63), answering_structure (0.6 x 0.75 = 0.45), voice_modulation (0.8 x 0.30 = 0.24). body_language wins on high coverage and high gap. answering_structure beats voice_modulation despite lower coverage because its gap is larger. Left panel shows the 3 selected bullets.
5. Quiz engine serves 3 questions, one per targeted concept. Difficulty is set by Priya's current score: body_language (0.30) and answering_structure (0.25) both fall in the 0.2-0.5 range, so both get medium questions. voice_modulation (0.70) is above 0.5, so it gets a hard question. Right panel shows the difficulty selection logic for each concept.
6. Priya answers. Response evaluator scores each question. Right panel shows results per concept.
7. Knowledge state updater applies EMA. Right panel shows before/after scores: body_language 0.30 -> 0.51 (correct), answering_structure 0.25 -> 0.175 (wrong), voice_modulation 0.70 -> 0.79 (correct).
8. Progress update shown to Priya on the left: "Body Language: 30% -> 51%. Voice Modulation: 70% -> 79%." Answering structure is not shown as a gain. Right panel shows the update logic.
9. Recommendation engine runs. The engine first checks whether this video is mid-series. Right panel shows the series lookup result for Slot 1. Then the aspiration formula runs for Slot 2: right panel shows the gap vector, relevance scores for candidate videos, and the softmax sampling. Left panel shows both slots if the series has a next episode, or just Slot 2 if the series is finished or Priya is not in a series.
10. Recall scheduler writes entries to the queue for all 3 quizzed concepts. Right panel shows the scheduled recall times per concept.

**What the evaluator should see:** The system classified Priya before doing anything. The recap targeted her weak spots, not the video's main topics. The quiz adapted to her level. The recommendation followed from her actual performance, not a generic "watch next." Every decision is visible in the right panel.

---

### Journey 2: Same Video, Different User (Rahul)

**What it proves:** The classifier is real. Content type and user state change the entire experience. Two users watching the same video get completely different responses.

**Counterfactual proof.** Same input. Different state. Different output. This is how you verify the system is making real decisions, not following a static path.

**Video:** Same video as Journey 1.

**Flow:**

1. Rahul's profile loads. Right panel shows his user type (IS), maturity (New), and empty knowledge state. Classifier walks through the steps: Step 1 skipped (utility% is 0%), Step 2 skipped (no single-category concentration), Step 3 fires (fewer than 5 non-entertainment videos total). Result: IS.
2. Content type identified as aspiration. Classifier determines: IS + aspiration = soft recap only, no quiz.
3. The same pre-generated concept profile loads. Right panel shows it is identical to Priya's.
4. Recap engine selects the top 2 IS-flavored pre-generated bullets. Right panel shows why: IS user gets the softer-toned version, 2 bullets instead of 3, no quiz follows.
5. No quiz. No knowledge state update from quiz. No recall scheduled. Right panel explicitly shows these steps being skipped and why.
6. Recommendation engine runs. Right panel shows the scoring. Left panel shows the recommendation with a warm nudge: "Liked this? Here's where this topic goes."

**What the evaluator should see:** Same video, same concept profile, completely different experience. Rahul is not overwhelmed. The system recognised he is new and exploring, and adjusted accordingly. The right panel makes the decision logic transparent: the classifier walked through each step and suppressed the full loop at Step 3. Not a hardcoded rule.

---

### Journey 3: The Loop Compounds (Priya, Video 2)

**What it proves:** The system gets smarter with each interaction. The loop is not a one-shot trick. This is what makes the data moat argument real.

**Setup:** Continues from Journey 1. Priya follows the recommendation and watches video 2.

**Flow:**

1. Priya's updated knowledge state loads (post-Journey 1). Right panel shows her scores have shifted: body_language is now 0.51 (correct answer), answering_structure dropped to 0.175 (wrong answer), voice_modulation is now 0.79 (correct answer).
2. Video 2 is a different Career & Jobs video, heavier on answering_structure. Content type: aspiration. Classifier: AS + aspiration = full loop.
3. Pre-generated concept profile for video 2 loads. Right panel shows the new profile, heavier on answering_structure than video 1.
4. Recap engine targets differently now. answering_structure dropped to 0.175 (gap = 0.825), which pushes it to the top of the ranking. Right panel shows the changed targeting scores compared to Journey 1.
5. Quiz engine serves questions. answering_structure gets an easy question this time (score 0.175, below the 0.2 threshold), a step down from the medium it got in Journey 1. body_language gets a hard question (score 0.51, above the 0.5 threshold), a step up from medium in Journey 1. Right panel shows the difficulty shift for each concept and why.
6. Priya answers correctly this time. Knowledge state updates: answering_structure 0.175 -> 0.42 (correct), body_language advances further if the hard question lands.
7. Progress update reflects the recovery: "Answering Structure: 17% -> 42%. Nice comeback."
8. Recommendation engine runs again. The series continuation check runs first for Slot 1. For Slot 2, the gap vector has shifted and the scoring produces a different result from Journey 1. Right panel shows the full scoring comparison alongside the series check, making the compounding visible.

**What the evaluator should see:** The system adapted in both directions. answering_structure difficulty stepped down after a wrong answer. body_language difficulty stepped up after a correct answer. The recap priorities flipped. This is the system responding to actual performance, not cycling through a fixed sequence. The right panel makes the compounding visible by showing before/after comparisons at every step.

---

### Journey 4: Day 2 Recall (Priya)

**What it proves:** The habit loop works. The system brings users back and tests whether learning stuck.

**Setup:** Simulated next-day return. Priya opens the app 24 hours after Journey 1.

**Flow:**

1. Priya's profile loads. The system checks her recall queue. Right panel shows pending recalls ranked by priority (urgency x importance). body_language and answering_structure are both due.
2. Top recall surfaces. Left panel shows a single question on body_language, drawn from the quiz bank for videos she has already watched. Right panel shows which question ID was selected and confirms it is different from the question served in Journey 1 (the `last_question_id` field on the recall entry prevents back-to-back repetition).
3. Priya answers. Response evaluator scores it. Knowledge state updater applies the recall alpha (0.15, smaller than quiz alpha of 0.3). Right panel shows the update.
4. If correct: recall interval doubles. Next recall for body_language scheduled further out. If wrong: interval halves (min 12 hours), concept score drops slightly. Right panel shows the new schedule.
5. Remaining recalls surface (up to the daily cap). After completion, Priya is free to browse normally.

**What the evaluator should see:** The system remembered what Priya learned yesterday and tested whether it stuck. The recall didn't repeat the exact quiz question. The interval adjusted based on performance. This is spaced repetition integrated into the product, not bolted on. The right panel shows the queue mechanics: how recalls were ranked, why this question was chosen, how the interval changed.

---

*Next: [Design Decisions](08-design-decisions.md)*
