
import requests
import json

URL = "https://turnmark.github.io/api/v1/2026/20260503.json"

EXPECTED = {
    "trifecta": 120,
    "trio": 20,
    "exacta": 30,
    "quinella": 15,
    "quinella_place": 30,
    "win": 6,
    "place": 12,
}


def flatten(value):
    if isinstance(value, dict):
        result = []
        for v in value.values():
            result.extend(flatten(v))
        return result

    if isinstance(value, list):
        result = []
        for v in value:
            result.extend(flatten(v))
        return result

    return [value]


def show(title, value):
    print(f"\n【{title}】")
    print(json.dumps(
        value,
        ensure_ascii=False,
        indent=2
    ))


def main():
    response = requests.get(URL, timeout=30)
    response.raise_for_status()

    data = response.json()
    stadiums = data["programs"]["stadiums"]

    stadium = stadiums.get("20")

    if stadium is None:
        print("場20のデータが見つかりません")
        return

    print("===== 場20・9R〜12R 原因調査 =====")
    print(f"データ日付: {data.get('date')}")

    for race_no in ["9", "10", "11", "12"]:
        race = stadium.get("races", {}).get(race_no)

        print("\n" + "=" * 50)

        if race is None:
            print(f"場20・{race_no}R のデータがありません")
            continue

        print(f"場20・{race_no}R")
        print(f"レース名: {race.get('title')}")

        basic = {
            key: value
            for key, value in race.items()
            if key not in ["odds", "racers", "preview", "result"]
        }
        show("レース基本情報", basic)

        show("出走選手情報", race.get("racers"))
        show("展示・直前情報", race.get("preview"))
        show("レース結果情報", race.get("result"))

        show("返還情報", race.get("refunds"))

        print("\n【券種別オッズ状況】")
        odds = race.get("odds") or {}

        for name, expected in EXPECTED.items():
            values = flatten(odds.get(name))
            valid = sum(
                isinstance(v, (int, float)) and v > 0
                for v in values
            )

            print(
                f"{name}: 正常値 {valid}/{expected} "
                f"項目数 {len(values)}"
            )


if __name__ == "__main__":
    main()
