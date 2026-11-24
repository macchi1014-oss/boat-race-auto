
import csv
import json
import os
import hashlib
from datetime import datetime
from zoneinfo import ZoneInfo
from itertools import permutations

import requests

JST = ZoneInfo("Asia/Tokyo")
DATA_DIR = "data"
PREDICTION_FILE = os.path.join(DATA_DIR, "predictions.csv")
RESULT_FILE = os.path.join(DATA_DIR, "race_results.csv")
SNAPSHOT_FILE = os.path.join(DATA_DIR, "race_snapshots.jsonl")
STATS_FILE = os.path.join(DATA_DIR, "statistics.csv")
API_URL = "https://boatraceopenapi.github.io/api/v1/today.json"

PREDICTION_FIELDS = [
    "date", "stadium_number", "race_number", "closed_at",
    "main_candidates", "backup_candidates",
    "exhibition_count", "generated_at",
    "confidence_score", "confidence_level",
    "evaluation_summary", "evaluation_details",
    "missing_metrics"
]

RESULT_FIELDS = [
    "date", "stadium_number", "race_number",
    "winning_combination", "payout_yen",
    "main_hit", "main_return_yen",
    "backup_hit", "backup_return_yen",
    "total_stake_yen", "total_return_yen",
    "profit_yen", "settled_at"
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

    values.sort(key=lambda item: item[1], reverse=higher)

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
        boats[key] = {**base, **before}

        if number(before.get("exhibition_time")) is not None:
            exhibition_count += 1

    scores = {str(lane): 0 for lane in range(1, 7)}
    used_metrics = 0
    evaluation_details = {}
    summary_parts = []
    missing_metrics = []

    metrics = [
        ("national_win_rate", True, 2),
        ("local_win_rate", True, 1),
        ("motor_top_2_percent", True, 2),
        ("average_start_timing", False, 1),
        ("exhibition_time", False, 2),
    ]

    for field, higher, weight in metrics:
        result = rank_scores(boats, field, higher, weight)

        values = {
            lane: number(boats[lane].get(field))
            for lane in boats
        }
        available = sum(
            value is not None for value in values.values()
        )

        if available < 6:
            missing_metrics.append(field)

        if result:
            used_metrics += 1

        for lane, points in result.items():
            scores[lane] += points

        ranked = sorted(
            result.items(),
            key=lambda item: (-item[1], int(item[0]))
        )

        evaluation_details[field] = {
            "weight": weight,
            "higher_is_better": higher,
            "available_boats": available,
            "values": values,
            "points": result,
            "ranking": [lane for lane, points in ranked]
        }

        if ranked:
            summary_parts.append(
                f"{field}: {ranked[0][0]}号艇が上位"
            )

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

    # 本線：最上位の1着軸から上位3通り
    main = combinations[:3]
    main_axis = main[0][1]
    main_set = {
        f"{a}-{b}-{c}" for score, a, b, c in main
    }

    # 押さえ：本線とは異なる1着軸から3通り
    backup = []
    for item in combinations:
        score, first, second, third = item
        combo = f"{first}-{second}-{third}"

        if first == main_axis:
            continue
        if combo in main_set:
            continue

        backup.append(item)
        if len(backup) == 3:
            break

    if len(main) != 3 or len(backup) != 3:
        return None

    main_text = ";".join(
        f"{a}-{b}-{c}" for score, a, b, c in main
    )
    backup_text = ";".join(
        f"{a}-{b}-{c}" for score, a, b, c in backup
    )

    ordered_scores = sorted(
        scores.values(), reverse=True
    )
    first_score = ordered_scores[0]
    second_score = ordered_scores[1]

    max_possible = sum(
        6 * weight for field, higher, weight in metrics
    )

    confidence_score = round(
        max(0, first_score - second_score)
        / max_possible * 100,
        1
    )

    if confidence_score >= 15:
        confidence_level = "相対評価：高め"
    elif confidence_score >= 7:
        confidence_level = "相対評価：中程度"
    else:
        confidence_level = "相対評価：低め"

    evaluation_summary = " / ".join(summary_parts)

    return (
        main_text,
        backup_text,
        exhibition_count,
        confidence_score,
        confidence_level,
        evaluation_summary,
        json.dumps(evaluation_details, ensure_ascii=False),
        ";".join(missing_metrics)
    )


def read_csv(path):
    if not os.path.exists(path):
        return []

    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path, fields, records):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)

