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

    targets = {
        ("9", "8"), ("9", "9"), ("9", "10"),
        ("9", "11"), ("9", "12"),
        ("11", "10"), ("11", "11"), ("11", "12")
    }

    print("===== 残り8レースの詳細調査 =====")

    for stadium_no, stadium in stadiums.items():
        for race_no, race in stadium.get("races", {}).items():

            if (stadium_no, race_no) not in targets:
                continue

            odds = race.get("odds") or {}

            print(f"\n場 {stadium_no}・{race_no}R")
            print(f"レース名: {race.get('title')}")
            print(f"締切時刻: {race.get('closed_at')}")

            for bet_type in [
                "trifecta",
                "trio",
                "exacta",
                "quinella",
                "quinella_place",
                "win",
                "place"
            ]:
                values = inspect(odds.get(bet_type))

                valid = sum(
                    isinstance(v, (int, float)) and v > 0
                    for v in values
                )

                nulls = sum(v is None for v in values)

                print(
                    f"{bet_type}: "
                    f"正常値 {valid} / null {nulls} / "
                    f"項目数 {len(values)}"
                )


if __name__ == "__main__":
    main()
