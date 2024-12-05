import requests
import time
from db.database import Database
import app.config as cfg

# Адрес RPC для получения токенов на кошельке
RPC_URL = "https://api.mainnet-beta.solana.com"


def get_token_accounts(wallet_address):
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTokenAccountsByOwner",
        "params": [
            wallet_address,
            {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
            {"encoding": "jsonParsed"}
        ]
    }

    try:
        response = requests.post(RPC_URL, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        if response.status_code == 200:
            data = response.json()
            if 'result' in data and 'value' in data['result']:
                accounts = data['result']['value']
                filtered_accounts = [
                    account for account in accounts
                    if account['account']['data']['parsed']['info']['tokenAmount']['uiAmount'] > 0.01
                ]
                return filtered_accounts
        else:
            print(f"Ошибка: {response.status_code}, {response.text}")
            return []
    except requests.exceptions.Timeout:
        print(f"Тайм-аут при запросе данных о токенах для кошелька {wallet_address}.")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе данных о токенах для кошелька {wallet_address}: {e}")
    return []


def get_token_info(token_address):
    url = f"https://api.dexscreener.com/latest/dex/search?q={token_address}"

    try:
        response = requests.get(url, timeout=2)
        response.raise_for_status()
        if response.status_code == 200:
            data = response.json()
            if "pairs" in data:
                for pair in data["pairs"]:
                    if pair['baseToken']['address'] == token_address or pair['quoteToken']['address'] == token_address:
                        token_name = pair['baseToken']['name'] if pair['baseToken']['address'] == token_address else pair['quoteToken']['name']
                        token_price_in_sol = float(pair['priceNative']) if pair['baseToken']['symbol'] == "SOL" or pair['quoteToken']['symbol'] == "SOL" else None
                        return token_name, token_price_in_sol
    except requests.exceptions.Timeout:
        print(f"Тайм-аут при запросе данных о токене {token_address}.")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе данных о токене {token_address}: {e}")
    return "Неизвестно", None

def process_wallets(db):
    wallets = db.get_wallets()

    for wallet in reversed(wallets):
        print(f"\nОбрабатываю кошелек: {wallet}")
        accounts = get_token_accounts(wallet)

        if accounts:
            try:
                print(f"Найдено {len(accounts)} токенов для кошелька {wallet}:\n")
                existing_tokens = db.get_tokens_for_wallet(wallet)
                updated_tokens = set()

                for account in accounts:
                    token_info = account['account']['data']['parsed']['info']
                    token_address = token_info['mint']
                    token_balance = token_info['tokenAmount']['uiAmount']
                    token_name, token_price_in_sol = get_token_info(token_address)

                    if token_price_in_sol is None:
                        continue

                    total_in_sol = round(token_balance * token_price_in_sol, 4)

                    if total_in_sol > 0.01:
                        print(f"Токен: {token_name} (Адрес: {token_address}), Сумма в SOL: {total_in_sol:.4f}")

                        if token_address in existing_tokens:
                            db.update_token_info(wallet, token_address, token_name, token_balance, total_in_sol)
                        else:
                            db.save_new_token(wallet, token_address, token_name, token_balance, total_in_sol)

                        updated_tokens.add(token_address)
                for token_address in existing_tokens:
                    if token_address not in updated_tokens:
                        print(f"Удаляю токен {token_address} для кошелька {wallet}")
                        db.remove_token(wallet, token_address)

            except KeyError:
                print(f"Не удалось извлечь данные из ответа для кошелька {wallet}.")
        else:
            print(f"Не удалось получить данные о токенах для кошелька {wallet}.")



def main():
    db = Database(minconn=1, maxconn=10, dbname=cfg.dbname, user=cfg.user, password=cfg.password)
    while True:
        process_wallets(db)

        print("Ожидаю 2 минут перед следующим обновлением...")
        time.sleep(120)


if __name__ == "__main__":
    main()
