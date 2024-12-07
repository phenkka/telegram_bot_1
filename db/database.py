import datetime
import sqlite3
from typing import Tuple, List

from psycopg2 import pool


class Database:
    def __init__(self, minconn, maxconn, dbname, user, password, host='rc1d-xiuvu9wy0xvcpdxn.mdb.yandexcloud.net', port='6432'):
        self.connection_pool = pool.SimpleConnectionPool(
            minconn,
            maxconn,
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )

    def get_connection(self):
        return self.connection_pool.getconn()

    def release_connection(self, conn):
        self.connection_pool.putconn(conn)

    def close_all_connections(self):
        self.connection_pool.closeall()

    def execute_read_many_query(self, query, params=None):
        conn = self.get_connection()
        result = None
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                if cursor.description:
                    result = cursor.fetchall()
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            self.release_connection(conn)
        return result

    def execute_read_one_query(self, query, params=None):
        conn = self.get_connection()
        result = None
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                if cursor.description:
                    result = cursor.fetchone()
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            self.release_connection(conn)
        return result

    def execute_write_query(self, query, params=None):
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                conn.commit()
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            self.release_connection(conn)

    """Функции SQL для таблицы sol_wallet"""

    def add_row(self, wallet, user, link, wallet_type):
        """Добавление нового кошелька"""
        exists_query = "SELECT EXISTS(SELECT 1 FROM sol_wallet WHERE wallet = %s);"
        exists_result: Tuple[bool] = self.execute_read_one_query(exists_query, params=(wallet,))
        if exists_result[0] is True:
            return False

        insert_query = """
            INSERT INTO sol_wallet(wallet, "user", link, wallet_type)
            VALUES (%s, %s, %s, %s);
        """
        self.execute_write_query(insert_query, (wallet, user, link, wallet_type))
        return True

    def get_user_wallets(self, user):
        """Получаем список кошельков пользователя"""
        query = """SELECT wallet_address FROM sol_wallet WHERE "user" = %s;"""
        result = self.execute_read_many_query(query, params=(user,))
        return result

    def get_wallets(self):
        """Получение списка всех кошельков"""
        query = "SELECT wallet FROM sol_wallet;"
        result = self.execute_read_many_query(query)
        wallets = [row[0] for row in result]
        return wallets

    def check_row(self, wallet):
        """Проверка существования кошелька и возвращение данных"""
        # Измените запрос, чтобы получать реальные данные, а не только булевое значение
        exists_query = "SELECT user, link FROM sol_wallet WHERE wallet = %s;"
        exists_result = self.execute_read_one_query(exists_query, params=(wallet,))

        # Печать результата для отладки
        print(exists_result)

        return exists_result

    def count_wallets(self, user):
        """Проверка, сколько кошельков у инфла"""
        count_query = """SELECT COUNT(*) FROM sol_wallet WHERE "user" = %s;"""
        count_result = self.execute_read_one_query(count_query, params=(user,))
        return count_result[0]

    def check_infl(self, user):
        """Проверка на наличие инфла в базе"""
        infl_query = """SELECT wallet FROM sol_wallet WHERE "user" = %s"""
        infl_result: List[Tuple] = self.execute_read_many_query(infl_query, params=(user,))
        if infl_result.__len__() == 0:
            return False
        return infl_result

    def get_influencers(self):
        """Получение списка всех уникальных инфлюенсеров (пользователей)"""
        infl_query = """SELECT DISTINCT "user" FROM sol_wallet"""
        infl_result: List[Tuple] = self.execute_read_many_query(infl_query)
        return [row[0] for row in infl_result]

    def get_influencer(self, wallet):
        """Получение информации о пользователе по кошельку"""
        infl_query = """SELECT "user", link FROM sol_wallet WHERE wallet = %s"""
        infl_result: List[Tuple] = self.execute_read_one_query(infl_query, params=(wallet,))
        return infl_result

    """Функции SQL для таблицы token_data"""

    def update_token_info(self, wallet, token_address, token_name, token_balance, total_in_sol):
        """Обновление информации о токене, включая название"""
        update_query = """
            UPDATE token_data
            SET token_name = %s, token_amount = %s, total_in_sol = %s
            WHERE wallet = %s AND token_address = %s
        """
        self.execute_write_query(update_query, params=(token_name, token_balance, total_in_sol, wallet, token_address))

    def save_new_token(self, wallet, token_address, token_name, token_balance, total_in_sol):
        """Добавление нового токена в базу с названием"""
        save_token_query = """
            INSERT INTO token_data (wallet, token_address, token_name, token_amount, total_in_sol)
            VALUES (%s, %s, %s, %s, %s)
        """
        self.execute_write_query(
            save_token_query,
            params=(wallet, token_address, token_name, token_balance, total_in_sol)
        )

    # Тут надо изменить hard удаление
    def remove_token(self, wallet, token_address):
        """Удаление токена из базы"""
        remove_token_query = "DELETE FROM token_data WHERE wallet = %s AND token_address = %s"
        self.execute_write_query(remove_token_query, params=(wallet, token_address))

    def get_tokens_for_wallet(self, wallet):
        """Получение всех токенов для кошелька"""
        get_tokens_query = "SELECT token_address FROM token_data WHERE wallet = %s"
        get_tokens_result = self.execute_read_many_query(get_tokens_query, params=(wallet,))
        return {row[0] for row in get_tokens_result}

    # ------------------------------------------------------------------------------------------------
    def get_wallets_by_token(self, token_address):
        """Получение всех кошельков, которые владеют указанным токеном"""
        get_wallets_query = """
            SELECT sol_wallet.wallet, token_data.total_in_sol
            FROM token_data
            JOIN sol_wallet ON sol_wallet.wallet = token_data.wallet
            WHERE token_data.token_address = %s
        """
        wallets_result: List[Tuple] = self.execute_read_many_query(get_wallets_query, params=(token_address,))
        return wallets_result

    def get_token_name_by_address(self, token_address):
        """Получение имени токена по его адресу"""
        get_token_query = "SELECT token_name FROM token_data WHERE token_address = %s"
        get_token_result = self.execute_read_one_query(get_token_query, params=(token_address,))
        return get_token_result[0] if get_token_result else None


    """Функции SQL для таблицы users"""

    def get_payment_status(self, user_id):
        """Метод для получения статуса оплаты пользователя по user_id"""
        status_query = 'SELECT payment_status FROM users WHERE user_id = %s'
        result_status = self.execute_read_one_query(status_query, params=(user_id,))
        return result_status[0] if result_status else None

    def update_payment_status(self, user_id, status):
        """Обновление статуса оплаты с записью даты"""
        payment_date = datetime.datetime.now()
        update_query = '''
                INSERT INTO users (user_id, payment_status, payment_date) 
                VALUES (%s, %s, %s) 
                ON CONFLICT(user_id) 
                DO UPDATE SET 
                    payment_status = EXCLUDED.payment_status, 
                    payment_date = EXCLUDED.payment_date;
            '''
        self.execute_write_query(update_query, params=(user_id, status, payment_date))

    def is_payment_valid(self, user_id):
        """Проверяет, действительна ли оплата (30 дней с момента оплаты)"""
        status_payment_query = 'SELECT payment_date FROM users WHERE user_id = %s'
        result_status_payment = self.execute_read_one_query(status_payment_query, params=(user_id,))

        if result_status_payment and result_status_payment[0]:
            payment_date = datetime.datetime.fromisoformat(str(result_status_payment[0]))
            time_diff = datetime.datetime.now() - payment_date
            return time_diff.total_seconds() <= 2592000
        return False

    def remove_expired_users(self):
        """Удаляет пользователей, чья оплата истекла более 30 дней назад"""
        expiration_date = datetime.datetime.now() - datetime.timedelta(days=30)
        remove_user = 'DELETE FROM users WHERE payment_date < %s'
        self.execute_write_query(remove_user, params=(expiration_date,))

    def get_notify_status(self, user_id):
        notify_status_query = "SELECT notify_status FROM users WHERE user_id = %s"
        result_notify_status = self.execute_read_one_query(notify_status_query, params=(user_id,))
        return result_notify_status[0] if result_notify_status else False

    def update_notify_status(self, user_id, status):
        update_query = "UPDATE users SET notify_status = %s WHERE user_id = %s"
        self.execute_write_query(update_query, params=(status, user_id))

    def get_users_with_notifications(self):
        not_notify_status_query = "SELECT user_id FROM users WHERE notify_status = TRUE"
        result_notify_status: List[Tuple] = self.execute_read_many_query(not_notify_status_query)
        return [row[0] for row in result_notify_status]


    """Транзакции"""
    # ОДНОВРЕМЕННО
    def add_transaction(self, wallet, token, amount_token, timestamp, operation_type):
        add_trans_query = """
            INSERT INTO infl_buys (wallet, token, amount_token, timestamp, operation_type) 
            VALUES (%s, %s, %s, to_timestamp(%s), %s)
        """
        self.execute_write_query(add_trans_query, params=(wallet, token, amount_token, timestamp, operation_type))

    # МЕТКАААААААА
    def delete_old_transaction(self):
        delete_query = """
            DELETE FROM infl_buys
            WHERE timestamp < NOW() - INTERVAL '1 day'
        """
        self.execute_write_query(delete_query)

    def get_tokens_with_time_for_wallet(self, wallet):
        """Получение всех токенов с их временем для кошелька"""
        get_tokens_query = "SELECT token, timestamp FROM infl_buys WHERE wallet = %s"
        result_tokens: List[Tuple] = self.execute_read_many_query(get_tokens_query, params=(wallet,))
        return {(row[0], row[1]) for row in result_tokens}

    def get_tokens_with_more_than_5_unique_wallets(self):
        """Запрос, который возвращает токены, купленные более чем 5 уникальными кошельками"""
        get_unique_tokens_query = """
            SELECT token 
            FROM infl_buys 
            GROUP BY token 
            HAVING COUNT(DISTINCT wallet) > 2
        """
        result_unique_tokens: List[Tuple] = self.execute_read_many_query(get_unique_tokens_query)
        return [row[0] for row in result_unique_tokens]

    def get_unique_wallets_for_token(self, token):
        """Запрос, который возвращает уникальные кошельки, купившие данный токен"""
        get_unique_wallets_query = """
            SELECT DISTINCT wallet 
            FROM infl_buys 
            WHERE token = %s
        """
        result_wallets: List[Tuple] = self.execute_read_many_query(get_unique_wallets_query, params=(token,))
        return [row[0] for row in result_wallets]

    def is_token_notified(self, token):
        """Проверка, был ли токен уже упомянут"""
        notified_query = "SELECT token FROM notified_tokens WHERE token = %s"
        return bool(self.execute_read_one_query(notified_query, params=(token,)))

    def add_notified_token(self, token):
        """Добавление токена в таблицу упомянутых"""
        add_notified_token_query ="""
            INSERT INTO notified_tokens (token) 
            VALUES (%s)
        """
        self.execute_write_query(add_notified_token_query, params=(token,))

    def add_or_update_row(self, wallet, pnl, wr):
        """Добавление или обновление записи для кошелька."""
        # Проверяем, существует ли кошелек
        check_wallet_query = "SELECT wallet FROM data_wallet WHERE wallet = %s"
        wallet_exists = self.execute_read_one_query(check_wallet_query, params=(wallet,))

        if wallet_exists:
            # Если кошелек уже существует, обновляем запись
            update_query = """
                UPDATE data_wallet
                SET pnl = %s, wr = %s
                WHERE wallet = %s
            """
            self.execute_write_query(update_query, params=(pnl, wr, wallet))
        else:
            # Если кошелька нет, добавляем новую запись
            insert_query = """
                INSERT INTO data_wallet (wallet, pnl, wr)
                VALUES (%s, %s, %s)
            """
            self.execute_write_query(insert_query, params=(wallet, pnl, wr))

    def get_data(self, wallet):
        """Получение pnl и wr для указанного кошелька."""
        query = "SELECT pnl, wr FROM data_wallet WHERE wallet = %s"
        result = self.execute_read_one_query(query, params=(wallet,))
        return result

    # <<<------------------------------------------------------------------------------------------------>>>

# Не изменял, тк у нас пнл и вр догружается файлом на сервер, раз в день (пока)
# А это как раз извлекает данные из подгружаемого файла
# class ImportDB:
#     def __init__(self, db_file):
#         """Инициализация класса с подключением к базе данных"""
#         self.connection = sqlite3.connect(db_file)
#         self.cursor = self.connection.cursor()
#
#
#
#     def get_data(self, wallet):
#         """Получение pnl и wr"""
#         with self.connection:
#             self.cursor.execute("SELECT pnl, wr FROM data_wallet WHERE wallet = ?", (wallet,))
#             result = self.cursor.fetchone()
#             if result is None:
#                 return None
#             return result
#
#     def close(self):
#         """Закрытие соединения с базой данных"""
#         self.connection.close()