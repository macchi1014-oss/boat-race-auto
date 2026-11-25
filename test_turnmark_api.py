import requests

URL = "https://turnmark.github.io/api/v1/2026/20260501.json"


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

    total_races = 0
    complete_races = 0
    incomplete_races = 0
    missing_races = 0

    print("===== 1日分・全レースの3連単調査 =====")

    for stadium_no, stadium in stadiums.items():
        for race_no, race in stadium.get("races", {}).items():

            total_races += 1

            odds = race.get("odds") or {}
            values = inspect(odds.get("trifecta"))

            valid = sum(
                isinstance(v, (int, float)) and v > 0
                for v in values
            )

            nulls = sum(v is None for v in values)

            invalid = sum(
                not isinstance(v, (int, float)) and v is not None
                for v in values
            )

            if valid == 120:
                complete_races += 1
            else:
                incomplete_races += 1

                if valid == 0:
                    missing_races += 1

                print(
                    f"\n場 {stadium_no}・{race_no}R"
                )
                print(f"レース名: {race.get('title')}")
                print(
                    f"正常値: {valid} / "
                    f"null: {nulls} / "
                    f"異常値: {invalid} / "
                    f"項目数: {len(values)}"
                )

    print("\n===== 全体集計 =====")
    print(f"対象レース数: {total_races}")
    print(f"120通り取得: {complete_races}")
    print(f"120通り未満: {incomplete_races}")
    print(f"正常値0件: {missing_races}")


if __name__ == "__main__":
    main()
