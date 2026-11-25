import requests
import json

URL = "https://turnmark.github.io/api/v1/2026/20260503.json"


def inspect(value):
    if isinstance(value, dict):
        result = []
        for v in value.values():
            result.extend(inspect(v))
        return result

    if isinstance(value, list):
        result = []
        for v in value:
            result.extend(inspect(v))
        return result

    return [value]


def main():
    response = requests.get(URL, timeout=30)
    response.raise_for_status()

    data = response.json()
    stadiums = data["programs"]["stadiums"]

    print("===== オッズ欠損レースの艇情報調査 =====")

    for stadium_no, stadium in stadiums.items():
        for race_no, race in stadium.get("races", {}).items():

            odds = race.get("odds") or {}
            values = inspect(odds.get("trifecta"))

            valid = sum(
                isinstance(v, (int, float)) and v > 0
                for v in values
            )

            if valid == 120:
                continue

            print("\n" + "=" * 40)
            print(f"場 {stadium_no}・{race_no}R")
            print(f"レース名: {race.get('title')}")
            print(f"正常値: {valid} / 120")

            print("\n----- オッズ以外のレース情報 -----")

            for key, value in race.items():
                if key == "odds":
                    continue

                print(f"\n【{key}】")
                print(json.dumps(
                    value,
                    ensure_ascii=False,
                    indent=2
                ))


if __name__ == "__main__":
    main()
