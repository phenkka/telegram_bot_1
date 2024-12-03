import aiohttp
import asyncio
import re
import app.config as cfg
from datetime import datetime, timezone
from db.database import Database


db = Database(minconn=1, maxconn=10, dbname=cfg.dbname, user=cfg.user, password=cfg.password)
api_key = cfg.HELIUM_API
current_timestamp = datetime.now(timezone.utc).timestamp()
day_timestamp = 86400
SOLANA_ADDRESS_REGEX = r'^[1-9A-HJ-NP-Za-km-z]{32,44}$'
sleep_interval = 1800

wallets = db.get_wallets()
print(wallets)

# Список кошельков
# wallets = ["AZzEApuBNjzewryE6gU4F76nLwWANpnCZ2DXShsdmbpF", "3kebnKw7cPdSkLRfiMEALyZJGZ4wdiSRvmoN4rD1yPzV"]


def has_one_decimal_place(number_str):
    if '.' in number_str:
        fractional_part = number_str.split('.')[1]
        return len(fractional_part) > 1
    return False

async def fetch_wallet_transactions(wallet):
    base_url = f"https://api.helius.xyz/v0/addresses/{wallet}/transactions"
    url = f"{base_url}?api-key={api_key}"

    while True:
        # Выполнение асинхронного запроса
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                # Проверка статуса ответа
                if response.status == 200:
                    transactions = await response.json()

                    if transactions:
                        for tx in transactions:
                            # Получаем описание токена, если доступно
                            description = tx.get("description", "No description").split(" ")
                            operation_type = tx.get("type", "Unknown")
                            timestamp = tx.get("timestamp")

                            # Проверка корректности описания
                            if not re.match(SOLANA_ADDRESS_REGEX, description[-1][:-1]):
                                continue

                            if timestamp + day_timestamp > current_timestamp:
                                if operation_type == 'SWAP':
                                    existing_tokens = db.get_tokens_for_wallet(description[0])
                                    if (description[-1], timestamp) in existing_tokens or not has_one_decimal_place(description[-2]) or float(description[-2]) < 1000:
                                        continue
                                    print(f"Description: {description}")
                                    print(f"Wallet: {description[0]}")
                                    print(f"Token: {description[-1]}")
                                    print(f"Token_am: {description[-2]}")
                                    print(f"Time: {timestamp}")
                                    print(f"Type: {operation_type}\n")
                                    db.add_transaction(description[0], description[-1], description[-2], timestamp, 'SWAP')


                                elif operation_type == "TRANSFER" and wallet == description[-1][:-1] and description[-3] != "SOL":
                                    existing_tokens = db.get_tokens_for_wallet(description[-1])
                                    if (description[-3], timestamp) in existing_tokens or not has_one_decimal_place(description[2]) or float(description[2]) < 1000:
                                        continue
                                    print(f"Description: {description}")
                                    print(f"Wallet: {description[-1][:-1]}")
                                    print(f"Token: {description[-3]}")
                                    print(f"Token_am: {description[2]}")
                                    print(f"Time: {timestamp}")
                                    print(f"Type: {operation_type}\n")
                                    db.add_transaction(description[-1][:-1], description[-3], description[2], timestamp, 'TRANSFER')

                    # Ожидаем 1 минуту перед следующим запросом
                    print(f"\nSleeping for {sleep_interval // 60} minutes...")
                    await asyncio.sleep(sleep_interval)


async def fetch_and_parse_transactions():
    db.delete_old_transaction()
    # Создаем задачи для всех кошельков
    tasks = [fetch_wallet_transactions(wallet) for wallet in wallets]

    # Запускаем все задачи одновременно
    await asyncio.gather(*tasks)


# Запуск асинхронной функции
if __name__ == "__main__":
    asyncio.run(fetch_and_parse_transactions())
