"""Prompt templates for Saathi's preprocessing pipeline.

All prompts follow: TASK -> RULES -> INPUT FORMAT -> EXAMPLE -> ACTUAL INPUT -> OUTPUT COMMAND
No XML-style tags. JSON-only output. Grounded in transcript content only.
"""


# ---------------------------------------------------------------------------
# Prompt 1: Concept Extraction
# ---------------------------------------------------------------------------

CONCEPT_EXTRACTION_SYSTEM = (
    "You are an expert educational content analyst specializing in "
    "skill-based learning videos for Indian learners.\n\n"
    "TASK: Analyze a video transcript and score how thoroughly each concept "
    "from a provided list is covered.\n\n"
    "RULES:\n"
    "1. Score EVERY concept in the provided list. Do not add or remove concepts.\n"
    "2. Scores must be floats in [0.0, 1.0], rounded to 2 decimal places.\n"
    "3. Use ONLY information present in the transcript. Do not hallucinate.\n"
    "4. Scores should reflect relative emphasis. Main topics must have clearly "
    "higher scores than minor mentions. If a concept is the primary focus, it "
    "should score 0.7+. If only briefly touched, it should score below 0.2.\n"
    "5. Return valid JSON only. No extra text, no markdown fences. "
    "If your response is not valid JSON, it will be rejected.\n\n"
    "SCORING RUBRIC:\n"
    "- 0.0: Not mentioned at all\n"
    "- 0.1-0.15: Briefly mentioned in passing, no real explanation\n"
    "- 0.3-0.5: Explained with some detail but not the primary focus\n"
    "- 0.5-0.7: Clearly covered with examples or structured explanation\n"
    "- 0.8-0.9: Primary focus of the video with detailed treatment\n"
    "- 1.0: Exhaustive and dominant theme throughout\n\n"
    "INPUT FORMAT:\n"
    "concepts:\n"
    "  - concept_name_1\n"
    "  - concept_name_2\n"
    "  - ...\n\n"
    "transcript:\n"
    "  <full transcript text>"
)


def build_concept_extraction_prompt(transcript: str, concepts: list[str]) -> str:
    concept_list = "\n".join(f"  - {c}" for c in concepts)
    example_concepts = (
        "  - body_language\n"
        "  - voice_modulation\n"
        "  - answering_structure\n"
        "  - handling_nervousness\n"
        "  - preparation"
    )
    return (
        "EXAMPLE INPUT:\n"
        "concepts:\n"
        f"{example_concepts}\n\n"
        "transcript:\n"
        "  Aaj hum baat karenge nervousness ke baare mein. Interview se pehle, "
        "5 deep breaths lena bahut helpful hota hai. Slow inhale, slow exhale. "
        "Isse aapka heart rate calm hota hai aur aap composed lagte ho. Haath "
        "shake kar rahe ho? Pen pakad lo ya hands interlock kar lo. Movement "
        "controlled ho jata hai. Baki sab cheezein -- baithna, bolna -- woh "
        "alag topics hain.\n\n"
        "EXAMPLE OUTPUT:\n"
        '{"body_language": 0.15, "voice_modulation": 0.0, '
        '"answering_structure": 0.0, "handling_nervousness": 0.85, '
        '"preparation": 0.1}\n\n'
        "NOW PROCESS:\n"
        "INPUT:\n"
        "concepts:\n"
        f"{concept_list}\n\n"
        "transcript:\n"
        f"  {transcript}"
    )


# ---------------------------------------------------------------------------
# Prompt 2: Recap Generation
# ---------------------------------------------------------------------------

RECAP_GENERATION_SYSTEM = (
    "You are a content writer creating recap bullets for an educational video "
    "platform serving Indian learners (Hinglish style is appropriate).\n\n"
    "TASK: Generate exactly two recap bullets for a given concept from a "
    "video transcript.\n\n"
    "RULES:\n"
    "1. IS bullet (Information Seeker tone): Direct, transactional, "
    "practical tip. 1-2 sentences. Low pressure, actionable.\n"
    "2. AS bullet (Aspiration Seeker tone): Growth and mastery framing. "
    "Positions skill as self-development investment. 1-2 sentences.\n"
    "3. Both bullets MUST reference specific techniques, examples, or "
    "situations from the transcript. Avoid generic advice like "
    "\"maintain good posture\" or \"practice regularly\".\n"
    "4. Do NOT hallucinate information not in the transcript.\n"
    "5. If coverage_score < 0.3, return empty strings for both bullets "
    "(this case should be rare since filtering happens upstream).\n"
    "6. Return valid JSON only. No extra text, no markdown fences. "
    "If your response is not valid JSON, it will be rejected.\n\n"
    "INPUT FORMAT:\n"
    "concept: <concept_name>\n"
    "coverage_score: <float>\n"
    "transcript: <full transcript text>\n\n"
    "OUTPUT FORMAT: {\"IS\": \"...\", \"AS\": \"...\"}"
)


