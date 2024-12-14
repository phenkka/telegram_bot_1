import unittest

from db.database import Database


def clean_db(db):
    db.execute_write_query("DELETE FROM token_data WHERE true;")
    db.execute_write_query("DELETE FROM sol_wallet WHERE true;")


def init_db():
    db = Database(minconn=1, maxconn=10, dbname='fabu-test', user='fabu', password='01234567')
    clean_db(db)
    return db


class MyTestCase(unittest.TestCase):
    def test_db_connection(self):
        db = init_db()
        conn = db.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1;")
                result = cursor.fetchall()
        finally:
            db.release_connection(conn)
        self.assertEqual(result, [(1,)])
        db.close_all_connections()

    def testAddRow(self):
        db = init_db()

        add_res = db.add_row(wallet='0xWALLET_ADDRESS_0', user=0, link='USER_LINK_0')
        self.assertTrue(add_res)
        add_res = db.add_row(wallet='0xWALLET_ADDRESS_0', user=0, link='USER_LINK_0')
        self.assertFalse(add_res)

    def test_get_wallets(self):
        db = init_db()

        db.add_row(wallet='0xWALLET_ADDRESS_0', user=0, link='USER_LINK_0')
        db.add_row(wallet='0xWALLET_ADDRESS_1', user=1, link='USER_LINK_1')
        db.add_row(wallet='0xWALLET_ADDRESS_2', user=2, link='USER_LINK_2')
        db.add_row(wallet='0xWALLET_ADDRESS_3', user=3, link='USER_LINK_3')
        wallets = db.get_wallets()
        self.assertEqual(4, wallets.__len__())
        self.assertTrue('0xWALLET_ADDRESS_0' in wallets)
        self.assertTrue('0xWALLET_ADDRESS_1' in wallets)
        self.assertTrue('0xWALLET_ADDRESS_2' in wallets)
        self.assertTrue('0xWALLET_ADDRESS_3' in wallets)

    def test_check_row(self):
        db = init_db()

        result_one = db.check_row('0xWALLET_ADDRESS_0')
        self.assertFalse(result_one)

        db.add_row(wallet='0xWALLET_ADDRESS_0', user=0, link='USER_LINK_0')
        result_two = db.check_row('0xWALLET_ADDRESS_0')
        self.assertTrue(result_two)

    def test_count_wallets(self):
        db = init_db()

        wallets_number = db.count_wallets(0)
        self.assertEqual(0, wallets_number)

        db.add_row(wallet='0xWALLET_ADDRESS_0', user=0, link='USER_LINK_0')
        db.add_row(wallet='0xWALLET_ADDRESS_1', user=0, link='USER_LINK_0')
        db.add_row(wallet='0xWALLET_ADDRESS_2', user=0, link='USER_LINK_0')
        db.add_row(wallet='0xWALLET_ADDRESS_3', user=0, link='USER_LINK_0')
        wallets_number = db.count_wallets(0)
        self.assertEqual(4, wallets_number)

    def test_check_infl(self):
        db = init_db()

        result_one = db.check_infl(0)
        self.assertFalse(result_one)

        db.add_row(wallet='0xWALLET_ADDRESS_0', user=0, link='USER_LINK_0')
        db.add_row(wallet='0xWALLET_ADDRESS_1', user=0, link='USER_LINK_0')
        result_two = db.check_infl(0)
        self.assertEqual([('0xWALLET_ADDRESS_0',), ('0xWALLET_ADDRESS_1',)], result_two)

    def test_get_influencers(self):
        db = init_db()

        db.add_row(wallet='0xWALLET_ADDRESS_0', user=0, link='USER_LINK_0')
        db.add_row(wallet='0xWALLET_ADDRESS_1', user=1, link='USER_LINK_1')
        db.add_row(wallet='0xWALLET_ADDRESS_2', user=2, link='USER_LINK_2')
        db.add_row(wallet='0xWALLET_ADDRESS_3', user=3, link='USER_LINK_3')
        influencers = db.get_influencers()
        self.assertEqual(4, influencers.__len__())
        self.assertTrue(0 in influencers)
        self.assertTrue(1 in influencers)
        self.assertTrue(2 in influencers)
        self.assertTrue(3 in influencers)

    def test_get_influencer(self):
        db = init_db()

        db.add_row(wallet='0xWALLET_ADDRESS_0', user=0, link='USER_LINK_0')
        db.add_row(wallet='0xWALLET_ADDRESS_1', user=1, link='USER_LINK_1')
        db.add_row(wallet='0xWALLET_ADDRESS_2', user=2, link='USER_LINK_2')
        db.add_row(wallet='0xWALLET_ADDRESS_3', user=3, link='USER_LINK_3')
        influencer = db.get_influencer('0xWALLET_ADDRESS_1')
        self.assertEqual((1, 'USER_LINK_1'), influencer)

    def test_save_and_get_tokens(self):
        db = init_db()

        db.add_row(wallet='0xWALLET_ADDRESS_0', user=0, link='USER_LINK_0')

        db.save_new_token('0xWALLET_ADDRESS_0', '0xTOKEN_ADDRESS', 'TOKEN_NAME', 100, 2)
        token_name = db.get_token_name_by_address('0xTOKEN_ADDRESS')
        self.assertEqual('TOKEN_NAME', token_name)

    def test_update_token(self):
        db = init_db()

        db.add_row(wallet='0xWALLET_ADDRESS_0', user=0, link='USER_LINK_0')
        db.save_new_token('0xWALLET_ADDRESS_0', '0xTOKEN_ADDRESS', 'TOKEN_NAME', 100, 2)

        db.update_token_info('0xWALLET_ADDRESS_0', '0xTOKEN_ADDRESS', 'TOKEN_NAME', 200, 4)

    # def test_get_tokens_for_wallet(self):
    #     db = init_db()
    #
    #     db.add_row(wallet='0xWALLET_ADDRESS_0', user=0, link='USER_LINK_0')
    #     db.save_new_token('0xWALLET_ADDRESS_0', '0xTOKEN_ADDRESS_0', 'TOKEN_NAME_0', 100, 2)
    #     db.save_new_token('0xWALLET_ADDRESS_0', '0xTOKEN_ADDRESS_1', 'TOKEN_NAME_1', 200, 4)
    #     db.save_new_token('0xWALLET_ADDRESS_0', '0xTOKEN_ADDRESS_2', 'TOKEN_NAME_2', 500, 5)
    #     db.save_new_token('0xWALLET_ADDRESS_0', '0xTOKEN_ADDRESS_3', 'TOKEN_NAME_3', 500, 5)
    #
    #     tokens = db.get_tokens_for_wallet('0xWALLET_ADDRESS_0')
    #     self.assertEqual(4, tokens.__len__())
    #     self.assertTrue('0xTOKEN_ADDRESS_0' in tokens)
    #     self.assertTrue('0xTOKEN_ADDRESS_1' in tokens)
    #     self.assertTrue('0xTOKEN_ADDRESS_2' in tokens)
    #     self.assertTrue('0xTOKEN_ADDRESS_3' in tokens)


if __name__ == '__main__':
    unittest.main()
