import logging
import asyncio
import re

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiocryptopay import Networks, AioCryptoPay

from db.database import Database
from app import config as cfg
import app.keyboards as kb
from dex_parse import fetch_token_data


bot = Bot(token=cfg.token)
dp = Dispatcher(bot=bot, storage=MemoryStorage())
db = Database(minconn=1, maxconn=25, dbname=cfg.dbname, user=cfg.user, password=cfg.password)


client = AioCryptoPay(token=cfg.TOKEN_CRYPTO_BOT, network=Networks.MAIN_NET)

API = cfg.API
SOLANA_ADDRESS_REGEX = r'^[1-9A-HJ-NP-Za-km-z]{32,44}$'

logging.basicConfig(level=logging.INFO)

class Form(StatesGroup):
    add_wallet = State()
    check_sol_wallet = State()
    check_sol_holders = State()


"""Блок настройки доступа к боту"""
# <<<------------------------------------------------------------------------------------------------>>>
# Функция для проверки статуса платежа
async def check_payment(user_id: int):
    payment_status = db.get_payment_status(user_id)  # Здесь проверяется статус оплаты в базе данных
    return payment_status == "paid"  # Возвращает True, если оплачено

# async def check_user_access(message: Message, database, check_payment_func):
#     user_id = message.from_user.id
#     group_id = cfg.TG_ID
#     chat_member = await bot.get_chat_member(group_id, user_id)
#     if not await check_payment_func(user_id) or not database.is_payment_valid(user_id):
#         await message.answer("Payment 💸 expired or missing ⏳. Please use the /pay command to renew. <b>30-days</b> subscription", parse_mode='HTML')
#         return False
#     if chat_member.status not in ["member", "administrator", "creator"]:
#         await message.answer("⚠️ To use the bot, you need to be a member of our group. Please subscribe:"
#             f" <a href='https://t.me/{group_id[1:]}'>{group_id}</a>", parse_mode='HTML')
#         return
#     return True



@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    db.update_payment_status(user_id, "paid")
    fabu_img_path = 'img/fabu.png'
    fabu_img = FSInputFile(fabu_img_path)

    # if not await check_user_access(message, db, check_payment):
    #     return

    await message.answer_photo(
        photo=fabu_img,
        caption="🤖 Hello there! 👋"
                "\n\nI’m your AI assistant, ready to help you dive into the 💼 depths of influencers’ wallets I’ve learned about. 🕵️‍♂️ Let’s explore what treasures they hold... 💎"
                "\n\nBut... 🤔 I don’t know everyone just yet. Over time, I’ll keep expanding my knowledge base! 🚀  "
                "\n\n🌟 So, what do you say? Shall we begin?"
                f"\n\n<a href='{cfg.ref_tgc}'>Channel</a> | <a href='{cfg.ref_tgchat}'>Chat</a> | <a href='{cfg.ref_sup}'>Support</a>",
        reply_markup=kb.greeting,
        parse_mode='HTML'
    )

@dp.message(Command("pay"))
async def pay_command(message: Message):
    invoice = await client.create_invoice(asset='USDT', amount=0.05)
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Payment Link", url=invoice.bot_invoice_url))
    builder.add(InlineKeyboardButton(text="Check Payment", callback_data=f"CHECK|{invoice.invoice_id}"))
    builder.adjust(1)
    await message.answer("🎩 To access my abilities, you’ll need to pay 💸. Let’s keep this between us 😉, okay?\n"
                         "Then press <i>Check Payment</i> to check the transaction status", reply_markup=builder.as_markup(), parse_mode='HTML')

@dp.callback_query(lambda c: c.data.startswith("CHECK|"))
async def check_invoice(call: CallbackQuery):
    invoice_id = int(call.data.split("|")[1])
    invoice = await client.get_invoices(invoice_ids=invoice_id)

    if invoice.status == "paid":
        user_id = call.from_user.id
        db.update_payment_status(user_id, "paid")  # Обновляем статус оплаты в базе данных
        await call.message.delete()
        await call.message.answer("🎉 Order paid! Now you’ve got <b>30 days</b> ⏳ to use my abilities. Use them wisely 🕵️‍♂️.", parse_mode='HTML')
    else:
        await call.answer("🤔 I don’t see the payment 💸 ... Is there something you're hiding? 🤨")
