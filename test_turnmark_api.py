import requests
from numbers import Number

URL = "https://turnmark.github.io/api/v1/2026/20260501.json"


def collect_values(data):
    values = []

    if isinstance(data, dict):
        for value in data.values():
            values.extend(collect_values(value))

    elif isinstance(data, (int, float)):
        values.append(data)

    elif isinstance(data, str):
        try:
            values.append(float(data))
        except ValueError:
            pass

    return values


def main():
    print("Turnmark API 3連単オッズ詳細テスト")

    response = requests.get(URL, timeout=30)
    print(f"HTTP status: {response.status_code}")
    response.raise_for_status()

    data = response.json()
    stadiums = data.get("programs", {}).get("stadiums", {})

    total_races = 0
    complete_races = 0
    incomplete_races = 0
    invalid_races = 0

    for stadium_no, stadium in stadiums.items():
        for race_no, race in stadium.get("races", {}).items():
            trifecta = (race.get("odds") or {}).get("trifecta")

            if not trifecta:
                continue

            total_races += 1
            values = collect_values(trifecta)

            if len(values) == 120:
                complete_races += 1
            else:
                incomplete_races += 1

            if len(values) != 120 or any(
                value <= 0 for value in values
            ):
                invalid_races += 1

            if total_races <= 5:
                print(
                    f"場 {stadium_no}・{race_no}R: "
                    f"{len(values)}通り"
                )

    print("\n===== 集計結果 =====")
    print(f"対象レース数: {total_races}")
    print(f"120通り揃ったレース: {complete_races}")
    print(f"120通り揃わなかったレース: {incomplete_races}")
    print(f"欠損・異常値のあるレース: {invalid_races}")


if __name__ == "__main__":
    main()
