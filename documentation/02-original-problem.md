# Original Problem Statement

## Context

This document captures the original take-home assignment from Seekho for an AI Engineer role.

## The Assignment

Problem Statement: AI Revision Coach for Micro-Learning

Seekho users consume short educational videos quickly, but many forget key concepts soon after watching. Your challenge is to build an AI system that improves learning retention and repeat engagement after each video.

Build an AI-powered "Revision Coach" that, after a learner watches a video, can:
- Generate a 60-second personalized recap (max 3 bullets).
- Create adaptive quiz questions (difficulty based on learner performance).
- Recommend the next best video based on weak concepts.
- Trigger a next-day recall check (1 quick revision question).

Important:
- AI must be the core intelligence, not a cosmetic chatbot wrapper.
- Your system should show how learner behavior changes based on AI adaptation.

Input (for prototype):
- Video transcript + title/topic metadata.
- Basic learner interaction data (quiz attempts, watch completion, topic history).

Expected Output:
- Working prototype/demo of the revision flow.
- Clear AI architecture (retrieval, personalization logic, model usage).
- Learning impact metrics (example: quiz improvement, return rate, completion rate).

Evaluation Focus:
- AI depth and originality
- Learning impact
- Practical execution
- Scalability potential

## How I Interpreted This

The assignment is focused and clear. But as I dug into Seekho's business model, I started thinking about the broader context.

My assumption is that the forgetting problem the assignment highlights is part of a bigger pattern: learners likely struggle not just with individual lessons, but with piecing together knowledge across videos, staying motivated, and seeing their own progress. So rather than optimizing narrowly for post-video recall, I scoped my response to address the full learning journey.

That's how I arrived at Saathi. It's my interpretation of what "AI revision coach" could become if we extended it to cover the learner's entire experience. The detailed reasoning is in [03-ai-vision.md](03-ai-vision.md) and [04-scoped-problem.md](04-scoped-problem.md).
