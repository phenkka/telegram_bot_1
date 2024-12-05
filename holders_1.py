import asyncio
import aiohttp
from db.database import Database
import app.config as cfg

RPC_URL = "https://api.mainnet-beta.solana.com"


async def get_token_accounts(wallet_address, session):
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
        async with session.post(RPC_URL, headers=headers, json=payload, timeout=10) as response:
            response.raise_for_status()
            data = await response.json()
            if 'result' in data and 'value' in data['result']:
                accounts = data['result']['value']
                filtered_accounts = [
                    account for account in accounts
                    if account['account']['data']['parsed']['info']['tokenAmount']['uiAmount'] > 0.01
                ]
                return filtered_accounts
    except Exception as e:
        print(f"Ошибка при запросе данных о токенах для кошелька {wallet_address}: {e}")
    return []

async def get_token_info(token_address, session):
    url = f"https://api.dexscreener.com/latest/dex/search?q={token_address}"

    try:
        async with session.get(url, timeout=10) as response:
            response.raise_for_status()
            data = await response.json()
            if "pairs" in data:
                for pair in data["pairs"]:
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


async def process_wallets(db, session):
    wallets = db.get_wallets()

    tasks = []
    for wallet in wallets:
        print(f"\nОбрабатываю кошелек: {wallet}")
        tasks.append(process_wallet(wallet, db, session))

    await asyncio.gather(*tasks)


async def process_wallet(wallet, db, session):
    accounts = await get_token_accounts(wallet, session)

    if accounts:
        try:
            print(f"Найдено {len(accounts)} токенов для кошелька {wallet}:\n")

            existing_tokens = db.get_tokens_for_wallet(wallet)
            updated_tokens = set()

            for account in accounts:
                token_info = account['account']['data']['parsed']['info']
                token_address = token_info['mint']
                token_balance = token_info['tokenAmount']['uiAmount']

                token_name, token_price_in_sol = await get_token_info(token_address, session)

                if token_price_in_sol is None:
                    continue

                total_in_sol = round(token_balance * token_price_in_sol, 4)

                if total_in_sol > 0.01:
                    print(
                        f"Токен: {token_name} (Адрес: {token_address}), Сумма в SOL: {total_in_sol:.4f}")

                    if token_address in existing_tokens:
                        db.update_token_info(wallet, token_address, token_name, token_balance, total_in_sol)
                    else:
                        db.save_new_token(wallet, token_address, token_name, token_balance, total_in_sol)

                    updated_tokens.add(token_address)
                await asyncio.sleep(0.5)
            for token_address in existing_tokens:
                if token_address not in updated_tokens:
                    print(f"Удаляю токен {token_address} для кошелька {wallet}")
                    db.remove_token(wallet, token_address)

        except KeyError:
            print(f"Не удалось извлечь данные из ответа для кошелька {wallet}.")
    else:
        print(f"Не удалось получить данные о токенах для кошелька {wallet}.")


async def main():
    db = Database(minconn=1, maxconn=10, dbname=cfg.dbname, user=cfg.user, password=cfg.password)

    async with aiohttp.ClientSession() as session:
        while True:
            await process_wallets(db, session)

            print("Ожидаю 2 минут перед следующим обновлением...")
            await asyncio.sleep(120)


if __name__ == "__main__":
    asyncio.run(main())
