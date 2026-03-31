# Scoped Problem Statement

Saathi is the full AI companion system I'm proposing for Seekho (see 03-ai-vision.md). This document scopes what I'm actually building for this prototype: **the proactive learning loop**.

## Problem

I believe the core problem is this: users watch a video, feel motivated in the moment, forget the key ideas by tomorrow, and never come back. Content delivery is not the same as learning. Learning requires recall, feedback, and repetition. Without these, retention collapses.

## Objective

Build an adaptive system that activates after a video is watched, reinforces learning through personalized recap and quiz, maintains a per-user knowledge state, and recommends the next video based on what the user actually knows.

This loop is the engine of Saathi. Everything else in the larger vision (conversational mode, skill trees, progress dashboards) depends on the data and knowledge state this loop produces.

## Core Principle

Good content is not enough. Users need to feel progress.

## Inputs

**Video Data:** Transcript, title/topic metadata, key concepts.

**User History:** Watch history, completion rates, previous quiz attempts, session patterns.

**User Knowledge State:** Per-concept mastery scores, user type classification, maturity level, last interaction timestamp.

## Design Decisions

These are choices I'm making based on my hypotheses about what will work:

**Do:** Classify user state before acting. Ground recap and quiz in weak concepts, not generic summaries. Update knowledge state after every interaction. Calibrate intensity to user state (nudge for new users, rigor for established ones). Keep everything under two minutes, mobile-first.

**Don't:** No one-size-fits-all behavior. No leaderboards. No arbitrary scoring. No generic LLM output. No pressure on new or information-seeking users.

## Scope

This prototype covers eight components: User State Classifier, Concept Extractor, Recap Engine, Quiz Engine, Response Evaluator, Knowledge State Updater, Recommendation Engine, and Recall Scheduler. Details on each are in [05-solution-overview.md](05-solution-overview.md).

Everything else in the larger Saathi vision (conversational mode, skill trees, progress dashboards, social signals) is outside the scope of this prototype and documented in [03-ai-vision.md](03-ai-vision.md).

## What the Prototype Must Prove

1. AI is doing real work, not just calling an LLM and showing output.
2. System classifies user state before acting.
3. System adapts based on user performance, not static rules.
4. Knowledge state is the intelligence layer, not the LLM alone.
5. The loop is closed: watch, classify, recap, quiz, update, recommend, recall, return.

## Success Criterion

The prototype should feel like this is a learning system that knows who it is talking to.

---

*← [AI Vision](03-ai-vision.md)* | *[Solution Overview →](05-solution-overview.md)*
