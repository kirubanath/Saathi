# Saathi: The AI Vision

## What is Saathi

Saathi means "companion" in Hindi. A saathi walks with you, not ahead of you. It is warm, non-threatening, and personal. That tone shapes everything about this system.

Seekho currently has a chatbot called Coach. Based on what I could observe, Coach appears to be stateless, generic, and reactive. It forgets everything between sessions, gives the same response to everyone, and waits for the user to come to it. But I think there's an opportunity to go much further.

Saathi is what I'm proposing instead. It is persistent (remembers every video watched and every question answered), personalized (adapts to each user's learning state), and proactive (shows up when learning can happen, not just when the user asks).

It has two modes that share one brain:

**Proactive Mode** is the learning loop. After a user watches aspiration content, Saathi shows up automatically with a recap, quiz, progress update, recommendation, and recall schedule. This is what the prototype implements.

**Conversational Mode** is an always-on chat grounded in the user's full learning history. When someone asks "Can you explain that differently?" or "can you help me remember what x was?", Saathi has the context to actually help. This is out of scope for this prototype.

Both modes read from and write to the same knowledge state. That shared brain is what makes Saathi coherent across sessions.

---

## The Deeper Problem (My Hypothesis)

The assignment frames this as a retention problem: users forget content, so remind them. That's accurate but I think it's incomplete.

My hypothesis is that the deeper problem is structural. I believe Seekho currently operates as a high-acquisition, high-churn content platform. Users come in, watch a few videos, and leave. Even in the future if they need a new information they could just borrow the app from someone else and watch exactly what they need and leave. There is no reason for them to create their own since there is no personalization. The platform becomes a revolving door. The real question is not "how do I help users remember?" but "how do I make Seekho a learning system that users want to keep coming back to?"

That question starts with understanding who the users are.

---

## Two User Types (My Assumption)

I think Seekho's users likely fall into two behavioral patterns, defined by intention rather than demographics.

**Information Seekers** come for a specific need: "How do I link Aadhaar to my bank account?" They watch 1-3 videos, get their answer, and leave. I hypothesize their lifetime value is low. Quizzing them after a utility video would feel annoying.

**Aspiration Seekers** come with a longer-term goal: "I want to speak English confidently" or "I want to crack job interviews." They return regularly and watch content in sequence. I hypothesize their lifetime value is much higher, but they drop off when progress is not visible.

My central assumption is that everyone starts as an Information Seeker. The primary growth lever is converting them into Aspiration Seekers, and then figuring out how to retain them. That conversion is what Saathi is designed to drive.

---

## What I Think Drives Retention (Another Assumption)

I'm hypothesizing that what motivates Tier 2/3 users to return is the feeling of moving forward, not leaderboards or point systems. They need to see themselves as different from their past self. The emotional north star is not "I am better than others" but "I am moving forward."

I believe that's why users pay Rs 200/month. They're not buying videos. They're buying the feeling of growth.

This shapes how Saathi needs to behave. Every interaction should answer one question from the user's perspective: am I getting better? If Saathi can reliably answer yes, with evidence, users have a reason to come back.

---

## How Saathi Reads the Room

Saathi classifies each user across three dimensions before deciding how to behave:

1. **User Type** (from watch history): Information Seeker, Aspiration Seeker, or Converting
2. **Maturity** (from tenure): New (0-7 days), Warming Up (1-4 weeks), Established (1+ month)
3. **Session Context** (from what they just watched): utility content, aspiration content, series completion, or recall return

These combine to determine how Saathi responds. The same video creates a completely different experience depending on who watched it. A few examples:

| User State | Watch Context | Saathi Response |
|---|---|---|
| New, Information Seeker | Utility content | No quiz. Gentle nudge: "Want to learn something else useful?" |
| New, warming up | Aspiration content | Soft introduction. Single easy question. Build confidence. |
| Returning, aspiration pattern | Aspiration content | Full loop: recap, adaptive quiz, progress update, recommendation. |
| Established, struggling | Aspiration content, dips | Encouragement first. Identify misconception, offer alternative explanation. |
| Converting | Mixed pattern | Conversion nudge: "You've been learning about X. Here's where this leads." |

---

## The Conversion Opportunity

I believe the path from Information Seeker to Aspiration Seeker follows a natural progression: arrive with a specific need, get a good answer, gain trust, then Saathi gently surfaces related aspiration content. If the user bites, the full learning loop activates. They start seeing progress. That progress creates a reason to return. Over time, the user shifts from "I came for one answer" to "this is where I grow."

