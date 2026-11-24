
import csv
import os

DATA_DIR = "data"
CSV_FILE = os.path.join(DATA_DIR, "races.csv")

FIELDS = [
    "date",
    "venue",
    "race_no",
    "combination",
    "stake_yen",
    "result",
    "payout_yen"
]


def initialize():
    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()

    print("Boat Race Auto initialized!")


def add_prediction(date, venue, race_no, combination):
    initialize()

    with open(CSV_FILE, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writerow({
            "date": date,
            "venue": venue,
            "race_no": race_no,
            "combination": combination,
            "stake_yen": 100,
            "result": "",
            "payout_yen": 0
        })

    print("Prediction saved!")


def show_statistics():
    initialize()

    total_bet = 0
    total_return = 0
    hits = 0
    races = set()

    with open(CSV_FILE, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            total_bet += int(row["stake_yen"] or 0)
            payout = int(row["payout_yen"] or 0)
            total_return += payout

            if payout > 0:
                hits += 1

            races.add((
                row["date"],
                row["venue"],
                row["race_no"]
            ))

    rate = (
        total_return / total_bet * 100
        if total_bet else 0
    )

    print("\n===== BOAT RACE STATISTICS =====")
    print(f"Recorded races: {len(races)}")
    print(f"Hit tickets: {hits}")
    print(f"Total bets: {total_bet} yen")
    print(f"Total returns: {total_return} yen")
    print(f"Recovery rate: {rate:.2f}%")
    print(f"Profit/Loss: {total_return - total_bet} yen")


if __name__ == "__main__":
    initialize()
    show_statistics()