def build_recap_generation_prompt(
    transcript: str, concept: str, coverage_score: float
) -> str:
    return (
        "EXAMPLE INPUT:\n"
        "concept: handling_nervousness\n"
        "coverage_score: 0.85\n"
        "transcript: Interview se pehle, 5 deep breaths lo. Slow inhale, "
        "slow exhale. Isse heart rate calm hota hai. Agar haath shake ho "
        "rahe hain, pen pakad lo ya hands interlock kar lo. Nervousness ko "
        "eliminate karne ki koshish mat karo -- usse manage karo.\n\n"
        "EXAMPLE OUTPUT:\n"
        '{"IS": "Before your next interview, try this: 5 slow deep breaths '
        "and keep your hands occupied with a pen. It stops the shake before "
        'anyone notices.", '
        '"AS": "Nervousness is not the enemy -- unmanaged nervousness is. '
        "Controlled breathing and deliberate hand positioning are trainable "
        'habits that build the composed presence interviewers respond to."}\n\n'
        "NOW PROCESS:\n"
        "INPUT:\n"
        f"concept: {concept}\n"
        f"coverage_score: {coverage_score:.2f}\n"
        f"transcript: {transcript}"
    )


# ---------------------------------------------------------------------------
# Prompt 3: Question Generation
# ---------------------------------------------------------------------------

QUESTION_GENERATION_SYSTEM = (
    "You are a quiz question writer for an educational video platform "
    "serving Indian learners.\n\n"
    "TASK: Generate exactly three multiple-choice questions for a given "
    "concept from a video transcript, one per difficulty level.\n\n"
    "RULES:\n"
    "1. Easy: Answer is directly stated in the transcript. Tests recall.\n"
    "2. Medium: User must apply a principle to a new scenario. Tests understanding.\n"
    "3. Hard: User must reason across multiple ideas or evaluate an approach. "
    "Tests synthesis.\n"
    "4. Each question should focus on a different aspect of the concept "
    "where possible. Do not generate 3 questions about the same idea.\n"
    "5. Each question has exactly 4 options.\n"
    "6. correct_index is 0-based (0, 1, 2, or 3).\n"
    "7. Spread correct_index values across positions. Do not cluster at 0 or 1.\n"
    "8. Wrong options must be plausible, not obviously absurd.\n"
    "9. Hinglish phrasing is acceptable.\n"
    "10. All questions MUST be grounded in transcript content. "
    "Do NOT hallucinate facts.\n"
    "11. If the concept is not meaningfully covered in the transcript, "
    "return null instead of fabricating questions.\n"
    "12. Return valid JSON only. No extra text, no markdown fences. "
    "If your response is not valid JSON, it will be rejected.\n\n"
    "INPUT FORMAT:\n"
    "concept: <concept_name>\n"
    "transcript: <full transcript text>\n\n"
    "OUTPUT FORMAT:\n"
    '{"easy": {"question": "...", "options": ["a","b","c","d"], "correct_index": N}, '
    '"medium": {"question": "...", "options": ["a","b","c","d"], "correct_index": N}, '
    '"hard": {"question": "...", "options": ["a","b","c","d"], "correct_index": N}}'
)


def build_question_generation_prompt(transcript: str, concept: str) -> str:
    return (
        "EXAMPLE INPUT:\n"
        "concept: handling_nervousness\n"
        "transcript: Interview se pehle 5 deep breaths lo. Slow inhale, "
        "slow exhale. Isse heart rate calm hota hai. Agar haath shake ho "
        "rahe hain, pen pakad lo ya hands ko lightly interlock kar lo. "
        "Nervousness ko eliminate karne ki koshish mat karo -- usse manage karo.\n\n"
        "EXAMPLE OUTPUT:\n"
        '{"easy": {"question": "According to the video, how many deep breaths '
        'should you take before an interview to calm your heart rate?", '
        '"options": ["3 deep breaths", "10 deep breaths", "5 deep breaths", '
        '"2 deep breaths"], "correct_index": 2}, '
        '"medium": {"question": "You are in the waiting room before an '
        "interview and notice your hands are shaking. Based on the video, "
        'what should you do?", '
        '"options": ["Try to relax by thinking of something else", '
        '"Hold a pen or lightly interlock your fingers to control the movement", '
        '"Hide your hands under the table so the interviewer does not notice", '
        '"Take a break and reschedule the interview"], "correct_index": 1}, '
        '"hard": {"question": "The video says not to try to eliminate '
        "nervousness, only to manage it. Which of the following best explains "
        'why this advice makes sense?", '
        '"options": ["Nervousness is impossible to eliminate so there is no '
        'point trying", '
        '"Trying to eliminate nervousness increases anxiety about feeling '
        "nervous, while managing it redirects energy into controlled "
        'behaviors", '
        '"Interviewers expect candidates to be nervous and will think less '
        'of someone who is too calm", '
        '"Managing nervousness takes less time to learn than eliminating it"], '
        '"correct_index": 1}}\n\n'
        "NOW PROCESS:\n"
        "INPUT:\n"
        f"concept: {concept}\n"
        f"transcript: {transcript}"
    )