# <<<------------------------------------------------------------------------------------------------>>>


"""Блок меню"""
# <<<------------------------------------------------------------------------------------------------>>>
"""Функция для отправки меню"""
"""Ниже - хендлеры для вызова через команду и просто"""

async def menu(message_or_callback):
    # if not await check_user_access(message_or_callback, db, check_payment):
    #     return
    user_id = message_or_callback.from_user.id
    db.update_payment_status(user_id, "paid")

    if isinstance(message_or_callback, Message):
        await message_or_callback.answer("🤖 What would you like to explore next? Your turn, thinker 🧠... The choice is yours! ✨", reply_markup=kb.menu)
    elif isinstance(message_or_callback, CallbackQuery):
        await message_or_callback.message.answer("🤖 What would you like to explore next? Your turn, thinker 🧠... The choice is yours! ✨ ", reply_markup=kb.menu)

@dp.callback_query(F.data == "start")
async def process_menu(callback_query: CallbackQuery):
    await menu(callback_query)

@dp.message(Command('menu'))
async def cmd_menu(message: Message):
    await menu(message)
# <<<------------------------------------------------------------------------------------------------>>>


"""Блок настроек"""
# <<<------------------------------------------------------------------------------------------------>>>
def generate_notify_keyboard(status1, status2):
    # button_text = "🟢 On" if status else "🔴 Off"
    button_text1 = "🟢 Notify influencers" if status1 else "🔴 Notify influencers"
    button_text2 = "🟢 Notify smarts" if status2 else "🔴 Notify smart"

    # button = InlineKeyboardButton(text=button_text, callback_data="toggle_notify")
    button1 = InlineKeyboardButton(text=button_text1, callback_data="infl_notify")
    button2 = InlineKeyboardButton(text=button_text2, callback_data="smart_notify")
    button_menu = InlineKeyboardButton(text="Menu", callback_data='start')

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button1, button2], [button_menu]])
    return keyboard

async def spy(message_or_callback):
    user_id = message_or_callback.from_user.id

    notify_infl = db.get_notify_infl(user_id)
    notify_smart = db.get_notify_smart(user_id)
    keyboard = generate_notify_keyboard(notify_infl, notify_smart)

    message = "🤖 Ah, keeping track of the influencers’ moves, are we? 😏 Just enable this feature, and I’ll notify you whenever I spot a token catching the attention of influencers! 🚀👀 Always here to keep you informed."

    if isinstance(message_or_callback, Message):
        await message_or_callback.answer(message, reply_markup=keyboard, parse_mode='HTML')
    elif isinstance(message_or_callback, CallbackQuery):
        await message_or_callback.message.edit_text(message, reply_markup=keyboard, parse_mode='HTML')

@dp.callback_query(F.data == "spy")
async def process_spy(callback_query: CallbackQuery):
    await spy(callback_query)

@dp.message(Command('spy'))
async def cmd_spy(message: Message):
    await spy(message)

