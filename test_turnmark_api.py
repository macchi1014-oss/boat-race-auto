import requests
from itertools import permutations

URL = "https://turnmark.github.io/api/v1/2026/20260501.json"


def main():
    response = requests.get(URL, timeout=30)
    print(f"HTTP status: {response.status_code}")
    response.raise_for_status()

    data = response.json()
    stadiums = data["programs"]["stadiums"]

    print("\n===== 120通り未満のレース調査 =====")

    checked = 0

    for stadium_no, stadium in stadiums.items():
        for race_no, race in stadium.get("races", {}).items():

            trifecta = (race.get("odds") or {}).get("trifecta") or {}

            values = []

            for first, second_group in trifecta.items():
                for second, third_group in second_group.items():
                    for third, value in third_group.items():
                        values.append(value)

            if len(values) == 120 and all(
                isinstance(v, (int, float)) and v > 0
                for v in values
            ):
                continue

            checked += 1

            result = race.get("result") or {}
            result_racers = result.get("racers") or {}

            absent = []

            for boat_no, racer in result_racers.items():
                if racer.get("place_number") in (14, 15, 16):
                    absent.append(str(boat_no))

            refunds = result.get("refunds") or []

            null_count = sum(v is None for v in values)
            valid_count = sum(
                isinstance(v, (int, float)) and v > 0
                for v in values
            )

            active_boats = [
                str(i) for i in range(1, 7)
                if str(i) not in absent
            ]

            expected = len(list(permutations(active_boats, 3)))

            print(f"\n場 {stadium_no}・{race_no}R")
            print(f"オッズ項目数: {len(values)}")
            print(f"正常なオッズ数: {valid_count}")
            print(f"nullの数: {null_count}")
            print(f"欠場判定の艇: {absent}")
            print(f"返還艇: {refunds}")
            print(f"欠場を除いた想定組み合わせ数: {expected}")

    print(f"\n調査対象レース数: {checked}")


if __name__ == "__main__":
    main()