def record_prediction_snapshots(stadiums, prediction_map, now):
    last_signatures = {}

    if os.path.exists(SNAPSHOT_FILE):
        with open(SNAPSHOT_FILE, encoding="utf-8") as f:
            for line in f:
                try:
                    old = json.loads(line)
                    key = (
                        old["date"],
                        str(old["stadium_number"]),
                        str(old["race_number"])
                    )
                    last_signatures[key] = old.get("signature")
                except (json.JSONDecodeError, KeyError):
                    continue

    records = []

    for stadium_no, stadium in stadiums.items():
        for race_no, race in (stadium.get("races") or {}).items():
           date = race.get("date", now.strftime("%Y-%m-%d")) 
            key = (str(date), str(stadium_no), str(race_no))

            prediction = prediction_map.get(key)
            if not prediction:
                continue

            deadline = parse_deadline(race.get("closed_at"))
            if deadline is None or deadline <= now:
                continue

            racers = race.get("racers") or {}
            preview = race.get("preview") or {}

            payload = {
                "date": date,
                "stadium_number": stadium_no,
                "race_number": race_no,
                "closed_at": race.get("closed_at", ""),
                "prediction": {
                    "main_candidates": prediction.get("main_candidates"),
                    "backup_candidates": prediction.get("backup_candidates"),
                    "confidence_score": prediction.get("confidence_score"),
                    "evaluation_details": prediction.get("evaluation_details")
                },
                "racers": racers,
                "preview": preview
            }

            signature = hashlib.sha256(
                json.dumps(
                    payload,
                    ensure_ascii=False,
                    sort_keys=True
                ).encode("utf-8")
            ).hexdigest()

            if last_signatures.get(key) == signature:
                continue

            record = {
                **payload,
                "captured_at": now.strftime("%Y-%m-%d %H:%M:%S"),
                "signature": signature
            }

            records.append(record)
            last_signatures[key] = signature

    if records:
        with open(SNAPSHOT_FILE, "a", encoding="utf-8") as f:
            for record in records:
                f.write(
                    json.dumps(record, ensure_ascii=False) + "\n"
                )

    print(f"予想時点スナップショット記録: {len(records)}件")
def get_winning_result(race):
    result = race.get("result") or {}
    result_racers = result.get("racers") or {}

    places = []
    for lane, racer in result_racers.items():
        place = number((racer or {}).get("place_number"))
        if place in (1, 2, 3):
            places.append((int(place), str(lane)))

    if len(places) != 3:
        return None

    places.sort()
    winning = "-".join(lane for place, lane in places)

    payouts = result.get("payouts") or {}
    trifecta = payouts.get("trifecta") or []

    payout_yen = None
    for item in trifecta:
        if item.get("combination") == winning:
            payout_yen = number(item.get("amount"))
            break

    if payout_yen is None:
        return None

    return winning, int(payout_yen)


def settle_results(stadiums, predictions, results):
    result_map = {
        (
            row["date"],
            row["stadium_number"],
            row["race_number"]
        ): row
        for row in results
    }

    prediction_map = {
        (
            row["date"],
            row["stadium_number"],
            row["race_number"]
        ): row
        for row in predictions
    }

    settled_count = 0
    now_text = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")

    for stadium_no, stadium in stadiums.items():
        for race_no, race in (stadium.get("races") or {}).items():
                         date = race.get("date", now.strftime("%Y-%m-%d"))
            key = (str(date), str(stadium_no), str(race_no))

            prediction = prediction_map.get(key)
            if not prediction:
                continue

            # 旧形式の予想は新方式の成績に混ぜない
            if not prediction.get("main_candidates"):
                continue

            if key in result_map:
                continue

            actual = get_winning_result(race)
            if actual is None:
                continue

            winning, payout = actual
            main = prediction["main_candidates"].split(";")
            backup = prediction["backup_candidates"].split(";")

            main_hit = winning in main
            backup_hit = winning in backup

            main_return = payout if main_hit else 0
            backup_return = payout if backup_hit else 0

            # 1通り100円、各グループ3通り
            total_stake = 600
            total_return = main_return + backup_return

            row = {
                "date": date,
                "stadium_number": stadium_no,
                "race_number": race_no,
                "winning_combination": winning,
                "payout_yen": payout,
                "main_hit": int(main_hit),
                "main_return_yen": main_return,
                "backup_hit": int(backup_hit),
                "backup_return_yen": backup_return,
                "total_stake_yen": total_stake,
                "total_return_yen": total_return,
                "profit_yen": total_return - total_stake,
                "settled_at": now_text
            }

            results.append(row)
            result_map[key] = row
            settled_count += 1

    return settled_count


