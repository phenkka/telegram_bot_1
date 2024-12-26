import requests
import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="dexscreener.log",
    filemode="a"
)

def fetch_token_data(address, max_retries=5, retry_delay=1):
    for attempt in range(max_retries):
        try:
            url = f"https://api.dexscreener.com/latest/dex/tokens/{address}"
            logging.info(f"Requesting data for token: {address}, Attempt: {attempt + 1}")

            response = requests.get(url)

            logging.info(f"Sent GET request: {url}")

            if response.status_code != 200:
                logging.error(
                    f"HTTP Error {response.status_code}: {response.reason}. Response body: {response.text}"
                )
                raise requests.RequestException(f"API Error: {response.status_code} {response.reason}")

            token_data = response.json()

            if "pairs" in token_data and token_data["pairs"]:
                pair = token_data["pairs"][0]
                base_token = pair.get("baseToken", {})
                market_cap = pair.get("marketCap", "Не указано")

                address = base_token.get("address", "Не указано")
                symbol = base_token.get("symbol", "Не указано")

                logging.info(f"Success on attempt {attempt + 1}: Symbol: {symbol}, Market Cap: {market_cap}")
                return symbol, str(market_cap)
            else:
                logging.warning(f"No pairs data found. Retrying... Attempt: {attempt + 1}")
                time.sleep(retry_delay)
        except Exception as e:
            logging.error(f"Attempt {attempt + 1}: Error while fetching data: {e}")
            time.sleep(retry_delay)

    raise ValueError("Failed to fetch token data after all retries.")

# Пример вызова
# if __name__ == "__main__":
#     try:
#         symbol, market_cap = fetch_token_data("FaefVP4DsPrudsbhVTThVqLckaSvqj175CsMPifhib2d")
#         print(f"Token Symbol: {symbol}, Market Cap: {market_cap}")
#     except ValueError as e:
#         logging.critical(f"Final failure: {e}")
#         print(e)
