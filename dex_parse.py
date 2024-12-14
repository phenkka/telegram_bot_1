WALLET_ADDRESS = "83z64mKGwjWecJmekE696rJYAHRYEPemMox6dg4Ypump"

import requests
import time

def fetch_token_data(address, max_retries=5, retry_delay=1):
    for attempt in range(max_retries):
        try:
            url = f"https://api.dexscreener.com/latest/dex/tokens/{address}"
            response = requests.get(url)

            if response.status_code != 200:
                raise requests.RequestException(f"Ошибка API: {response.status_code} {response.reason}")

            token_data = response.json()

            if "pairs" in token_data and token_data["pairs"]:
                pair = token_data["pairs"][0]
                base_token = pair.get("baseToken", {})
                market_cap = pair.get("marketCap", "Не указано")

                address = base_token.get("address", "Не указано")
                symbol = base_token.get("symbol", "Не указано")

                print(f"Трай {attempt + 1}: Успех")
                print(address, symbol, str(market_cap))
                return symbol, str(market_cap)
            else:
                print(f"Трай {attempt + 1}: Ретрай")
                time.sleep(retry_delay)
        except Exception as e:
            print(f"Попытка {attempt + 1}: Ошибка при получении данных: {e}")
            time.sleep(retry_delay)

    raise ValueError("Не удалось получить данные о парах после всех попыток.")

try:
    print(fetch_token_data(WALLET_ADDRESS))
except ValueError as e:
    print(f"Финальная ошибка: {e}")
