# Saathi Documentation

This folder contains the complete documentation for the Saathi project, my AI learning companion proposal for Seekho.

Start with SOLUTION.md in the project root for a concise summary of the full proposal. Then use this index to go deeper on any section.

## Documents

**[01-background.md](01-background.md)** - What Seekho is, why it works, and the problem as I see it. Covers the business model, user base, content strategy, and where the platform leaves retention on the table.

**[02-original-problem.md](02-original-problem.md)** - The assignment as given, preserved verbatim, plus how I interpreted it and what I chose to build.

**[03-ai-vision.md](03-ai-vision.md)** - The core document. My user hypotheses (Information Seekers vs Aspiration Seekers), the retention theory, what Saathi is, and why a proactive learning loop is the right answer before conversational AI.

**[04-scoped-problem.md](04-scoped-problem.md)** - What this prototype actually builds. The proactive learning loop only: inputs, constraints, what is explicitly out of scope, and why.

**[05-solution-overview.md](05-solution-overview.md)** - The full technical detail. Three phases: preprocessing, session start, and the per-video pipeline. Every component, formula, data structure, metric, and the demo dataset.

**[06-architecture.md](06-architecture.md)** - How the system is structured. Three diagrams (one per phase), API endpoints, technology choices, LLM layer design, component read/write responsibilities, data layer, deployment, and scaling.

**[07-demo-overview.md](07-demo-overview.md)** - How the demo works. What the demo proves, format, two demo users, the preprocessing step, and four journeys including a counterfactual proof that the system makes real decisions based on user state.

**[08-design-decisions.md](08-design-decisions.md)** - Why the system is designed this way. Key decisions with reasoning and tradeoffs: LLM offline strategy, EMA alpha choices, fixed taxonomy, recall scheduling, rule-based classifier, two-call quiz design, and known limitations.
