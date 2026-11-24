
import csv
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from itertools import permutations

import requests

JST = ZoneInfo("Asia/Tokyo")
DATA_DIR = "data"
PREDICTION_FILE = os.path.join(DATA_DIR, "predictions.csv")
API_URL = "https://boatraceopenapi.github.io/api/v1/today.json"

FIELDS = [
    "date", "stadium_number", "race_number",
    "closed_at", "first", "second", "third",
    "candidates", "exhibition_count", "generated_at"
]


def number(value):
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (ValueError, TypeError):
        return None


def parse_deadline(value):
    if not value:
        return None

    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=JST)
        return dt.astimezone(JST)
    except ValueError:
        return None


def rank_scores(boats, field, higher, weight):
    values = []

    for lane, boat in boats.items():
        value = number(boat.get(field))
        if value is not None:
            values.append((lane, value))

    values.sort(
        key=lambda item: item[1],
        reverse=higher
    )

    scores = {}

    for index, (lane, value) in enumerate(values):
        scores[lane] = (len(values) - index) * weight

    return scores


def predict_race(race):
    racers = race.get("racers") or {}
    preview = race.get("preview") or {}
    preview_racers = preview.get("racers") or {}

    if len(racers) != 6:
        return None

    boats = {}

    exhibition_count = 0

    for lane in range(1, 7):
        key = str(lane)
        base = racers.get(key) or {}
        before = preview_racers.get(key) or {}

        boats[key] = {
            **base,
            **before
        }

        if number(before.get("exhibition_time")) is not None:
            exhibition_count += 1

    scores = {str(lane): 0 for lane in range(1, 7)}
    used_metrics = 0

    metrics = [
        ("national_win_rate", True, 2),
        ("local_win_rate", True, 1),
        ("motor_top_2_percent", True, 2),
        ("average_start_timing", False, 1),
        ("exhibition_time", False, 2),
    ]

    for field, higher, weight in metrics:
        result = rank_scores(
            boats, field, higher, weight
        )

        if result:
            used_metrics += 1

        for lane, points in result.items():
            scores[lane] += points

    if used_metrics == 0:
        return None

    top_boats = sorted(
        scores,
        key=lambda lane: (-scores[lane], int(lane))
    )[:4]

    combinations = []

    for first, second, third in permutations(top_boats, 3):
        total = (
            scores[first] * 3
            + scores[second] * 2
            + scores[third]
        )

        combinations.append(
            (total, first, second, third)
        )

    combinations.sort(
        key=lambda item: (
            -item[0],
            int(item[1]),
            int(item[2]),
            int(item[3])
        )
    )

    return combinations[:3], exhibition_count


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    now = datetime.now(JST)
    today = now.strftime("%Y%m%d")

    print("レースデータを取得中...")

    response = requests.get(API_URL, timeout=30)
    response.raise_for_status()
    data = response.json()

    file_path = os.path.join(
        DATA_DIR, f"{today}.json"
    )

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(
            data, f, ensure_ascii=False, indent=2
        )

    stadiums = (
        data.get("programs", {})
        .get("stadiums", {})
    )

    records = {}

    if os.path.exists(PREDICTION_FILE):
        with open(
            PREDICTION_FILE,
            newline="",
            encoding="utf-8-sig"
        ) as f:
            for row in csv.DictReader(f):
                key = (
                    row.get("date", ""),
                    row.get("stadium_number", ""),
                    row.get("race_number", "")
                )
                records[key] = row

    new_count = 0
    update_count = 0

    for stadium_no, stadium in stadiums.items():
        races = stadium.get("races") or {}

        for race_no, race in races.items():
            date = race.get(
                "date", now.strftime("%Y-%m-%d")
            )

            key = (
                str(date),
                str(stadium_no),
                str(race_no)
            )

            closed_at = race.get("closed_at")
            deadline = parse_deadline(closed_at)

            if deadline is None or deadline <= now:
                continue

            result = predict_race(race)

            if result is None:
                continue

            picks, exhibition_count = result
            best = picks[0]

            candidates = ";".join(
                f"{a}-{b}-{c}"
                for score, a, b, c in picks
            )

            row = {
                "date": date,
                "stadium_number": stadium_no,
                "race_number": race_no,
                "closed_at": closed_at,
                "first": best[1],
                "second": best[2],
                "third": best[3],
                "candidates": candidates,
                "exhibition_count": exhibition_count,
                "generated_at": now.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            }

            if key in records:
                update_count += 1
            else:
                new_count += 1

            records[key] = row

    with open(
        PREDICTION_FILE,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as f:
        writer = csv.DictWriter(
            f, fieldnames=FIELDS
        )
        writer.writeheader()

        for row in records.values():
            writer.writerow({
                field: row.get(field, "")
                for field in FIELDS
            })

    print("===== 予想処理完了 =====")
    print(f"開催場数: {len(stadiums)}")
    print(f"今回の新規予想: {new_count}")
    print(f"締切前の予想更新: {update_count}")
    print(f"保存先: {PREDICTION_FILE}")


if __name__ == "__main__":
    main()
