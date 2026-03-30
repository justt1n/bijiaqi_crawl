import csv
import os
import time
import pandas as pd

from typing import List, Dict, Any, Optional

from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

import requests
from pydantic import BaseModel, Field, field_validator, ConfigDict, ValidationInfo


# ================== ĐỊNH NGHĨA MODEL ĐẦY ĐỦ ==================


def normalize_merchant_name(value: Optional[str]) -> str:
    if not value:
        return ""
    return " ".join(value.strip().lower().split())


class FlexibleBaseModel(BaseModel):
    """
    A custom base model with a flexible configuration that:
    - Ignores extra fields from the API.
    - Automatically converts None to "" for string fields.
    """
    model_config = ConfigDict(
        extra='ignore',  # Ignore fields not defined in the model
        populate_by_name=True,  # Allow using aliases
    )

    @field_validator('*', mode='before')
    @classmethod
    def none_to_empty_str(cls, v: Any, info: ValidationInfo) -> Any:
        """If a field should be a string and the value is None, convert it to ""."""
        field_info = cls.model_fields.get(info.field_name)
        if field_info:
            is_string_field = field_info.annotation is str or \
                              str in getattr(field_info.annotation, '__args__', ())
            if is_string_field and v is None:
                return ""  # Convert None to empty string
        return v


class Server(FlexibleBaseModel):
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


class Merchant(FlexibleBaseModel):
    """Model cho đối tượng 'merchant' lồng bên trong."""
    id: str
    user_id: str = Field(alias='userId')
    store_name: str = Field(alias='storeName')
    order_completion_rate: float = Field(alias='orderCompletionRate')
    order_settlement_of_second: int = Field(alias='orderSettlementOfSecond')
    online: bool
    created_at: str = Field(alias='createdAt')


class ShopDemand(FlexibleBaseModel):
    """Model cho một 'mặt hàng' trong danh sách 'list' (all attributes optional)."""
    id: Optional[str] = None
    title: Optional[str] = None
    price: Optional[float] = None
    sum_quantity: Optional[int] = Field(default=None, alias='sumQuantity')
    min_quantity: Optional[int] = Field(default=None, alias='minQuantity')
    stock_quantity: Optional[int] = Field(default=None, alias='stockQuantity')
    effective_quantity: Optional[int] = Field(default=None, alias='effectiveQuantity')
    unit: Optional[str] = None
    delivery_method_label: Optional[str] = Field(default=None, alias='deliveryMethodLabel')
    delivery_speed_of_second: Optional[int] = Field(default=None, alias='deliverySpeedOfSecond')
    avg_delivery_speed_of_second: Optional[int] = Field(default=None, alias='avgDeliverySpeedOfSecond')
    guaranteed: Optional[bool] = None
    deposit: Optional[str] = None
    game_code: Optional[str] = Field(default=None, alias='gameCode')
    game_name: Optional[str] = Field(default=None, alias='gameName')
    attr_name_indexes: Optional[str] = Field(default=None, alias='attrNameIndexes')
    created_at: Optional[str] = Field(default=None, alias='createdAt')
    merchant: Optional[Merchant] = None



class PageInfo(FlexibleBaseModel):
    """Model for nested pageInfo object in API response."""
    current_page: int = Field(alias='currentPage')
    page_size: int = Field(alias='pageSize')
    total: Optional[int] = None


class ShopDemandResponse(FlexibleBaseModel):
    """Model tổng thể cho toàn bộ JSON response."""
    current_page: int = Field(alias='currentPage')
    page_size: int = Field(alias='pageSize')
    list: List[ShopDemand]  # Một danh sách các đối tượng ShopDemand
    page_info: Optional[PageInfo] = Field(default=None, alias='pageInfo')  # New nested pageInfo object