def create_statistics(results):
    groups = {
        "main": {
            "races": 0, "hits": 0, "stake": 0, "returned": 0
        },
        "backup": {
            "races": 0, "hits": 0, "stake": 0, "returned": 0
        },
        "total": {
            "races": 0, "hits": 0, "stake": 0, "returned": 0
        }
    }

    for row in results:
        groups["main"]["races"] += 1
        groups["backup"]["races"] += 1
        groups["total"]["races"] += 1

        main_hit = int(row["main_hit"])
        backup_hit = int(row["backup_hit"])
        total_hit = int(main_hit or backup_hit)

        groups["main"]["hits"] += main_hit
        groups["backup"]["hits"] += backup_hit
        groups["total"]["hits"] += total_hit

        groups["main"]["stake"] += 300
        groups["backup"]["stake"] += 300
        groups["total"]["stake"] += 600

        groups["main"]["returned"] += int(row["main_return_yen"])
        groups["backup"]["returned"] += int(row["backup_return_yen"])
        groups["total"]["returned"] += int(row["total_return_yen"])

    rows = []
    for name, values in groups.items():
        races = values["races"]
        hits = values["hits"]
        stake = values["stake"]
        returned = values["returned"]

        rows.append({
            "category": name,
            "races": races,
            "hits": hits,
            "hit_rate_percent": round(hits / races * 100, 2) if races else 0,
            "stake_yen": stake,
            "return_yen": returned,
            "profit_yen": returned - stake,
            "recovery_rate_percent": round(returned / stake * 100, 2) if stake else 0
        })

    write_csv(
        STATS_FILE,
        [
            "category", "races", "hits", "hit_rate_percent",
            "stake_yen", "return_yen", "profit_yen",
            "recovery_rate_percent"
        ],
        rows
    )


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

    predictions = [
    row for row in read_csv(PREDICTION_FILE)
    if row.get("main_candidates") and row.get("backup_candidates")
]
    prediction_map = {
        (
            row["date"],
            row["stadium_number"],
            row["race_number"]
        ): row
        for row in predictions
    }

    new_count = 0
    update_count = 0

    for stadium_no, stadium in stadiums.items():
        for race_no, race in (stadium.get("races") or {}).items():
            date = race.get("date", now.strftime("%Y-%m-%d"))
            key = (str(date), str(stadium_no), str(race_no))

            deadline = parse_deadline(race.get("closed_at"))
            if deadline is None or deadline <= now:
                continue

            prediction = predict_race(race)
            if prediction is None:
                continue

            (
                main_text,
                backup_text,
                exhibition_count,
                confidence_score,
                confidence_level,
                evaluation_summary,
                evaluation_details,
                missing_metrics
            ) = prediction

            row = {
                "date": date,
                "stadium_number": stadium_no,
                "race_number": race_no,
                "closed_at": race.get("closed_at", ""),
                "main_candidates": main_text,
                "backup_candidates": backup_text,
                "exhibition_count": exhibition_count,
                "confidence_score": confidence_score,
                "confidence_level": confidence_level,
                "evaluation_summary": evaluation_summary,
                "evaluation_details": evaluation_details,
                "missing_metrics": missing_metrics,
                "generated_at": now.strftime("%Y-%m-%d %H:%M:%S")
            }

            if key in prediction_map:
                update_count += 1
            else:
                new_count += 1

            prediction_map[key] = row

    predictions = list(prediction_map.values())
    record_prediction_snapshots(stadiums, prediction_map, now)
    write_csv(PREDICTION_FILE, PREDICTION_FIELDS, predictions)

    results = read_csv(RESULT_FILE)
    settled_count = settle_results(stadiums, predictions, results)

    write_csv(RESULT_FILE, RESULT_FIELDS, results)
    create_statistics(results)

    print("===== 自動処理完了 =====")
    print(f"開催場数: {len(stadiums)}")
    print(f"新規予想: {new_count}")
    print(f"予想更新: {update_count}")
    print(f"今回の結果確定: {settled_count}")
    print(f"結果記録数: {len(results)}")
    print("本線・押さえ・合計の成績を更新しました。")


if __name__ == "__main__":
    main()
