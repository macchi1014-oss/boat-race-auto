
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
    "candidates", "generated_at"
]


def number(value):
    try:
        if value is None:
            return None
        return float(value)
    except (ValueError, TypeError):
        return None


def rank_scores(boats, getter, higher, weight):
    values = []

    for lane, boat in boats.items():
        value = number(getter(boat))
        if value is not None:
            values.append((lane, value))

    values.sort(key=lambda x: x[1], reverse=higher)

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

    exhibition_count = sum(
        number((preview_racers.get(str(lane)) or {}).get("exhibition_time"))
        is not None
        for lane in range(1, 7)
    )

    if exhibition_count < 4:
        return None

    boats = {}

    for lane in range(1, 7):
        base = racers.get(str(lane)) or {}
        before = preview_racers.get(str(lane)) or {}

        boats[str(lane)] = {
            **base,
            **before
        }

    scores = {str(lane): 0 for lane in range(1, 7)}

    metrics = [
        ("national_win_rate", True, 2),
        ("local_win_rate", True, 1),
        ("motor_top_2_percent", True, 2),
        ("average_start_timing", False, 1),
        ("exhibition_time", False, 2),
    ]

    for field, higher, weight in metrics:
        result = rank_scores(
            boats,
            lambda boat: boat.get(field),
            higher,
            weight
        )

        for lane, points in result.items():
            scores[lane] += points

    top_boats = sorted(
        scores,
        key=lambda lane: scores[lane],
        reverse=True
    )[:4]

    combinations = []

    for first, second, third in permutations(top_boats, 3):
        total = (
            scores[first] * 3
            + scores[second] * 2
            + scores[third]
        )
        combinations.append((total, first, second, third))

    combinations.sort(reverse=True)

    return combinations[:3]


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    now = datetime.now(JST)
    today = now.strftime("%Y%m%d")

    print("レースデータを取得中...")

    response = requests.get(API_URL, timeout=30)
    response.raise_for_status()
    data = response.json()

    file_path = os.path.join(DATA_DIR, f"{today}.json")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    stadiums = (
        data.get("programs", {})
        .get("stadiums", {})
    )

    existing = set()

    if os.path.exists(PREDICTION_FILE):
        with open(
            PREDICTION_FILE,
            newline="",
            encoding="utf-8-sig"
        ) as f:
            for row in csv.DictReader(f):
                existing.add((
                    row["date"],
                    row["stadium_number"],
                    row["race_number"]
                ))

    new_count = 0

    with open(
        PREDICTION_FILE,
        "a",
        newline="",
        encoding="utf-8-sig"
    ) as f:

        writer = csv.DictWriter(f, fieldnames=FIELDS)

        if os.path.getsize(PREDICTION_FILE) == 0:
            writer.writeheader()

        for stadium_no, stadium in stadiums.items():
            races = stadium.get("races") or {}

            for race_no, race in races.items():
                date = race.get("date", now.strftime("%Y-%m-%d"))
                key = (date, str(stadium_no), str(race_no))

                if key in existing:
                    continue

                closed_at = race.get("closed_at")

                if not closed_at:
                    continue

                try:
                    deadline = datetime.strptime(
                        closed_at,
                        "%Y-%m-%d %H:%M:%S"
                    ).replace(tzinfo=JST)
                except ValueError:
                    continue

                if deadline <= now:
                    continue

                picks = predict_race(race)

                if not picks:
                    continue

                best = picks[0]

                candidates = ";".join(
                    f"{a}-{b}-{c}"
                    for score, a, b, c in picks
                )

                writer.writerow({
                    "date": date,
                    "stadium_number": stadium_no,
                    "race_number": race_no,
                    "closed_at": closed_at,
                    "first": best[1],
                    "second": best[2],
                    "third": best[3],
                    "candidates": candidates,
                    "generated_at": now.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                })

                existing.add(key)
                new_count += 1

    print("===== 予想処理完了 =====")
    print(f"開催場数: {len(stadiums)}")
    print(f"今回の新規予想: {new_count}")
    print(f"保存先: {PREDICTION_FILE}")


if __name__ == "__main__":
    main()
