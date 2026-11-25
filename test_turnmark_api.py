
import requests

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

NAMES = {
    "trifecta": "3連単",
    "trio": "3連複",
    "exacta": "2連単",
    "quinella": "2連複",
    "quinella_place": "拡連複",
    "win": "単勝",
    "place": "複勝",
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


def count_valid(values):
    return sum(
        isinstance(v, (int, float)) and v > 0
        for v in values
    )


def main():
    response = requests.get(URL, timeout=30)
    response.raise_for_status()

    data = response.json()
    stadiums = data["programs"]["stadiums"]

    totals = {
        name: {"valid": 0, "items": 0, "complete": 0, "races": 0}
        for name in EXPECTED
    }

    missing = {name: [] for name in EXPECTED}
    race_count = 0

    print("===== 2026年5月3日 券種別欠損調査 =====")

    for stadium_no, stadium in stadiums.items():
        for race_no, race in stadium.get("races", {}).items():
            race_count += 1
            odds = race.get("odds") or {}

            for name, expected in EXPECTED.items():
                values = flatten(odds.get(name))
                valid = count_valid(values)

                totals[name]["valid"] += valid
                totals[name]["items"] += len(values)
                totals[name]["races"] += 1

                if valid == expected:
                    totals[name]["complete"] += 1
                else:
                    missing[name].append({
                        "stadium": stadium_no,
                        "race": race_no,
                        "title": race.get("title"),
                        "valid": valid,
                        "items": len(values),
                        "expected": expected,
                    })

    print(f"\n対象レース数: {race_count}")

    print("\n===== 券種別の欠損レース一覧 =====")

    for name, records in missing.items():
        print(f"\n【{NAMES[name]}】")

        if not records:
            print("欠損なし")
            continue

        for item in records:
            print(
                f"場{item['stadium']}・{item['race']}R "
                f"{item['title']} "
                f"正常値 {item['valid']} / {item['expected']} "
                f"（項目数 {item['items']}）"
            )

    print("\n===== 券種別の全体集計 =====")

    for name, result in totals.items():
        print(
            f"{NAMES[name]}: "
            f"{result['valid']} / {result['items']} 正常値、"
            f"{result['complete']} / {result['races']} レースで"
            f"基準通り取得、"
            f"欠損レース {len(missing[name])}"
        )


if __name__ == "__main__":
    main()
