import aiohttp
import asyncio
import re
from datetime import datetime, timezone
from app.config import HELIUM_API
from db.database import Database

# Инициализация базы данных и переменных
db = Database("db/database.db")
api_key = HELIUM_API
last_signatures = {}  # Хранение last_signature для каждого кошелька
current_timestamp = datetime.now(timezone.utc).timestamp()
day_timestamp = 86400
SOLANA_ADDRESS_REGEX = r'^[1-9A-HJ-NP-Za-km-z]{32,44}$'
sleep_interval = 60  # Интервал ожидания в секундах


async def fetch_wallet_transactions(wallet, session):
    global last_signatures
    base_url = f"https://api.helius.xyz/v0/addresses/{wallet}/transactions"
    url = f"{base_url}?api-key={api_key}"

    # Если last_signature существует, добавляем его в запрос
    last_signature = last_signatures.get(wallet)
    if last_signature:
        url = f"{url}&before={last_signature}"

    # Выполнение запроса к API
    async with session.get(url) as response:
        if response.status == 200:
            transactions = await response.json()
            if transactions:
                # Фильтруем только транзакции с type == "SWAP"
                swap_transactions = [tx for tx in transactions if tx.get("type") == "SWAP"]
                for tx in swap_transactions:
                    # Обрабатываем данные транзакции
                    description = tx.get("description", "No description").split(" ")

                    if len(description) != 7:
                        continue

                    if len(description[-1]) <= 15:
                        continue

                    if not re.match(SOLANA_ADDRESS_REGEX, description[-1]) and (description[3] != 'SOL'):
                        continue

                    # Извлекаем время транзакции из данных API
                    timestamp = tx.get("timestamp", 0)
                    # Конвертируем timestamp в формат UTC
                    transaction_time = datetime.utcfromtimestamp(timestamp).isoformat()

                    if timestamp + day_timestamp > current_timestamp:
                        # Добавляем транзакцию в базу данных
                        db.add_transaction(wallet, description[-1], description[-2], description[2], transaction_time)
                        print(f"Description: {description}")
                        print(f"Wallet: {wallet}")
                        print(f"Token: {description[-1]}")
                        print(f"Token_amount: {description[-2]}")
                        print(f"Amount: {description[2]}")
                        print(f"Transaction Time: {transaction_time}\n")

                # Сохраняем last_signature для текущего кошелька
                last_signatures[wallet] = transactions[-1]["signature"]


async def fetch_and_parse_transactions():
    """
    Основной цикл обработки транзакций.
    """
    async with aiohttp.ClientSession() as session:
        while True:
            # Получаем список кошельков из базы данных
            wallets = db.get_wallets()

            # Создаем задачи для всех кошельков
            tasks = [fetch_wallet_transactions(wallet, session) for wallet in wallets]

            # Ожидаем выполнения всех задач
            await asyncio.gather(*tasks)

            # Удаляем старые транзакции из базы данных
            db.delete_old_transaction()

            # Засыпаем на заданное время
            print(f"\nSleeping for {sleep_interval // 60} minutes...")
            await asyncio.sleep(sleep_interval)


# Запуск асинхронной функции
if __name__ == "__main__":
    asyncio.run(fetch_and_parse_transactions())
