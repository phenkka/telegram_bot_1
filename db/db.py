import string
from typing import Tuple, List

from psycopg2 import pool


class Database:
    def __init__(self, minconn, maxconn, dbname, user, password, host='localhost', port='5432'):
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

    def add_row(self, wallet, user, link):
        """Добавление нового кошелька"""
        exists_query = "SELECT EXISTS(SELECT 1 FROM sol_wallet WHERE wallet = %s);"
        exists_result: Tuple[bool] = self.execute_read_one_query(exists_query, params=(wallet,))
        if exists_result[0] is True:
            return False

        insert_query = """
            INSERT INTO sol_wallet(wallet, "user", link)
            VALUES (%s, %s, %s);
        """
        self.execute_write_query(insert_query, (wallet, user, link))
        return True

    def get_wallets(self):
        """Получение списка всех кошельков"""
        query = "SELECT wallet FROM sol_wallet;"
        result = self.execute_read_many_query(query)
        wallets = [row[0] for row in result]
        return wallets

    def check_row(self, wallet):
        """Проверка существования кошелька"""
        exists_query = "SELECT EXISTS(SELECT 1 FROM sol_wallet WHERE wallet = %s);"
        exists_result = self.execute_read_one_query(exists_query, params=(wallet,))
        return exists_result[0]

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

    def get_wallets_by_token(self, token_address):
        """Получение всех кошельков, которые владеют указанным токеном"""
        with self.connection:
            self.cursor.execute("""
                    SELECT sol_wallet.wallet, token_data.total_in_sol
                    FROM token_data
                    JOIN sol_wallet ON sol_wallet.wallet = token_data.wallet
                    WHERE token_data.token_address = %s
                """, (token_address,))
            return self.cursor.fetchall()

    def get_token_name_by_address(self, token_address):
        """Получение имени токена по его адресу"""
        get_token_query = "SELECT token_name FROM token_data WHERE token_address = %s"
        get_token_result = self.execute_read_one_query(get_token_query, params=(token_address,))
        return get_token_result[0]


    """Функции SQL для таблицы users"""

    def get_payment_status(self, user_id):
        """Метод для получения статуса оплаты пользователя по user_id"""
        self.cursor.execute('SELECT payment_status FROM users WHERE user_id = %s', (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def update_payment_status(self, user_id, status):
        """Обновление статуса оплаты с записью даты"""
        payment_date = datetime.datetime.now()
        self.cursor.execute('''INSERT INTO users (user_id, payment_status, payment_date) 
                                   VALUES (%s, %s, %s) 
                                   ON CONFLICT(user_id) 
                                   DO UPDATE SET payment_status = %s, payment_date = %s''',
                            (user_id, status, payment_date, status, payment_date))
        self.connection.commit()

    def is_payment_valid(self, user_id):
        """Проверяет, действительна ли оплата (30 дней с момента оплаты)"""
        self.cursor.execute('SELECT payment_date FROM users WHERE user_id = %s', (user_id,))
        result = self.cursor.fetchone()
        if result:
            payment_date = datetime.datetime.fromisoformat(result[0])
            return (datetime.datetime.now() - payment_date).seconds <= 2592000
        return False

    def remove_expired_users(self):
        """Удаляет пользователей, чья оплата истекла более 30 дней назад"""
        expiration_date = datetime.datetime.now() - datetime.timedelta(days=31)
        self.cursor.execute('DELETE FROM users WHERE payment_date < %s', (expiration_date,))

    def get_notify_status(self, user_id):
        self.cursor.execute("SELECT notify_status FROM users WHERE user_id = %s", (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result else False

    def update_notify_status(self, user_id, status):
        self.cursor.execute("UPDATE users SET notify_status = %s WHERE user_id = %s", (status, user_id))
        self.connection.commit()

    def get_users_with_notifications(self):
        self.cursor.execute("SELECT user_id FROM users WHERE notify_status = TRUE")
        users = [row[0] for row in self.cursor.fetchall()]
        return users

    """Транзакции"""

    # ОДНОВРЕМЕННО
    def add_transaction(self, wallet, token, amount_token, timestamp, operation_type):
        with self.connection:
            self.cursor.execute("""
                        INSERT INTO infl_buys (wallet, token, amount_token, timestamp, operation_type) 
                        VALUES (?, ?, ?, ?, ?)
                    """, (wallet, token, amount_token, timestamp, operation_type))

    # МЕТКАААААААА
    def delete_old_transaction(self):
        with self.connection:
            self.cursor.execute("""
                        DELETE FROM infl_buys
                        WHERE timestamp < datetime('now', '-1 day')
                    """)

    def get_tokens_for_wallet(self, wallet):
        """Получение всех токенов с их временем для кошелька"""
        with self.connection:
            self.cursor.execute("SELECT token, timestamp FROM infl_buys WHERE wallet = ?", (wallet,))
            # Создаем множество с уникальными комбинациями токенов и времени
            unique_tokens = {(row[0], row[1]) for row in self.cursor.fetchall()}
            return unique_tokens

    def get_tokens_with_more_than_5_unique_wallets(self):
        # Запрос, который возвращает токены, купленные более чем 5 уникальными кошельками
        self.cursor.execute("""
                    SELECT token 
                    FROM infl_buys 
                    GROUP BY token 
                    HAVING COUNT(DISTINCT wallet) > 2
                """)
        tokens = [row[0] for row in self.cursor.fetchall()]
        return tokens

    def get_unique_wallets_for_token(self, token):
        # Запрос, который возвращает уникальные кошельки (user_id), купившие данный токен
        self.cursor.execute("""
                    SELECT DISTINCT wallet 
                    FROM infl_buys 
                    WHERE token = ?
                """, (token,))
        wallets = [row[0] for row in self.cursor.fetchall()]
        return wallets

    def is_token_notified(self, token):
        """Проверка, был ли токен уже упомянут"""
        with self.connection:
            self.cursor.execute("""
                        SELECT token FROM notified_tokens WHERE token = ?
                    """, (token,))
            return self.cursor.fetchone() is not None

    def add_notified_token(self, token):
        """Добавление токена в таблицу упомянутых"""
        with self.connection:
            self.cursor.execute("""
                        INSERT INTO notified_tokens (token) VALUES (?)
                    """, (token,))

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
    # <<<------------------------------------------------------------------------------------------------>>>


class ImportDB:
    def __init__(self, db_file):
        """Инициализация класса с подключением к базе данных"""
        self.connection = sqlite3.connect(db_file)
        self.cursor = self.connection.cursor()

    def get_data(self, wallet):
        """Получение pnl и wr"""
        with self.connection:
            self.cursor.execute("SELECT pnl, wr FROM data_wallet WHERE wallet = ?", (wallet,))
            result = self.cursor.fetchone()
            if result is None:
                return None
            return result

    def close(self):
        """Закрытие соединения с базой данных"""
        self.connection.close()


class Transactions:
    def __init__(self, db_file):
        """Инициализация класса с подключением к базе данных"""
        self.connection = sqlite3.connect(db_file)
        self.cursor = self.connection.cursor()

    def create_table(self):
        """Создание таблицы для кошельков и токенов"""
        with self.connection:
            self.cursor.execute("""
                    CREATE TABLE IF NOT EXISTS infl_buys (
                        wallet TEXT,
                        token TEXT,
                        amount_token REAL,
                        timestamp TIMESTAMP,
                        operation_type TEXT
                    )
                """)
        with self.connection:
            self.cursor.execute("""
                    CREATE TABLE IF NOT EXISTS notified_tokens (
                        token TEXT PRIMARY KEY
                    )
                """)

    def close(self):
        """Закрытие соединения с базой данных"""
        self.connection.close()
