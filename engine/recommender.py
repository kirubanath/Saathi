import math
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from db.models import User, Video, WatchHistory
from config.taxonomy import CONCEPTS, ADJACENCY
from storage.base import get_storage_client


@dataclass
class RecommendationResult:
    slot1: dict | None  # Series continuation video or None
    slot2: dict | None  # Engine-picked video or None
    reasoning: list[str] = field(default_factory=list)


def _video_to_dict(video: Video) -> dict:
    return {
        "video_id": video.video_id,
        "title": video.title,
        "series_id": video.series_id,
        "series_position": video.series_position,
        "content_type": video.content_type,
        "category": video.category,
    }


def _get_all_videos(db: Session) -> list[Video]:
    return db.query(Video).all()


def _get_user_watch_history(db: Session, user_id: str) -> list[WatchHistory]:
    return (
        db.query(WatchHistory)
        .filter(WatchHistory.user_id == user_id)
        .all()
    )


def _get_series_videos(all_videos: list[Video], series_id: str) -> list[Video]:
    return sorted(
        [v for v in all_videos if v.series_id == series_id],
        key=lambda v: v.series_position or 0,
    )


def _find_next_in_series(
    series_videos: list[Video],
    watched_ids: set[str],
    current_position: int,
) -> Video | None:
    for v in series_videos:
        if (v.series_position or 0) > current_position and v.video_id not in watched_ids:
            return v
    return None


def _is_series_completed(series_videos: list[Video], watched_ids: set[str]) -> bool:
    return all(v.video_id in watched_ids for v in series_videos)


def _softmax(scores: list[float], temperature: float = 1.0) -> list[float]:
    if not scores:
        return []
    max_s = max(scores)
    exps = [math.exp((s - max_s) / max(temperature, 0.01)) for s in scores]
    total = sum(exps)
    return [e / total for e in exps]


def _weighted_choice(items: list, weights: list[float]):
    if not items:
        return None
    total = sum(weights)
    if total == 0:
        return random.choice(items)
    r = random.random() * total
    cumulative = 0.0
    for item, w in zip(items, weights):
        cumulative += w
        if r <= cumulative:
            return item
    return items[-1]


def recommend(
    db: Session,
    user: User,
    current_video: Video,
) -> RecommendationResult:
    reasoning = []
    all_videos = _get_all_videos(db)
    watch_history = _get_user_watch_history(db, user.user_id)
    watched_ids = {wh.video_id for wh in watch_history}

    # Slot 1: Series continuation
    slot1 = None
    if current_video.series_id:
        series_videos = _get_series_videos(all_videos, current_video.series_id)
        next_video = _find_next_in_series(
            series_videos, watched_ids, current_video.series_position or 0
        )
        if next_video:
            slot1 = _video_to_dict(next_video)
            reasoning.append(
                f"Slot 1: next in series '{current_video.series_id}' = "
                f"{next_video.video_id} (position {next_video.series_position})"
            )
        else:
            reasoning.append(
                f"Slot 1: no more episodes in series '{current_video.series_id}'"
            )

    # Slot 2: Engine pick
    slot2 = _pick_slot2(
        db, user, current_video, all_videos, watch_history, watched_ids, reasoning
    )

    return RecommendationResult(slot1=slot1, slot2=slot2, reasoning=reasoning)


def _pick_slot2(
    db: Session,
    user: User,
    current_video: Video,
    all_videos: list[Video],
    watch_history: list[WatchHistory],
    watched_ids: set[str],
    reasoning: list[str],
) -> dict | None:
    content_type = current_video.content_type

    # Build pool: one candidate per series, excluding current series
    pool = _build_candidate_pool(
        all_videos, watch_history, watched_ids,
        current_video.series_id, content_type, reasoning,
    )

    if not pool:
        reasoning.append("Slot 2: no candidates available")
        return None

    if content_type == "aspiration":
        return _aspiration_pick(
            db, user, current_video, pool, watch_history, reasoning
        )
    elif content_type == "entertainment":
        return _bucket_pick(
            pool, current_video.category,
            same_pct=0.40, other_same_type_pct=0.30, aspiration_pct=0.30,
            content_type="entertainment", reasoning=reasoning,
        )
    else:  # utility
        return _bucket_pick(
            pool, current_video.category,
            same_pct=0.50, other_same_type_pct=0.30, aspiration_pct=0.20,
            content_type="utility", reasoning=reasoning,
        )


@dataclass
class PoolCandidate:
    video: Video
    series_id: str
    is_revisit: bool = False
    days_since_completion: float = 0.0
    avg_quiz_score: float = 0.5


