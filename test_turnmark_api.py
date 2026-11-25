
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

    race_count = 0
    trifecta_complete = 0
    trifecta_zero = 0
    trifecta_partial = 0

    print("===== 2026年5月3日 全レースオッズ集計 =====")

    for stadium_no, stadium in stadiums.items():
        for race_no, race in stadium.get("races", {}).items():
            race_count += 1
            odds = race.get("odds") or {}

            race_valid = {}

            for name, expected in EXPECTED.items():
                values = flatten(odds.get(name))
                valid = count_valid(values)

                totals[name]["valid"] += valid
                totals[name]["items"] += len(values)
                totals[name]["races"] += 1

                if valid == expected:
                    totals[name]["complete"] += 1

                race_valid[name] = valid

            trifecta = race_valid["trifecta"]

            if trifecta == EXPECTED["trifecta"]:
                trifecta_complete += 1
            elif trifecta == 0:
                trifecta_zero += 1
            else:
                trifecta_partial += 1

            if trifecta != EXPECTED["trifecta"]:
                print(
                    f"欠損: 場{stadium_no}・{race_no}R "
                    f"{race.get('title')} "
                    f"3連単 {trifecta}/120"
                )

    print("\n===== 全体集計 =====")
    print(f"対象レース数: {race_count}")
    print(f"3連単120通り正常: {trifecta_complete}")
    print(f"3連単全欠損: {trifecta_zero}")
    print(f"3連単一部欠損: {trifecta_partial}")

    print("\n===== 券種別集計 =====")

    for name, result in totals.items():
        print(
            f"{name}: "
            f"{result['valid']} / {result['items']} "
            f"正常値、"
            f"{result['complete']} / {result['races']} レースで"
            f"基準通り取得"
        )


if __name__ == "__main__":
    main()
