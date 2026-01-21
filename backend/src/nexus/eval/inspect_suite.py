from __future__ import annotations

import json
import pathlib
from datetime import datetime

import psycopg

from nexus.config import get_settings


def load_questions() -> list[dict]:
    questions_path = pathlib.Path("data/eval/questions.jsonl")
    items: list[dict] = []
    if not questions_path.exists():
        return items
    with questions_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            items.append(json.loads(line))
    return items


def run_eval() -> dict:
    questions = load_questions()
    # Placeholder scoring: mark count only. Hook up inspect_ai suite here.
    score = {"questions": len(questions), "timestamp": datetime.utcnow().isoformat()}
    settings = get_settings()
    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO eval_runs(collection_id, model, score) VALUES ((SELECT id FROM collections WHERE name=%s LIMIT 1), %s, %s) RETURNING id",
                ("test", settings.chat_model, json.dumps(score)),
            )
    return score


if __name__ == "__main__":
    print(run_eval())
