
import requests

URLS = {
    "公式サイト": "https://boatracecsv.github.io/",
    "公式GitHub": "https://github.com/BoatraceCSV/boatracecsv.github.io",
    "公式データ説明書": "https://raw.githubusercontent.com/BoatraceCSV/boatracecsv.github.io/main/docs/data/README.md",
    "公式CSVサンプル": "https://boatracecsv.github.io/data/results/realtime/2026/05/06.csv",
}

def main():
    success = 0

    for name, url in URLS.items():
        print(f"\n===== {name} =====")
        print(f"確認URL: {url}")

        try:
            response = requests.get(
                url,
                timeout=30,
                headers={"User-Agent": "Mozilla/5.0"}
            )

            print(f"HTTP status: {response.status_code}")
            print(f"最終URL: {response.url}")
            print(f"Content-Type: {response.headers.get('Content-Type', '')}")
            print(f"受信サイズ: {len(response.content)} bytes")

            if response.status_code == 200:
                print("判定: 接続成功")
                print(response.text[:200])
                success += 1
            else:
                print("判定: 接続先からエラー応答")

        except Exception as e:
            print(f"通信エラー: {e}")

    print(f"\n接続成功: {success} / 4")

if __name__ == "__main__":
    main()
