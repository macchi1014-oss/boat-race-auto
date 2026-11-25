import requests
import csv
import io

DATE = "2026/05/03"

URLS = {
    "直前情報 tkz": f"https://boatracecsv.github.io/data/previews/tkz/{DATE}.csv",
    "3連単オッズ od3": f"https://boatracecsv.github.io/data/previews/od3/{DATE}.csv",
    "出走表 race_cards": f"https://boatracecsv.github.io/data/programs/race_cards/{DATE}.csv",
}


def main():
    success = 0

    for name, url in URLS.items():
        print(f"\n===== {name} =====")
        print(f"URL: {url}")

        try:
            response = requests.get(url, timeout=30)
            print(f"HTTP status: {response.status_code}")

            if response.status_code == 200:
                text = response.content.decode("utf-8-sig")
                reader = csv.DictReader(io.StringIO(text))
                headers = reader.fieldnames or []
                rows = list(reader)

                print(f"CSV列数: {len(headers)}")
                print(f"レース行数: {len(rows)}")
                print(f"先頭の列名: {headers[:10]}")

                if rows:
                    print(f"先頭行のレースコード: {rows[0].get('レースコード', '')}")

                success += 1
            else:
                print("取得できませんでした")

        except Exception as e:
            print(f"エラー: {e}")

    print(f"\n取得成功: {success} / 3")

    if success == 0:
        raise RuntimeError("3種類とも取得できませんでした")


if __name__ == "__main__":
    main()