@dp.callback_query(lambda c: c.data == "infl_notify")
async def toggle_notify_infl(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    current_status = db.get_notify_infl(user_id)
    new_status = not current_status

    db.update_notify_infl_status(user_id, new_status)

    notify_infl = db.get_notify_infl(user_id)
    notify_smart = db.get_notify_smart(user_id)

    status_message = "Influencer notifications " + ("enabled!" if new_status else "disabled!")
    await callback_query.answer(status_message, show_alert=True)

    keyboard = generate_notify_keyboard(notify_infl, notify_smart)
    await bot.edit_message_reply_markup(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=keyboard
    )

@dp.callback_query(lambda c: c.data == "smart_notify")
async def toggle_notify_smart(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    current_status = db.get_notify_smart(user_id)
    new_status = not current_status

    db.update_notify_smart_status(user_id, new_status)

    notify_infl = db.get_notify_infl(user_id)
    notify_smart = db.get_notify_smart(user_id)

    status_message = "Smart notifications " + ("enabled!" if new_status else "disabled!")
    await callback_query.answer(status_message, show_alert=True)

    keyboard = generate_notify_keyboard(notify_infl, notify_smart)
    await bot.edit_message_reply_markup(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=keyboard
    )


async def background_task():
    try:
        while True:

            retry_attempts = 5
            tokens = None
            for attempt in range(retry_attempts):
                try:
                    tokens = db.get_tokens_with_more_than_5_unique_wallets()
                    if tokens:
                        break
                    else:
                        print("Нет токенов, повторяю попытку.")
                except Exception as e:
                    print(f"Ошибка при получении токенов, попытка {attempt + 1}: {e}")
                    if attempt == retry_attempts - 1:
                        print("Превышено количество попыток для получения токенов.")
                        raise

            for token in tokens:
                infl_count, all_count, degen_count = 0, 0, 0

                if not db.is_token_notified(token):

                    retry_attempts_wallets = 5
                    wallets = None
                    for attempt in range(retry_attempts_wallets):
                        try:
                            wallets = db.get_unique_wallets_for_token(token)
                            if wallets:
                                break
                            else:
                                print(f"Нет кошельков для токена {token}, повторяю попытку.")
                        except Exception as e:
                            print(f"Ошибка при получении кошельков для токена {token}, попытка {attempt + 1}: {e}")
                            if attempt == retry_attempts_wallets - 1:
                                print(f"Превышено количество попыток для получения кошельков для токена {token}.")
                                raise

                    try:
                        symbol, market_cap = fetch_token_data(token)
                    except ValueError as e:
                        symbol, market_cap = 'unknown', '0000'

                    if len(market_cap) < 7:
                        market_cap = f"{market_cap[:-3]}K"

                    elif 7 <= len(market_cap) < 10:
                        market_cap = f"{market_cap[:-6]}.{market_cap[-6:-4]}M"

                    else:
                        market_cap = f"{market_cap[:-9]}.{market_cap[-9:-7]}B"

                    message = (f"🔔 <b>${symbol}</b> <code>{token}</code> is being actively bought!"
                               f"\nMC: <i>{market_cap}</i> 💲"
                               f"\nHere's the list:\n\n")
                    message_smart = (f"🔔 <b>${symbol}</b> <code>{token}</code> is being actively bought!"
                               f"\nMC: <i>{market_cap}</i> 💲"
                               f"\nHere's the list:\n\n")
                    message_infl = (f"🔔 <b>${symbol}</b> <code>{token}</code> is being actively bought!"
                               f"\nMC: <i>{market_cap}</i> 💲"
                               f"\nHere's the list:\n\n")

                    for wallet in wallets:
                        retry_attempts_wallet = 5
                        for attempt in range(retry_attempts_wallet):
                            try:
                                result = db.get_data(wallet)
                                if result is not None:
                                    try:
                                        pnl, wr = result
                                    except (ValueError, TypeError):
                                        pnl, wr = 25, 30
                                    pnl_emoji = "🟢" if float(pnl.strip('%')) > 0 else "🔴"
                                    wr_emoji = "🟢" if float(wr.strip('%')) > 50 else "🔴"
                                    infl, link = db.get_influencer(wallet)

                                    all_count += 1
                                    message += (
                                        f"{pnl_emoji} PNL: {pnl}, {wr_emoji} WR(7d): {wr}, <b><a href='{link}'>{infl}</a></b>\n"
                                        f"<code>{wallet}</code>\n\n"
                                    )

                                    if infl == 'smart_degen':
                                        degen_count += 1
                                        message_smart += (
                                            f"{pnl_emoji} PNL: {pnl}, {wr_emoji} WR(7d): {wr}, <b><a href='{link}'>{infl}</a></b>\n"
                                            f"<code>{wallet}</code>\n\n"
                                        )
                                    else:
                                        infl_count += 1
                                        message_infl += (
                                            f"{pnl_emoji} PNL: {pnl}, {wr_emoji} WR(7d): {wr}, <b><a href='{link}'>{infl}</a></b>\n"
                                            f"<code>{wallet}</code>\n\n"
                                        )
                                else:
                                    continue
                                break
                            except Exception as e:
                                print(f"Ошибка при обработке кошелька {wallet}, попытка {attempt + 1}: {e}")
                                if attempt == retry_attempts_wallet - 1:
                                    print(f"Превышено количество попыток для кошелька {wallet}.")
                                    continue

                    if all_count > 2 or infl_count > 2 or degen_count > 1:
                        print('захожу в нотифай юзерс')
                        db.add_notified_token(token)
                        await notify_users(message, message_smart, message_infl, infl_count, all_count, degen_count)

            await asyncio.sleep(60)
    except Exception as e:
        print(f"Общая ошибка в background_task: {e}")
        print("Произошла ошибка, будет попытка повторить выполнение через 60 секунд.")
        await asyncio.sleep(60)

async def notify_users(message, message_smart, message_infl, infl_count, all_count, degen_count):
    users_with_notifications = db.get_users_with_notifications()
    print(users_with_notifications)

    for user_id in users_with_notifications:
        try:
            notify_infl = db.get_notify_infl(user_id)
            notify_smart = db.get_notify_smart(user_id)

            if notify_infl and notify_smart and all_count > 2:
                await bot.send_message(user_id, message, parse_mode='HTML', disable_web_page_preview=True)
                continue

            elif notify_infl and infl_count > 2:
                await bot.send_message(user_id, message_infl, parse_mode='HTML', disable_web_page_preview=True)
                continue

            elif notify_smart and degen_count > 1:
                await bot.send_message(user_id, message_smart, parse_mode='HTML', disable_web_page_preview=True)
                continue

            else:
                continue
        except Exception as e:
            print(f"Ошибка при отправке уведомления пользователю {user_id}: {e}")
# <<<------------------------------------------------------------------------------------------------>>>


"""Блок проверки кошельков"""
# <<<------------------------------------------------------------------------------------------------>>>
async def check(message_or_callback, state: FSMContext):
    # Формируем основное сообщение для обоих случаев
    # if not await check_user_access(message_or_callback, db, check_payment):
    #     return

    message_text = "🤖 Alright, here’s how it works:"\
                   "You can input a 💳 <u><b>wallet</b></u>, and I’ll check if I recognize it and share its 📊 stats.\n" \
                   "Or, if you’d rather provide an 🤵 <u><b>influencer’s name</b></u>, I’ll show you their 💼 wallets and the data I’ve gathered.\n\n" \
                   "The choice is yours — let’s dive in! 🚀"

    if isinstance(message_or_callback, Message):
        await message_or_callback.answer(message_text, parse_mode='HTML', reply_markup=kb.tips)

    elif isinstance(message_or_callback, CallbackQuery):
        await message_or_callback.message.answer(message_text, parse_mode='HTML', reply_markup=kb.tips)
    await state.set_state(Form.check_sol_wallet)


@dp.callback_query(F.data == "tip")
async def process_tip(callback_query: CallbackQuery, state: FSMContext):
    message_text = "That's who I know about... Looks around cautiously You know, top secret stuff 🤐: "

    influencers = db.get_influencers()
    excluded_names = {"smart_degen", "fabu"}
    filtered_influencers = [influencer for influencer in influencers if influencer not in excluded_names]

    if filtered_influencers:
        influencer_list = ", ".join(filtered_influencers)
        message_text += influencer_list
    else:
        message_text += "No one to share this time!"

    await state.set_state(Form.check_sol_wallet)
    await callback_query.message.answer(message_text, parse_mode='HTML')


@dp.callback_query(F.data == "check_sol")
async def process_check_start(callback_query: CallbackQuery, state: FSMContext):
    await check(callback_query, state)

@dp.message(Command('check'))
async def cmd_check(message: Message, state: FSMContext):
    await check(message, state)

"""Блок проверки SOL кошельков"""
@dp.message(Form.check_sol_wallet)
async def process_check_end(message: Message, state: FSMContext):
    query = message.text

    if query.startswith('/'):
        await state.clear()
        await cmd_holders(message, state)
        return

    if query == 'smart_degen':
        return

    if re.match(SOLANA_ADDRESS_REGEX, message.text):
        result = db.check_row(query)

        if result:
            if len(result) == 2:  # Проверяем, что результат состоит из 2 элементов
                user, link = result  # Извлекаем значения из кортежа
            else:
                await message.reply("Sorry, no valid data found for this wallet.")
                return
            count_wallets = db.count_wallets(user)


            await message.reply(f"Yes, I know the owner of this wallet 😏. "
                                f"This is 🤵 <b><a href='{link}'>{user}</a></b>. 🕵️‍ Don't tell anyone! ️",
                                parse_mode='HTML', disable_web_page_preview=True)
            if count_wallets > 1:
                user_wallets = db.get_user_wallets(user)
                list_wallets = ''
                for user_wallet in user_wallets:
                    wallet_address = user_wallet[0]
                    pnl, wr = db.get_data(wallet_address)

                    if pnl is not None and wr is not None:
                        pnl_emoji = "🟢" if float(pnl.strip('%')) > 0 else "🔴"
                        wr_emoji = "🟢" if float(wr.strip('%')) > 50 else "🔴"

                        # Формируем строку для кошелька
                        list_wallets += (
                            f"{pnl_emoji} PNL: {pnl}, {wr_emoji} WR(7d): {wr}\n"
                            f"<code>{wallet_address}</code>\n\n"
                        )
                    else:
                        list_wallets += f"<code>{wallet_address}</code>\nNo data available for PNL/WR.\n\n"

                await message.answer(
                    f"🤵 <b><a href='{link}'>{user}</a></b> has 💰 <b>{count_wallets}</b> wallet(s):\n\n{list_wallets.strip()}",
                    reply_markup=kb.return_menu, parse_mode='HTML', disable_web_page_preview=True
                )

            else:
                await message.answer(f"This is the only wallet of 🤵 <b>{user}</b>.", reply_markup=kb.return_menu,
                                     parse_mode='HTML')

        else:
            await message.reply("Unfortunately 😭, I don't know anything about this wallet. This one is a mystery!")
    else:
        wallets = db.check_infl(message.text.lower())
        if wallets:
            response = "Yeah 🤔, I remember it now... Here are all of their 💼 wallets:\n\n"

            for wallet in wallets:
                wallet_address = wallet[0]
                pnl, wr = db.get_data(wallet_address)

                if pnl is not None and wr is not None:
                    pnl_emoji = "🟢" if float(pnl.strip('%')) > 0 else "🔴"
                    wr_emoji = "🟢" if float(wr.strip('%')) > 50 else "🔴"

                    # Формируем строку для каждого кошелька
                    response += (
                        f"{pnl_emoji} PNL: {pnl}, {wr_emoji} WR(7d): {wr}\n"
                        f"<code>{wallet_address}</code>\n\n"
                    )
                else:
                    response += f"<code>{wallet_address}</code>\nNo data available for PNL/WR.\n\n"

            await message.reply(response.strip(), reply_markup=kb.return_menu, parse_mode='HTML')
        else:
            await message.reply("Unfortunately 😭, I don't know this user.")


# <<<------------------------------------------------------------------------------------------------>>>


# <<<------------------------------------------------------------------------------------------------>>>
async def holders(message_or_callback, state: FSMContext):
    # if not await check_user_access(message_or_callback, db, check_payment):
    #     return
    if isinstance(message_or_callback, Message):
        await message_or_callback.answer("🤖 Here, you can ✍️ enter a <u><b>token address</b></u>, and I’ll 🔍 help you figure out who is holding it, along with any details I’ve gathered. Let’s keep it simple and efficient — ready when you are! 🚀", parse_mode='HTML')
    elif isinstance(message_or_callback, CallbackQuery):
        await message_or_callback.message.answer("🤖 Here, you can ✍️ enter a <u><b>token address</b></u>, and I’ll 🔍 help you figure out who is holding it, along with any details I’ve gathered. Let’s keep it simple and efficient — ready when you are! 🚀", parse_mode='HTML')
    await state.set_state(Form.check_sol_holders)

@dp.callback_query(F.data == "holders")
async def process_holders_start(callback_query: CallbackQuery, state: FSMContext):
    await holders(callback_query, state)

@dp.message(Command('holders'))
async def cmd_holders(message: Message, state: FSMContext):
    await holders(message, state)


@dp.message(Form.check_sol_holders)
async def process_holders_end(message: Message, state: FSMContext):
    token_address = message.text.strip()

    if token_address.startswith('/check'):
        await state.clear()
        await cmd_check(message, state)
        return

    token_name = db.get_token_name_by_address(token_address)
    wallets = db.get_wallets_by_token(token_address)

    if re.match(SOLANA_ADDRESS_REGEX, message.text):
        if wallets:
            response = f"Here are the 🤵 influencers who own 💵 <b>{token_name}</b>:\n<code>{token_address}</code>:\n\n"
            for wallet, total_in_sol in wallets:
                wallet_info = db.check_row(wallet)
                if isinstance(wallet_info, dict):  # Проверяем, что вернулся словарь
                    user = wallet_info.get('user', 'Unknown User')  # Используем безопасное извлечение
                    link = wallet_info.get('link', '#')  # Ссылка по умолчанию
                    response += f"Here 💰 <code>{wallet}</code> holds the token, which is owned by 👨 <b><a href='{link}'>{user}</a></b>, and it has tokens worth 💲 <b>{total_in_sol} SOL</b>\n\n"
                else:
                    response += f"So {wallet}, Balance: {total_in_sol} SOL. Owner information not found.\n\n"
            await message.answer(response, reply_markup=kb.return_menu, parse_mode='HTML', disable_web_page_preview=True)
        else:
            await message.answer(f"Unfortunately 😢, no one owns this token... yet. But who knows, maybe soon I’ll have more info!")
    else:
        await message.reply("Listen 😠, please enter a valid token address. I'm trying to help here!")
# <<<------------------------------------------------------------------------------------------------>>>




"""ДЛЯ РАЗРАБА"""
"""Блок для добавление кошельков и их инфлов в базу"""
# <<<------------------------------------------------------------------------------------------------>>>
"""Функция для добавления кошельков в базу"""

@dp.message(Command('etomoyacomanda'))
async def cmd_add_wallet(message: Message, state: FSMContext):
    my_id = cfg.MY_ID
    if int(message.from_user.id) == my_id:
        await state.clear()
        await message.answer(
            "Введи через пробел <u><b>кошелек</b></u>, <u><b>имя инфлюенсера</b></u> и <u><b>ссылку</b></u>."
            "\n<b>Например: wallet nickname link</b>"
            "\nP.s. Если имя инфла включает пробел, то его надо заменить на <b>[пробел]</b>", parse_mode='HTML')
        await state.set_state(Form.add_wallet)
    else:
        await message.reply('Ты сейчас про что? 🤷‍♂️')


"""Хендлер для окончания добавления кошельков базу"""
"""Может не добавить какой то кош изза проверки"""

@dp.message(Form.add_wallet)
async def process_add_end(message: Message):
    data = message.text.split(' ')
    data[1] = data[1].replace('[пробел]', ' ').lower()

    if len(data) > 4:
        await message.reply('См. образец!')
        return

    if not db.add_row(data[0], data[1], data[2], data[3]):
        await message.reply("Ошибка!")
        return

    await message.reply("Занесено!")
# <<<------------------------------------------------------------------------------------------------>>>



async def main():
    db.remove_expired_users()
    asyncio.create_task(background_task())
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exit")