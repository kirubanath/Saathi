# Saathi

An AI-powered learning companion proposal for [Seekho](https://seekho.ai), a micro-learning platform with 25M+ monthly active users in India.

Saathi is my proposal to turn passive video watching into an active, personalized learning loop. It figures out who the user is, tracks what they know, targets their weak spots, and gives them a reason to come back.

> **Note:** This repository implements the proactive learning loop, one piece of the larger Saathi vision. The full system (conversational mode, real-time adaptation, multi-modal interactions) is described in the documentation but is outside the scope of this prototype.

## Quick Start

> Setup and run instructions will be added after implementation is complete.

## Solution Summary

For a concise overview of the full solution, read **[SOLUTION.md](SOLUTION.md)**.

## Documentation

All documentation lives in [`documentation/`](documentation/). Start with the index for reading order, or jump to what you need.

| #   | Document                                                   | What It Covers                                               |
| --- | ---------------------------------------------------------- | ------------------------------------------------------------ |
| 00  | [Index](documentation/00-index.md)                         | Reading order and document map                               |
| 01  | [Background](documentation/01-background.md)               | What Seekho is, why it works, and the problem as I see it    |
| 02  | [Original Problem](documentation/02-original-problem.md)   | The assignment as given, plus how I interpreted it           |
| 03  | [AI Vision](documentation/03-ai-vision.md)                 | My hypotheses, the opportunity, and what Saathi is as the answer |
| 04  | [Scoped Problem](documentation/04-scoped-problem.md)       | What the prototype builds: inputs, constraints, scope        |
| 05  | [Solution Overview](documentation/05-solution-overview.md) | Nine components, formulas, knowledge state, metrics          |
| 06  | [Demo Overview](documentation/06-demo-overview.md)         | Demo format, users, journeys, and flow                       |
| 07  | [Architecture](documentation/07-architecture.md)           | Component boundaries and data flow                           |
| 08  | [Design Document](documentation/08-design-document.md)     | Implementation plan and build order                          |

## Project Structure

```
.
├── README.md
├── SOLUTION.md             # Concise standalone summary
├── documentation/          # Project documentation
│   ├── 00-index.md
│   ├── 01-background.md
│   ├── 02-original-problem.md
│   ├── 03-ai-vision.md
│   ├── 04-scoped-problem.md
│   ├── 05-solution-overview.md
│   ├── 06-demo-overview.md
│   ├── 07-architecture.md
│   └── 08-design-document.md
├── data/                   # Taxonomy, users, videos, question bank
│   └── transcripts/        # Video transcripts
├── src/saathi/             # Python source code
├── demo/                   # Streamlit demo app
├── main.py                 # CLI entry point
├── pyproject.toml
└── requirements.txt
```
