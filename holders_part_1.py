import asyncio
import aiohttp
from db.database import Database

# Адрес RPC для получения токенов на кошельке
RPC_URL = "https://api.mainnet-beta.solana.com"


# Функция получения токенов на кошельке с фильтрацией по балансу
async def get_token_accounts(wallet_address, session):
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
        async with session.post(RPC_URL, headers=headers, json=payload, timeout=10) as response:
            response.raise_for_status()
            data = await response.json()
            if 'result' in data and 'value' in data['result']:
                accounts = data['result']['value']
                # Фильтруем токены, оставляя только те, у которых баланс > 0.01
                filtered_accounts = [
                    account for account in accounts
                    if account['account']['data']['parsed']['info']['tokenAmount']['uiAmount'] > 0.01
                ]
                return filtered_accounts
    except Exception as e:
        print(f"Ошибка при запросе данных о токенах для кошелька {wallet_address}: {e}")
    return []


# Функция для получения информации о токене
async def get_token_info(token_address, session):
    url = f"https://api.dexscreener.com/latest/dex/search?q={token_address}"

    try:
        async with session.get(url, timeout=10) as response:
            response.raise_for_status()
            data = await response.json()
            if "pairs" in data:
                for pair in data["pairs"]:
                    # Ищем пару с SOL в качестве base или quote токена
                    if pair['baseToken']['address'] == token_address or pair['quoteToken']['address'] == token_address:
                        token_name = pair['baseToken']['name'] if pair['baseToken']['address'] == token_address else \
                        pair['quoteToken']['name']
                        token_price_in_sol = float(pair['priceNative']) if pair['baseToken']['symbol'] == "SOL" or \
                                                                           pair['quoteToken'][
                                                                               'symbol'] == "SOL" else None
                        return token_name, token_price_in_sol
    except Exception as e:
        print(f"Ошибка при запросе данных о токене {token_address}: {e}")
    return "Неизвестно", None


# Основной цикл обработки всех кошельков
async def process_wallets(db, session):
    # Получаем все кошельки из базы данных
    wallets = db.get_wallets()

    tasks = []
    for wallet in wallets:
        print(f"\nОбрабатываю кошелек: {wallet}")
        tasks.append(process_wallet(wallet, db, session))

    # Запускаем все задачи параллельно
    await asyncio.gather(*tasks)


async def process_wallet(wallet, db, session):
    accounts = await get_token_accounts(wallet, session)

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
                token_name, token_price_in_sol = await get_token_info(token_address, session)

                # Пропуск токенов с нулевым балансом или если баланс меньше 0.01
                if token_price_in_sol is None:
                    continue

                total_in_sol = round(token_balance * token_price_in_sol, 4)  # Округление до 4 знаков после запятой

                if total_in_sol > 0.01:
                    print(
                        f"Токен: {token_name} (Адрес: {token_address}), Сумма в SOL: {total_in_sol:.4f}")  # Округление в выводе

                    # Если токен уже есть в базе, обновляем информацию
                    if token_address in existing_tokens:
                        db.update_token_info(wallet, token_address, token_name, token_balance, total_in_sol)
                    else:
                        # Если токен новый, добавляем его в базу
                        db.save_new_token(wallet, token_address, token_name, token_balance, total_in_sol)

                    # Добавляем токен в обновленный список
                    updated_tokens.add(token_address)
                await asyncio.sleep(0.5)
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
async def main():
    # Инициализация базы данных
    db = Database('db/database.db')
    db.create_table()

    async with aiohttp.ClientSession() as session:
        while True:
            # Обработка всех кошельков
            await process_wallets(db, session)

            # Задержка между выполнениями (например, 10 минут)
            print("Ожидаю 10 минут перед следующим обновлением...")
            await asyncio.sleep(600)  # 600 секунд = 10 минут


if __name__ == "__main__":
    asyncio.run(main())
