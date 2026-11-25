
import requests
import json

URL = "https://turnmark.github.io/api/v1/2026/20260502.json"

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


def inspect_race(stadium, race_no):
    race = stadium.get("races", {}).get(str(race_no))

    print("\n" + "=" * 60)
    print(f"場20・{race_no}R")

    if race is None:
        print("レースデータなし")
        return

    print("\n【レース名】")
    print(race.get("title"))

    print("\n【レース内のデータ項目】")
    print(list(race.keys()))

    print("\n【出走選手数】")
    print(len(race.get("racers") or {}))

    print("\n【展示情報】")
    preview = race.get("preview")
    if isinstance(preview, dict):
        print("取得あり")
        print("項目:", list(preview.keys()))
    else:
        print(preview)

    print("\n【オッズデータの構造】")
    odds = race.get("odds")

    print("oddsの型:", type(odds).__name__)

    if not isinstance(odds, dict):
        print("オッズデータ:", odds)
        return

    print("券種:", list(odds.keys()))

    for name, expected in EXPECTED.items():
        values = flatten(odds.get(name))

        valid = sum(
            isinstance(v, (int, float)) and v > 0
            for v in values
        )

        print(f"\n--- {name} ---")
        print(f"正常値: {valid}/{expected}")
        print(f"項目数: {len(values)}")
        print("先頭5件:", values[:5])
        print("元データ:")
        print(json.dumps(
            odds.get(name),
            ensure_ascii=False
        )[:700])


def main():
    response = requests.get(URL, timeout=30)
    response.raise_for_status()

    data = response.json()

    stadium = data["programs"]["stadiums"].get("20")

    if stadium is None:
        print("場20のデータがありません")
        return

    print("===== 正常レースと異常レースの比較 =====")
    print("比較日: 2026-05-03")

    inspect_race(stadium, 9)
    inspect_race(stadium, 10)
    inspect_race(stadium, 11)
    inspect_race(stadium, 12)


if __name__ == "__main__":
    main()
