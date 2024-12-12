# WALLET_ADDRESS = "ABAGcLC6hoapG3xFcBkwaXzmdFzdH7nup2JD1feapump"

import requests

def fetch_token_data(address):
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

            print(address, symbol, str(market_cap))
            return symbol, str(market_cap)

            # return {
            #     "name": name,
            #     "symbol": symbol,
            #     "address": address,
            #     "marke_tCap": market_cap
            # }
        else:
            raise ValueError("Данные о парах не найдены в ответе API.")
    except Exception as e:
        print(f"Ошибка при получении данных: {e}")
        raise

# print(fetch_token_data(WALLET_ADDRESS))