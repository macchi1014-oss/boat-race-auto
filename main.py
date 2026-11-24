
import csv
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

DATA_DIR = "data"
CSV_FILE = os.path.join(DATA_DIR, "races.csv")
CHECK_FILE = os.path.join(DATA_DIR, "source_check.txt")

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


def check_boatrace_site():
    today = datetime.now(
        ZoneInfo("Asia/Tokyo")
    ).strftime("%Y%m%d")

    url = (
        "https://www.boatrace.jp/owpc/pc/race/index"
        f"?hd={today}"
    )

    try:
        response = requests.get(
            url,
            timeout=20,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )
        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        title = (
            soup.title.get_text(strip=True)
            if soup.title else "タイトルなし"
        )

        message = (
            "公式サイト接続確認\n"
            f"確認日時: {today}\n"
            f"HTTP status: {response.status_code}\n"
            f"ページタイトル: {title}\n"
            f"取得文字数: {len(response.text)}\n"
        )

    except Exception as e:
        message = (
            "公式サイト接続確認に失敗\n"
            f"確認日時: {today}\n"
            f"エラー: {e}\n"
        )

    with open(
        CHECK_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        f.write(message)

    print(message)


def show_statistics():
    total_bet = 0
    total_return = 0
    hits = 0
    races = set()

    with open(
        CSV_FILE,
        newline="",
        encoding="utf-8-sig"
    ) as f:
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
    check_boatrace_site()
    show_statistics()
