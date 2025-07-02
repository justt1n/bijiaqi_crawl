import json
import time
import pandas as pd

from typing import List, Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

import requests
from pydantic import BaseModel, Field

# ================== ĐỊNH NGHĨA MODEL ĐẦY ĐỦ ==================

class Server(BaseModel):
    """Model Server đầy đủ, map tất cả các trường từ JSON."""
    id: int
    parent_id: int = Field(alias='parentId')
    name: str
    leaf: bool
    type: str
    type_name: str = Field(alias='typeName')
    initial: str
    hot: bool
    sort: str
    # Các trường có thể là null được khai báo là Optional
    code: Optional[str] = None
    english_name: Optional[str] = Field(default=None, alias='englishName')
    unit: Optional[str] = None
    description: Optional[str] = None
    img_url: Optional[str] = Field(default=None, alias='imgUrl')

class Game(BaseModel):
    """Model Game đầy đủ, map tất cả các trường từ JSON."""
    id: int
    name: str
    leaf: bool
    type: str
    type_name: str = Field(alias='typeName')
    initial: str
    hot: bool
    sort: str
    code: str
    english_name: str = Field(alias='englishName')
    unit: str
    description: str
    img_url: Optional[str] = Field(default=None, alias='imgUrl')
    servers: List[Server] = []


class GameService:
    API_BASE_URL = "https://www.bijiaqi.com/api/v1/any/shop"
    HEADERS = {'Content-Type': 'application/json'}

    def __init__(self):
        self.games: List[Game] = []

    def _setup_mock_api_data(self) -> Dict[int, List[Dict[str, Any]]]:
        # Dữ liệu giả lập cho API
        return {
            560: [
                {"id": 37196, "parentId": 560, "name": "Doomhowl(Hardcore) - Alliance", "leaf": False, "type": "server", "typeName": "服务器", "initial": "D", "hot": False, "sort": "1940248948203720704", "code": None, "englishName": None, "unit": None, "description": None, "imgUrl": None},
                {"id": 37197, "parentId": 560, "name": "Doomhowl(Hardcore) - Horde", "leaf": False, "type": "server", "typeName": "服务器", "initial": "D", "hot": False, "sort": "1940248948203720705", "code": None, "englishName": None, "unit": None, "description": None, "imgUrl": None}
            ],
            561: [
                {"id": 40100, "parentId": 561, "name": "Silvermoon (EU) - Alliance", "leaf": False, "type": "server", "typeName": "服务器", "initial": "S", "hot": True, "sort": "2000000000000000001", "code": None, "englishName": None, "unit": None, "description": None, "imgUrl": None}
            ]
        }

    # def _fetch_servers_from_api(self, game_id: int) -> List[Dict[str, Any]]:
    #     print(f"▶️  Đang gọi API cho game ID: {game_id}...")
    #     time.sleep(0.5)
    #     servers_data = self._mock_api_data.get(game_id, [])
    #     print(f"✅  Nhận được {len(servers_data)} server.")
    #     return servers_data
    #
    # def join_game_with_servers(self):
    #     print("--- Bắt đầu quá trình kết hợp dữ liệu ---")
    #     for game in self.games:
    #         server_dicts = self._fetch_servers_from_api(game.id)
    #         game.servers = server_dicts # Pydantic tự động phân tích dữ liệu vào model Server đầy đủ
    #     print("--- Hoàn tất quá trình kết hợp ---\n")
    #

    def _fetch_games_from_api(self) -> List[Dict[str, Any]]:
        url = f"{self.API_BASE_URL}/home/games"
        print(f"Fetching games from API: {url}...")

        try:
            response = requests.post(url, headers=self.HEADERS, json={}, timeout=10)
            response.raise_for_status()
            games_data = response.json()
            print(f"Fetched {len(games_data)} games from API.")
            return games_data

        except requests.exceptions.RequestException as e:
            print(f"Error fetching games from API: {e}")
            return []


    def _fetch_servers_from_api(self, game_id: int) -> List[Dict[str, Any]]:
        @retry(
            wait=wait_fixed(2),  # Wait 2 seconds between retries
            stop=stop_after_attempt(5),  # Stop after 3 attempts
            retry=retry_if_exception_type(requests.exceptions.RequestException),  # Only retry on network/HTTP errors
            reraise=False  # Do not re-raise the exception after the last attempt
        )
        def _make_api_call() -> List[Dict[str, Any]]:
            url = f"{self.API_BASE_URL}/home/servers"
            payload = {"gameId": game_id}

            print(f"▶️  Calling API for servers of game ID {game_id} from: {url}...")

            response = requests.post(url, headers=self.HEADERS, json=payload, timeout=30)
            response.raise_for_status()

            servers_data = response.json()
            print(f"✅  Successfully retrieved {len(servers_data)} servers for game ID {game_id}.")
            return servers_data

        try:
            result = _make_api_call()
            return result if result is not None else []
        except Exception as e:
            print(f"❌  All retry attempts failed for game ID {game_id}: {e}")
            return []


    def join_game_with_servers(self):
        print("\n--- Starting process to join servers into games ---")
        if not self.games:
            print("No games found to process.")
            return
        for game in self.games:
            server_dicts = self._fetch_servers_from_api(game.id)
            time.sleep(0.5)  # Giả lập độ trễ để tránh quá tải API
            game.servers = server_dicts
        print("--- Finished joining process ---\n")

    def get_final_result(self) -> List[Dict[str, Any]]:
        return [game.model_dump(by_alias=True) for game in self.games]


if __name__ == "__main__":

    game_service = GameService()

    game_list = game_service._fetch_games_from_api()
    if not game_list:
        print("No games found. Exiting.")
        exit(1)
    print(f"Found {len(game_list)} games. Processing...")

    for game_data in game_list:
        # Sử dụng Pydantic để tạo model Game đầy đủ
        game = Game.model_validate(game_data)
        game_service.games.append(game)

    print(f"Loaded {len(game_service.games)} games into service.")

    # Bây giờ chúng ta sẽ gọi API để lấy danh sách server cho từng game
    # và kết hợp chúng vào model Game đầy đủ
    game_service.join_game_with_servers()
    final_result_data = game_service.get_final_result()
    if not final_result_data:
        print("No data to process for CSV export.")
        exit()

    print("--- Flattening data for CSV export ---")

    # --- Start of Flattening Logic ---
    flattened_data = []
    for game in final_result_data:
        # Check if there are servers for this game
        if game.get('servers'):
            for server in game['servers']:
                # Create a new record for each server
                record = {}

                # Copy game data into the record
                for key, value in game.items():
                    if key != 'servers':  # Exclude the nested server list
                        record[key] = value

                # Add server data into the record, prefixing keys to avoid conflicts
                for server_key, server_value in server.items():
                    record[f"server_{server_key}"] = server_value

                flattened_data.append(record)
        else:
            # If a game has no servers, add it as a single row
            record = {}
            for key, value in game.items():
                if key != 'servers':
                    record[key] = value
            flattened_data.append(record)
    # --- End of Flattening Logic ---

    # Create DataFrame from the new flattened list
    if flattened_data:
        df = pd.DataFrame(flattened_data)

        # Define the desired column order
        jkljkl

        game_cols = [c for c in df.columns if not c.startswith('server_')]
        server_cols = sorted([c for c in df.columns if c.startswith('server_')])
        df = df[game_cols + server_cols]

        output_filename = 'bij_client_games_flattened.csv'
        df.to_csv(output_filename, index=False, encoding='utf-8-sig')
        print(f"✅  Successfully exported flattened data to {output_filename}")
    else:
        print("⚠️  No data available to create a DataFrame.")