This is where AI matters. Rule-based systems can't make the nudge feel personal. They can't calibrate a quiz to the user's actual knowledge level. AI is what makes the suggestions feel relevant and the assessments feel fair. That personalization is what turns a feature into a habit.

---

## Design Principles

**The emotional north star: "Am I moving forward?"**

My working theory is that Seekho's Tier 2/3 audience is not competing with peers. They are trying to become a better version of themselves. They have specific aspirations: speak English at work, earn more, not feel left behind. I believe "You improved" resonates with them. "You are rank 47" creates shame.

Every Saathi touchpoint should answer one question: "Am I moving forward?" The recap says you learned something. The quiz says let's see how far you've come. The progress score says you just got better. The recall says yesterday's learning is sticking. The recommendation says here's your next step.

**Social signals: show movement, not ranking.**

I think the right kind of social proof for this audience is community momentum, not competition. "4,200 people from Rajasthan learned this skill this month" works. "You are 847th" does not. The principle: show users that people like them are moving forward, not where they stand relative to others.

**Three pillars that work together:**

Personalization (different users get different experiences), progress visibility (users see concrete evidence of improvement), and habit loop (the system creates recurring reasons to engage). Personalization makes the habit feel tailored. Progress visibility makes it rewarding. The habit loop makes the reward regular.

---

## The Data Moat

Content is replicable. Any platform can create "how to speak confidently" videos. But learning intelligence data is not.

Duolingo's moat is not its content. It is the behavioral data from hundreds of millions of learners that continuously improves how learning is delivered. Seekho can build a similar advantage for Indian vernacular skill learning, especially for Tier 2 and Tier 3 users, a segment that remains largely under-instrumented and poorly understood.

Most learning systems today are optimized for urban, English-speaking users. Tier 2 and Tier 3 users behave differently. Their learning is more need-driven, language-first, and closely tied to real-world outcomes. There is very little high-quality data capturing how this segment discovers, consumes, forgets, and returns to learning.

With Saathi running, Seekho would start collecting data that no competitor can replicate without the same user base: which concepts users forget within 24 hours, what content converts Information Seekers into Aspiration Seekers, what sequences of content drive continued engagement, and what triggers users to return after drop-off. This data gets more valuable as the user base grows and creates a flywheel that is very hard to catch up to.

Better insights lead to better personalization. Better personalization leads to better outcomes. Better outcomes lead to higher retention, which generates more data. That loop becomes the moat. Not the content itself, but the accumulated understanding of how this segment learns and progresses over time.

This depends on a specific architectural choice I'm making: concept keys in the knowledge state are defined per category, not extracted per video. This keeps the knowledge state stable and trackable over time, which is what allows the data to compound.

---

## The Full Vision

This prototype focuses on Proactive Mode. The proactive loop is the engine. It produces the knowledge state data that every other component needs. Without it, nothing below has anything to work with. That's why it's the first thing I build.

**Onboarding Assessment:** A short interaction when a user first signs up. "What are you trying to learn? What do you already know?" This gives Saathi a starting signal instead of relying entirely on watch history inference, which takes multiple sessions to stabilize. It also directly solves the IS/AS misclassification problem noted in the solution's limitations.

**Skill Trees:** A structured view of each category's concepts and the user's progress through them. "Career & Jobs: Body Language (strong), Answering Structure (learning), Preparation (not started)." This solves two problems at once. First, it makes progress visible. The user can see exactly where they are and what's left. Second, it creates a natural notion of completion. When all concepts in a category cross a threshold, the user has "graduated" from that skill tree. That graduation signal is what the current system is missing. Without it, Saathi keeps recommending the same category forever.

**Progress Dashboard:** A visual summary of learning over time. Score trajectories, recall streaks, concepts mastered this month. This is the long-form version of the progress update that the prototype shows after each quiz. The dashboard serves the emotional north star at a larger scale: not just "did I improve today" but "look how far I've come this month."

**Conversational Mode:** An always-on chat grounded in the user's full knowledge state and watch history. When someone asks "Can you explain that differently?" or "Help me prepare for an interview tomorrow", Saathi has the context to actually help. This shares the same brain as Proactive Mode. Both read from and write to the same knowledge state.

**Community-based Social Signals:** Social proof that shows movement, not ranking. "4,200 people from Rajasthan learned this skill this month." This reinforces the emotional north star at a community level. The principle from the design section applies: show users that people like them are moving forward, not where they stand relative to others.

---

*Next: [Scoped Problem](04-scoped-problem.md)*
