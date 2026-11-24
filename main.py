
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

DATA_DIR = "data"
CHECK_FILE = os.path.join(DATA_DIR, "source_check.txt")

API_URL = "https://boatraceopenapi.github.io/api/v1/today.json"


def fetch_race_data():
    os.makedirs(DATA_DIR, exist_ok=True)

    today = datetime.now(
        ZoneInfo("Asia/Tokyo")
    ).strftime("%Y%m%d")

    print("レースデータを取得しています...")

    response = requests.get(
        API_URL,
        timeout=30,
        headers={"User-Agent": "BoatRaceAuto/1.0"}
    )

    response.raise_for_status()

    data = response.json()

    if not isinstance(data, dict):
        raise ValueError("JSONの形式が正しくありません")

    programs = data.get("programs", {})
    stadiums = programs.get("stadiums", {})

    if not isinstance(stadiums, dict):
        raise ValueError("レース場データが見つかりません")

    race_count = 0

    for stadium in stadiums.values():
        races = stadium.get("races", {})
        race_count += len(races)

    file_path = os.path.join(
        DATA_DIR,
        f"{today}.json"
    )

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )

    message = (
        "レースデータ取得成功\n"
        f"取得日: {today}\n"
        f"レース場数: {len(stadiums)}\n"
        f"レース数: {race_count}\n"
        f"保存先: {file_path}\n"
    )

    with open(
        CHECK_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        f.write(message)

    print(message)


if __name__ == "__main__":
    fetch_race_data()
