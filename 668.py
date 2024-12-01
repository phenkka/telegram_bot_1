import requests
import time
from db.database import Database

# Адрес RPC для получения токенов на кошельке
RPC_URL = "https://api.mainnet-beta.solana.com"

# Функция получения токенов на кошельке с фильтрацией по балансу
def get_token_accounts(wallet_address):
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTokenAccountsByOwner",
        "params": [
            wallet_address,
            {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},  # Программа токенов Solana
            {"encoding": "jsonParsed"}
        ]
    }

    try:
        response = requests.post(RPC_URL, headers=headers, json=payload, timeout=10)  # Тайм-аут 10 секунд
        response.raise_for_status()
        if response.status_code == 200:
            data = response.json()
            if 'result' in data and 'value' in data['result']:
                accounts = data['result']['value']
                # Фильтруем токены, оставляя только те, у которых баланс > 0.01
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
        response = requests.get(url, timeout=2)  # Тайм-аут 10 секунд
        response.raise_for_status()
        if response.status_code == 200:
            data = response.json()
            if "pairs" in data:
                for pair in data["pairs"]:
                    # Ищем пару с SOL в качестве base или quote токена
                    if pair['baseToken']['address'] == token_address or pair['quoteToken']['address'] == token_address:
                        token_name = pair['baseToken']['name'] if pair['baseToken']['address'] == token_address else pair['quoteToken']['name']
                        token_price_in_sol = float(pair['priceNative']) if pair['baseToken']['symbol'] == "SOL" or pair['quoteToken']['symbol'] == "SOL" else None
                        return token_name, token_price_in_sol
    except requests.exceptions.Timeout:
        print(f"Тайм-аут при запросе данных о токене {token_address}.")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе данных о токене {token_address}: {e}")
    return "Неизвестно", None


# Основной цикл обработки всех кошельков
# Основной цикл обработки всех кошельков
def process_wallets(db):
    # Получаем все кошельки из базы данных
    wallets = db.get_wallets()

    # Перебор кошельков с конца
    for wallet in reversed(wallets):
        print(f"\nОбрабатываю кошелек: {wallet}")
        # Получаем информацию о токенах для кошелька
        accounts = get_token_accounts(wallet)

        if accounts:
            try:
                print(f"Найдено {len(accounts)} токенов для кошелька {wallet}:\n")

                # Получаем все текущие токены для этого кошелька из базы данных
                existing_tokens = db.get_tokens_for_wallet(wallet)
                updated_tokens = set()

                for account in accounts:
                    token_info = account['account']['data']['parsed']['info']
                    token_address = token_info['mint']  # Адрес токена (mint)
                    token_balance = token_info['tokenAmount']['uiAmount']  # Баланс токенов

                    # Получаем название токена и цену в SOL
                    token_name, token_price_in_sol = get_token_info(token_address)

                    # Пропуск токенов с нулевым балансом или если баланс меньше 0.01
                    if token_price_in_sol is None:
                        continue

                    total_in_sol = round(token_balance * token_price_in_sol, 4)  # Округление до 4 знаков после запятой

                    if total_in_sol > 0.01:
                        print(f"Токен: {token_name} (Адрес: {token_address}), Сумма в SOL: {total_in_sol:.4f}")  # Округление в выводе

                        # Если токен уже есть в базе, обновляем информацию
                        if token_address in existing_tokens:
                            db.update_token_info(wallet, token_address, token_name, token_balance, total_in_sol)
                        else:
                            # Если токен новый, добавляем его в базу
                            db.save_new_token(wallet, token_address, token_name, token_balance, total_in_sol)

                        # Добавляем токен в обновленный список
                        updated_tokens.add(token_address)

                # Удаляем токены, которые больше не присутствуют на кошельке
                for token_address in existing_tokens:
                    if token_address not in updated_tokens:
                        print(f"Удаляю токен {token_address} для кошелька {wallet}")
                        db.remove_token(wallet, token_address)

            except KeyError:
                print(f"Не удалось извлечь данные из ответа для кошелька {wallet}.")
        else:
            print(f"Не удалось получить данные о токенах для кошелька {wallet}.")



# Инициализация и запуск скрипта
def main():
    # Инициализация базы данных
    db = Database('db/database.db')
    db.create_table()

    while True:
        # Обработка всех кошельков
        process_wallets(db)

        # Задержка между выполнениями (например, 10 минут)
        print("Ожидаю 2 минут перед следующим обновлением...")
        time.sleep(120)


if __name__ == "__main__":
    main()
