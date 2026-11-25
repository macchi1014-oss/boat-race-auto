import csv
import io
from datetime import datetime, timedelta
from itertools import permutations
from zoneinfo import ZoneInfo

import requests


def main():
    today = datetime.now(ZoneInfo("Asia/Tokyo")).date()

    expected_odds = {
        "3連単_" + "-".join(map(str, combo))
        for combo in permutations(range(1, 7), 3)
    }

    found = False

    for days_ago in range(30):
        target_date = today - timedelta(days=days_ago)
        date_text = target_date.strftime("%Y/%m/%d")
        url = f"https://boatracecsv.github.io/data/previews/od3/{date_text}.csv"

        print(f"\n確認日: {date_text}")

        try:
            response = requests.get(url, timeout=20)
            print(f"HTTP status: {response.status_code}")

            if response.status_code == 404:
                print("CSVなし")
                continue

            response.raise_for_status()

            text = response.content.decode("utf-8-sig")
            reader = csv.DictReader(io.StringIO(text))
            headers = reader.fieldnames or []
            rows = list(reader)

            actual_odds = set(headers) & expected_odds

            print(f"CSV列数: {len(headers)}")
            print(f"レース行数: {len(rows)}")
            print(f"3連単オッズ列: {len(actual_odds)} / 120")

            if rows:
                first = rows[0]
                print(f"レースコード: {first.get('レースコード', '')}")
                print(f"取得日時: {first.get('取得日時', '')}")

                filled = sum(
                    1 for column in expected_odds
                    if first.get(column, "").strip() not in ("", "0", "0.0")
                )
                print(f"有効なオッズ数: {filled} / 120")

            if len(actual_odds) == 120 and rows:
                print("判定: オッズCSVを正常に取得できました！")
                found = True
                break

            print("データ形式が想定と異なります")

        except Exception as e:
            print(f"取得エラー: {e}")

    if not found:
        raise RuntimeError("過去30日間で正常なオッズCSVを確認できませんでした。")

    print("\nテスト成功！")


if __name__ == "__main__":
    main()
