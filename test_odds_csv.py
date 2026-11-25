
import csv
import io
from datetime import datetime
from itertools import permutations
from zoneinfo import ZoneInfo

import requests


def main():
    today = datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y/%m/%d")
    url = f"https://boatracecsv.github.io/data/previews/od3/{today}.csv"

    print(f"取得先: {url}")
    response = requests.get(url, timeout=30)
    print(f"HTTP status: {response.status_code}")
    response.raise_for_status()

    text = response.content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    headers = reader.fieldnames or []
    rows = list(reader)

    expected_odds = {
        "3連単_" + "-".join(map(str, combo))
        for combo in permutations(range(1, 7), 3)
    }
    actual_odds = set(headers) & expected_odds
    missing_odds = sorted(expected_odds - actual_odds)

    print(f"CSV列数: {len(headers)}")
    print(f"レース行数: {len(rows)}")
    print(f"3連単オッズ列: {len(actual_odds)} / 120")

    if missing_odds:
        print("不足しているオッズ列（最大10件）:")
        print(", ".join(missing_odds[:10]))

    if not rows:
        raise RuntimeError("CSVは取得できましたが、レース行がありません。")

    first = rows[0]
    race_code = first.get("レースコード", "")
    captured_at = first.get("取得日時", "")
    filled = sum(
        1 for column in expected_odds
        if first.get(column, "").strip() not in ("", "0", "0.0")
    )

    print(f"先頭行のレースコード: {race_code}")
    print(f"先頭行の取得日時: {captured_at}")
    print(f"先頭行の有効なオッズ数: {filled} / 120")

    if len(actual_odds) != 120:
        raise RuntimeError("3連単オッズ列が120列そろっていません。")
    if len(race_code) != 12 or not race_code.isdigit():
        raise RuntimeError("レースコードが12桁の数字ではありません。")

    print("判定: CSV取得・120列・レースコードの基本確認は成功")


if __name__ == "__main__":
    main()
