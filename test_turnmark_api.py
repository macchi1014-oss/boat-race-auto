import requests

URL = "https://turnmark.github.io/api/v1/2026/20260501.json"

def main():
    print("Turnmark API 接続テスト")
    print(f"取得URL: {URL}")

    response = requests.get(URL, timeout=30)
    print(f"HTTP status: {response.status_code}")

    response.raise_for_status()

    data = response.json()

    stadiums = data.get("programs", {}).get("stadiums", {})
    print(f"取得したレース場数: {len(stadiums)}")

    odds_count = 0

    for stadium_no, stadium in stadiums.items():
        races = stadium.get("races", {})

        for race_no, race in races.items():
            odds = race.get("odds") or {}
            trifecta = odds.get("trifecta") or {}

            if trifecta:
                odds_count += 1

                if odds_count == 1:
                    print(f"サンプル: レース場 {stadium_no}")
                    print(f"レース番号: {race_no}")
                    print("3連単オッズの一部:")

                    for first, second_group in trifecta.items():
                        for second, third_group in second_group.items():
                            for third, value in third_group.items():
                                print(
                                    f"{first}-{second}-{third}: {value}"
                                )
                                break
                            break
                        break

    print(f"3連単オッズ取得レース数: {odds_count}")

    if odds_count > 0:
        print("判定: 3連単オッズ取得成功")
    else:
        print("判定: データは取得できたが、3連単オッズが見つかりません")

if __name__ == "__main__":
    main()
