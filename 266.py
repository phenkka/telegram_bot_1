import aiohttp
import asyncio
import re

from app.config import HELIUM_API
from datetime import datetime, timedelta, timezone
from db.database import Transactions


db = Transactions("db/database.db")
wallet = '8yJFWmVTQq69p6VJxGwpzW7ii7c5J9GRAtHCNMMQPydj'
base_url = f"https://api.helius.xyz/v0/addresses/{wallet}/transactions"
api_key = HELIUM_API
url = f"{base_url}?api-key={api_key}"
last_signature = None

current_timestamp = datetime.now(timezone.utc).timestamp()
day_timestamp = 86400

SOLANA_ADDRESS_REGEX = r'^[1-9A-HJ-NP-Za-km-z]{32,44}$'

sleep_interval = 60

async def fetch_and_parse_transactions():
    global last_signature

    while True:
        # Выполнение асинхронного запроса
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                # Проверка статуса ответа
                if response.status == 200:
                    transactions = await response.json()

                    if transactions:
                        # Фильтруем только транзакции с type == "SWAP"
                        swap_transactions = [tx for tx in transactions if tx.get("type") == "SWAP"]

                    print(transactions)

                    if transactions:
                        for tx in transactions:
                            print(tx)
                            # # Получаем описание токена, если доступно
                            # description = tx.get("description", "No description")[:-1].split(" ")
                            # operation_type = tx.get("type", "Unknown")
                            # timestamp = tx.get("timestamp")
                            #
                            # if not re.match(SOLANA_ADDRESS_REGEX, description[-1]):
                            #     continue
                            #
                            # if wallet not in description:
                            #     continue
                            #
                            # if timestamp + day_timestamp > current_timestamp:
                            #     if operation_type == 'SWAP':
                            #
                            #         print(f"Description: {description}")
                            #         print(f"Wallet: {description[0]}")
                            #         print(f"Token: {description[-1]}")
                            #         print(f"Token_am: {description[-2]}")
                            #         print(f"Time: {timestamp}")
                            #         print(f"Type: {operation_type}\n")
                            #     elif operation_type == "TRANSFER" and wallet == description[-1]:
                            #         print(f"Description: {description}")
                            #         print(f"Wallet: {description[-1]}")
                            #         print(f"Token: {description[-3]}")
                            #         print(f"Token_am: {description[2]}")
                            #         print(f"Time: {timestamp}")
                            #         print(f"Type: {operation_type}\n")

        # Засыпаем на 3 минуты
        print(f"\nSleeping for {sleep_interval // 60} minutes...")
        await asyncio.sleep(sleep_interval)


# Запуск асинхронной функции
asyncio.run(fetch_and_parse_transactions())