"""Session metrics tracking for whisper-typing."""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

from whisper_typing.paths import get_history_dir

logger = logging.getLogger(__name__)


def _metrics_file() -> Path:
    return get_history_dir() / "metrics.jsonl"


def _transcripts_file() -> Path:
    return get_history_dir() / "transcripts.jsonl"


@dataclass
class SessionMetric:
    """A single recording session's metrics."""

    timestamp: str = ""
    words: int = 0
    chars: int = 0
    recording_duration_s: float = 0.0
    processing_duration_s: float = 0.0
    model: str = ""
    device: str = ""
    language_detected: str = ""

    @property
    def typing_time_saved_s(self) -> float:
        if self.words == 0:
            return 0.0
        return self.words / 0.667  # ~40 WPM

    @property
    def net_time_saved_s(self) -> float:
        return max(0.0, self.typing_time_saved_s - self.recording_duration_s - self.processing_duration_s)


@dataclass
class AggregateMetrics:
    """Aggregated metrics across all sessions."""

    total_sessions: int = 0
    total_words: int = 0
    total_chars: int = 0
    total_recording_s: float = 0.0
    total_processing_s: float = 0.0
    total_time_saved_s: float = 0.0
    avg_words_per_session: float = 0.0
    avg_recording_s: float = 0.0
    avg_processing_s: float = 0.0
    sessions_today: int = 0
    words_today: int = 0
    time_saved_today_s: float = 0.0
    streak_days: int = 0
    words_by_day: dict[str, int] = field(default_factory=dict)
    recent: list[SessionMetric] = field(default_factory=list)


def save_metric(metric: SessionMetric) -> None:
    """Append a session metric to the JSONL file."""
    try:
        path = _metrics_file()
        path.parent.mkdir(exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(metric), ensure_ascii=False) + "\n")
    except Exception:
        logger.exception("Failed to save metric")


def load_metrics() -> list[SessionMetric]:
    """Load all session metrics from the JSONL file."""
    path = _metrics_file()
    if not path.exists():
        return []
    results = []
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    results.append(SessionMetric(**data))
                except (json.JSONDecodeError, TypeError):
                    pass
    except OSError:
        logger.exception("Failed to load metrics")
    return results


def backfill_from_transcripts() -> int:
    """Migrate legacy transcripts to metrics. Returns count of new entries."""
    transcript_path = _transcripts_file()
    if not transcript_path.exists():
        return 0

    # Get existing metric timestamps to avoid duplicates
    existing = {m.timestamp for m in load_metrics()}

    count = 0
    try:
        with transcript_path.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    ts = data.get("timestamp", "")
                    text = data.get("text", "")
                    if not ts or ts in existing:
                        continue
                    words = len(text.split()) if text.strip() else 0
                    if words == 0:
                        continue
                    metric = SessionMetric(
                        timestamp=ts,
                        words=words,
                        chars=len(text),
                        recording_duration_s=0.0,
                        processing_duration_s=0.0,
                        model="legacy",
                        device="unknown",
                    )
                    save_metric(metric)
                    existing.add(ts)
                    count += 1
                except (json.JSONDecodeError, TypeError):
                    pass
    except OSError:
        logger.exception("Failed to backfill transcripts")
    return count


def _calculate_streak(sessions: list[SessionMetric]) -> int:
    """Count consecutive days with at least one session, backward from today."""
    if not sessions:
        return 0

    days_with_sessions: set[str] = set()
    for s in sessions:
        if s.timestamp:
            days_with_sessions.add(s.timestamp[:10])

    today = datetime.now(UTC).date()
    streak = 0
    day = today
    while day.isoformat() in days_with_sessions:
        streak += 1
        day -= timedelta(days=1)

    return streak


def _words_by_day(sessions: list[SessionMetric], days: int = 7) -> dict[str, int]:
    """Aggregate words per day for the last N days."""
    today = datetime.now(UTC).date()
    result: dict[str, int] = {}
    for i in range(days):
        d = (today - timedelta(days=i)).isoformat()
        result[d] = 0

    for s in sessions:
        day = s.timestamp[:10] if s.timestamp else ""
        if day in result:
            result[day] += s.words

    return result


def aggregate(sessions: list[SessionMetric] | None = None) -> AggregateMetrics:
    """Compute aggregate metrics from session list."""
    if sessions is None:
        sessions = load_metrics()

    if not sessions:
        return AggregateMetrics()

    today = datetime.now(UTC).date().isoformat()

    agg = AggregateMetrics()
    agg.total_sessions = len(sessions)

    for s in sessions:
        agg.total_words += s.words
        agg.total_chars += s.chars
        agg.total_recording_s += s.recording_duration_s
        agg.total_processing_s += s.processing_duration_s
        agg.total_time_saved_s += s.net_time_saved_s

        if s.timestamp.startswith(today):
            agg.sessions_today += 1
            agg.words_today += s.words
            agg.time_saved_today_s += s.net_time_saved_s

    if agg.total_sessions > 0:
        agg.avg_words_per_session = agg.total_words / agg.total_sessions
        agg.avg_recording_s = agg.total_recording_s / agg.total_sessions
        agg.avg_processing_s = agg.total_processing_s / agg.total_sessions

    agg.streak_days = _calculate_streak(sessions)
    agg.words_by_day = _words_by_day(sessions)
    agg.recent = sessions[-30:]
    return agg


def format_duration(seconds: float) -> str:
    """Format seconds into a human-readable string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds) // 60
    secs = seconds - minutes * 60
    if minutes < 60:
        return f"{minutes}m {secs:.0f}s"
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}m"