class ItemToSheet(FlexibleBaseModel):
    name: str
    price: float
    min_quantity: Optional[int]
    max_quantity: Optional[int]
    deposit: Optional[str]
    delivery_time: Optional[str]
    delivery_method: Optional[str]

    @classmethod
    def from_shop_demand(cls, demand: ShopDemand):
        if not demand:
            return None

        def convert_second_to_hour(seconds: int) -> int:
            if not isinstance(seconds, int) or seconds < 0:
                return 0
            return max(1, seconds // 3600)

        settlement_seconds = None
        if demand.merchant and demand.merchant.order_settlement_of_second is not None:
            settlement_seconds = demand.merchant.order_settlement_of_second
        elif demand.delivery_speed_of_second is not None:
            settlement_seconds = demand.delivery_speed_of_second

        max_quantity = demand.sum_quantity
        if max_quantity is None:
            max_quantity = demand.stock_quantity
        if max_quantity is None:
            max_quantity = demand.effective_quantity

        data_to_validate = {
            "name": demand.merchant.store_name,
            "price": demand.price,
            "min_quantity": demand.min_quantity if demand.min_quantity is not None else 1,
            "max_quantity": max_quantity,
            "deposit": demand.deposit,
            "delivery_method": demand.delivery_method_label,
            "delivery_time": f"{convert_second_to_hour(settlement_seconds)}时" if settlement_seconds is not None else None,
        }
        return cls.model_validate(data_to_validate)



class GameService:
    API_BASE_URL = "https://www.bijiaqi.com/api/v1/any/shop"
    HEADERS = {
        'Content-Type': 'application/json',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Origin': 'https://www.bijiaqi.com',
        'Referer': 'https://www.bijiaqi.com/',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36'
    }

    def __init__(self):
        self.games: List[Game] = []

    def _setup_mock_api_data(self) -> Dict[int, List[Dict[str, Any]]]:
        # Dữ liệu giả lập cho API
        return {
            560: [
                {"id": 37196, "parentId": 560, "name": "Doomhowl(Hardcore) - Alliance", "leaf": False,
                 "type": "server",
                 "typeName": "服务器", "initial": "D", "hot": False, "sort": "1940248948203720704",
                 "code": None,
                 "englishName": None, "unit": None, "description": None, "imgUrl": None},
                {"id": 37197, "parentId": 560, "name": "Doomhowl(Hardcore) - Horde", "leaf": False,
                 "type": "server",
                 "typeName": "服务器", "initial": "D", "hot": False, "sort": "1940248948203720705",
                 "code": None,
                 "englishName": None, "unit": None, "description": None, "imgUrl": None}
            ],
            561: [
                {"id": 40100, "parentId": 561, "name": "Silvermoon (EU) - Alliance", "leaf": False,
                 "type": "server",
                 "typeName": "服务器", "initial": "S", "hot": True, "sort": "2000000000000000001", "code": None,
                 "englishName": None, "unit": None, "description": None, "imgUrl": None}
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

            print(f"Calling API for servers of game ID {game_id} from: {url}...")

            response = requests.post(url, headers=self.HEADERS, json=payload, timeout=30)
            response.raise_for_status()

            servers_data = response.json()
            print(f"Successfully retrieved {len(servers_data)} servers for game ID {game_id}.")
            return servers_data

        try:
            result = _make_api_call()
            return result if result is not None else []
        except Exception as e:
            print(f"ERROR: All retry attempts failed for game ID {game_id}: {e}")
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

    @retry(
        wait=wait_fixed(5),  # Wait 2 seconds between each retry
        stop=stop_after_attempt(5),  # Stop after 3 attempts in total
        retry=retry_if_exception_type(requests.exceptions.RequestException),
        # Only retry on network/HTTP errors
        reraise=False  # Do not re-raise the exception after the last attempt fails
    )
    def fetch_shop_demand(self, game_id: int, server_id: int) -> Optional['ShopDemandResponse']:
        url = "https://www.bijiaqi.com/api/shop/commodity/listShopCommodity"
        payload = {
            "isQueryTotal": False,
            "categoryId": int(os.getenv("CATEGORY_ID", "3")),
            "gameId": game_id,
            "attrIdIndexes": str(server_id),
            "loginUserId": "",
            "limit": 15
        }

        # print(f"Calling API for shop demand for game {game_id}, server {server_id}...")

        try:
            response = requests.post(url, headers=self.HEADERS, json=payload, timeout=10)

            # This will trigger a retry if the status code is 4xx or 5xx
            response.raise_for_status()

            response_data = response.json()
            validated_response = ShopDemandResponse.model_validate(response_data)

            # print(f"Successfully fetched shop demand for game {game_id}.")
            return validated_response

        except requests.exceptions.RequestException as e:
            print(f"API call failed: {e}. Retrying if possible...")
            raise

        except Exception as e:
            # Catch other errors (like Pydantic validation) that should NOT be retried.
            print(f"Error processing shop demand data: {e}")
            return None


def load_server_map_from_csv(filepath: str) -> dict:
    server_map = {}
    try:
        with open(filepath, mode='r', encoding='utf-8') as infile:
            reader = csv.reader(infile)
            next(reader)  # Bỏ qua dòng tiêu đề (header)
            for row in reader:
                if len(row) >= 2:
                    try:
                        # Check if both values are non-empty
                        if not row[0].strip() or not row[1].strip():
                            print(f"Ignoring row with empty values: {row}")
                            continue
                        game_id = int(row[0])
                        server_id = int(row[1])
                        server_map[server_id] = game_id
                    except ValueError:
                        print(f"Ignoring malformed row (not valid numbers): game_id='{row[0]}', server_id='{row[1]}'")
    except FileNotFoundError:
        print(f"Can't find {filepath}.")
        return {}
    return server_map


def find_game_id(server_map: dict, server_id_to_find: int) -> int | None:
    if not server_map:
        return None
    return server_map.get(server_id_to_find)


def crawl_server_data():
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
        game_cols = [c for c in df.columns if not c.startswith('server_')]
        server_cols = sorted([c for c in df.columns if c.startswith('server_')])
        df = df[game_cols + server_cols]

        output_filename = 'bij_client_games_flattened.csv'
        df.to_csv(output_filename, index=False, encoding='utf-8-sig')
        print(f"Successfully exported flattened data to {output_filename}")
    else:
        print("WARNING: No data available to create a DataFrame.")


def get_price_list(server_map: dict, server_id: int) -> list[ShopDemand] | None:
    game_service = GameService()

    game_id = find_game_id(server_map, server_id)
    if not game_id:
        print(f"Could not find a gameId for server_id: {server_id}")
        return None

    response = game_service.fetch_shop_demand(game_id, server_id)
    if not response or not response.list:
        print(f"No items found for game {game_id}, server {server_id}.")
        return None

    print(f"Fetched {len(response.list)} commodity items for game {game_id}, server {server_id}.")
    return response.list


def get_the_max_price(
        items: List['ShopDemand'],
        delivery_types,  # Can be str or list
        min_qty: int,
        max_qty: int,
        black_list = None
) -> Optional['ShopDemand']:
    if not items:
        print(f"WARNING: No items provided to filter")
        return None

    print(f"Filtering {len(items)} items with:")
    print(f"   min_qty={min_qty} (items must require AT MOST this for minimum order)")
    print(f"   max_qty={max_qty} (items must have AT LEAST this quantity available)")
    print(f"   delivery_types={delivery_types} (type: {type(delivery_types).__name__})")

    # Handle both string and list inputs
    if isinstance(delivery_types, str):
        allowed_delivery_methods = {method.strip() for method in delivery_types.split(',')}
    elif isinstance(delivery_types, list):
        allowed_delivery_methods = {method.strip() for method in delivery_types}
    else:
        allowed_delivery_methods = set(delivery_types)

    print(f"Allowed delivery methods: {allowed_delivery_methods}")
    normalized_blacklist = {
        normalize_merchant_name(name) for name in (black_list or []) if normalize_merchant_name(name)
    }
    if normalized_blacklist:
        print(f"Loaded {len(normalized_blacklist)} blacklist entries")

    # Use a generator expression for memory-efficient filtering
    filtered_items = []

    # 2. Loop through all items to filter them
    for idx, item in enumerate(items):
        # Debug first few items
        if idx < 3:
            print(f"\nItem {idx+1}:")
            print(f"   min_quantity={item.min_quantity}, stock_quantity={item.stock_quantity}, effective_quantity={item.effective_quantity}")
            print(f"   delivery={item.delivery_method_label}, price={item.price}")
            print(f"   store={item.merchant.store_name if item.merchant else 'N/A'}")

        # Check each condition
        item_min_quantity = item.min_quantity if item.min_quantity is not None else 1
        item_available_quantity = item.effective_quantity
        if item_available_quantity is None:
            item_available_quantity = item.stock_quantity
        if item_available_quantity is None:
            item_available_quantity = item.sum_quantity

        min_check = item_min_quantity <= min_qty
        qty_check = item_available_quantity is not None and item_available_quantity >= max_qty
        delivery_check = item.delivery_method_label in allowed_delivery_methods

        if idx < 3:
            print(f"   [CHECK] min_quantity ({item_min_quantity}) <= {min_qty}? {min_check}")
            print(f"   [CHECK] available_quantity ({item_available_quantity}) >= {max_qty}? {qty_check}")
            print(f"   [CHECK] delivery_method in allowed? {delivery_check}")

        # 3. Check if the item matches all conditions
        # Logic: Find items where:
        # - Item's minimum order requirement is LESS than or equal to what user can buy
        # - Item has ENOUGH quantity available (at least what user wants)
        # - Delivery method matches
        if (min_check and qty_check and delivery_check):
            # Check blacklist
            merchant_name = item.merchant.store_name if item.merchant else ""
            normalized_merchant_name = normalize_merchant_name(merchant_name)
            if normalized_blacklist and normalized_merchant_name in normalized_blacklist:
                if idx < 3:
                    print(f"   [BLACKLISTED]: {merchant_name}")
                else:
                    print(f"   [BLACKLISTED]: {merchant_name}")
                continue

            print(f"[MATCH #{len(filtered_items)+1}] price={item.price}, min={item_min_quantity}, effective={item_available_quantity}, store={item.merchant.store_name if item.merchant else 'N/A'}")
            filtered_items.append(item)
        elif idx < 3:
            print(f"   [REJECTED]")

    print(f"Filtered to {len(filtered_items)} matching items")

    try:
        # The min() function will raise a ValueError if filtered_items is empty
        result = max(filtered_items, key=lambda item: item.price)
        print(f"Found max price item: {result.price} from {result.merchant.store_name if result.merchant else 'N/A'}")
        return result
    except ValueError as e:
        print(f"ERROR: No items matched the filter criteria")
        return None



if __name__ == "__main__":
    # use crawl_server_data
    crawl_server_data()