def _build_candidate_pool(
    all_videos: list[Video],
    watch_history: list[WatchHistory],
    watched_ids: set[str],
    exclude_series_id: str | None,
    current_content_type: str,
    reasoning: list[str],
) -> list[PoolCandidate]:
    # Group videos by series
    series_map: dict[str, list[Video]] = {}
    for v in all_videos:
        if v.series_id:
            series_map.setdefault(v.series_id, []).append(v)

    # Sort each series by position
    for sid in series_map:
        series_map[sid].sort(key=lambda v: v.series_position or 0)

    # Build watch history lookup
    watched_at_map = {}
    quiz_scores_map: dict[str, list[float]] = {}
    for wh in watch_history:
        watched_at_map[wh.video_id] = wh.watched_at
        if wh.quiz_scores:
            vid = wh.video_id
            series_id_for_vid = None
            for v in all_videos:
                if v.video_id == vid:
                    series_id_for_vid = v.series_id
                    break
            if series_id_for_vid:
                quiz_scores_map.setdefault(series_id_for_vid, []).extend(
                    wh.quiz_scores.values()
                )

    pool = []
    now = datetime.now(timezone.utc)

    for series_id, series_videos in series_map.items():
        if series_id == exclude_series_id:
            continue

        completed = _is_series_completed(series_videos, watched_ids)
        series_content_type = series_videos[0].content_type

        if completed:
            if series_content_type in ("utility", "entertainment"):
                # Completed utility/entertainment: excluded entirely
                continue

            # Completed aspiration: re-enters as episode 1 with revisit penalty
            representative = series_videos[0]
            # Calculate days since last watch in series
            last_watched = max(
                (watched_at_map.get(v.video_id, now) for v in series_videos),
                default=now,
            )
            days_since = (now - last_watched).total_seconds() / 86400.0

            scores = quiz_scores_map.get(series_id, [])
            avg_score = sum(scores) / len(scores) if scores else 0.5

            pool.append(
                PoolCandidate(
                    video=representative,
                    series_id=series_id,
                    is_revisit=True,
                    days_since_completion=days_since,
                    avg_quiz_score=avg_score,
                )
            )
        else:
            # Find next unwatched episode
            next_ep = None
            for v in series_videos:
                if v.video_id not in watched_ids:
                    next_ep = v
                    break

            if next_ep:
                pool.append(
                    PoolCandidate(
                        video=next_ep,
                        series_id=series_id,
                    )
                )

    reasoning.append(f"Slot 2 pool: {len(pool)} candidates from {len(series_map)} series")
    return pool


def _aspiration_pick(
    db: Session,
    user: User,
    current_video: Video,
    pool: list[PoolCandidate],
    watch_history: list[WatchHistory],
    reasoning: list[str],
) -> dict | None:
    storage = get_storage_client()
    knowledge = user.knowledge_state or {}
    current_category = current_video.category
    adjacent_categories = ADJACENCY.get(current_category, [])

    # Temperature by user state
    temperature = {"new": 1.5, "warming_up": 1.0, "established": 0.7}.get(
        user.maturity, 1.0
    )

    scored_candidates = []
    for candidate in pool:
        video = candidate.video

        # Only score aspiration videos with gap scoring
        if video.content_type != "aspiration":
            scored_candidates.append((candidate, 0.1))  # Low baseline for non-aspiration
            continue

        # Load concept profile for the representative video
        key = f"videos/{video.video_id}/concept_profile.json"
        try:
            concept_profile = storage.get_json(key)
        except Exception:
            scored_candidates.append((candidate, 0.1))
            continue

        cat_knowledge = knowledge.get(video.category, {})

        # Gap score: sum(coverage * (1 - knowledge))
        relevance = sum(
            coverage * (1.0 - cat_knowledge.get(concept, 0.0))
            for concept, coverage in concept_profile.items()
        )

        if candidate.is_revisit:
            # Revisit penalty
            time_decay = 1.0 - math.exp(-candidate.days_since_completion / 30.0)
            final_score = relevance * (1.0 - candidate.avg_quiz_score) * time_decay
            reasoning.append(
                f"  {video.video_id} (revisit): relevance={relevance:.2f}, "
                f"quiz_score={candidate.avg_quiz_score:.2f}, "
                f"time_decay={time_decay:.2f}, final={final_score:.2f}"
            )
        else:
            final_score = relevance
            reasoning.append(
                f"  {video.video_id}: relevance={relevance:.2f}"
            )

        # Apply category distribution weight
        if video.category == current_category:
            weight = 0.80
        elif video.category in adjacent_categories:
            weight = 0.15
        else:
            weight = 0.05

        final_score *= weight
        scored_candidates.append((candidate, final_score))

    if not scored_candidates:
        return None

    candidates, scores = zip(*scored_candidates)
    probabilities = _softmax(list(scores), temperature)

    reasoning.append(f"Aspiration pick: temperature={temperature}")

    selected = _weighted_choice(list(candidates), probabilities)
    if selected:
        reasoning.append(f"Slot 2 selected: {selected.video.video_id}")
        return _video_to_dict(selected.video)

    return None


def _bucket_pick(
    pool: list[PoolCandidate],
    current_category: str,
    same_pct: float,
    other_same_type_pct: float,
    aspiration_pct: float,
    content_type: str,
    reasoning: list[str],
) -> dict | None:
    # Split pool into buckets
    same_category = [c for c in pool if c.video.category == current_category]
    other_same_type = [
        c for c in pool
        if c.video.content_type == content_type and c.video.category != current_category
    ]
    aspiration = [c for c in pool if c.video.content_type == "aspiration"]

    reasoning.append(
        f"Bucket split ({content_type}): same_cat={len(same_category)}, "
        f"other_{content_type}={len(other_same_type)}, aspiration={len(aspiration)}"
    )

    # Build weighted bucket selection
    buckets = [
        (same_category, same_pct),
        (other_same_type, other_same_type_pct),
        (aspiration, aspiration_pct),
    ]

    # Filter out empty buckets and redistribute
    non_empty = [(b, w) for b, w in buckets if b]
    if not non_empty:
        return None

    total_weight = sum(w for _, w in non_empty)
    r = random.random() * total_weight
    cumulative = 0.0

    for bucket, weight in non_empty:
        cumulative += weight
        if r <= cumulative:
            selected = random.choice(bucket)
            reasoning.append(f"Slot 2 selected: {selected.video.video_id}")
            return _video_to_dict(selected.video)

    selected = random.choice(non_empty[-1][0])
    reasoning.append(f"Slot 2 selected: {selected.video.video_id}")
    return _video_to_dict(selected.video)
