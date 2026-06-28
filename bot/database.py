import aiomysql
from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME


class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        self.pool = await aiomysql.create_pool(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            db=DB_NAME,
            charset='utf8mb4',
            autocommit=True,
            minsize=5,
            maxsize=20
        )

    async def close(self):
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()

    async def execute(self, query: str, params: tuple = None):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, params)
                return cur.lastrowid

    async def fetchone(self, query: str, params: tuple = None):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(query, params)
                return await cur.fetchone()

    async def fetchall(self, query: str, params: tuple = None):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(query, params)
                return await cur.fetchall()

    # ============ USER METHODS ============

    async def get_user(self, user_id: int):
        return await self.fetchone("SELECT * FROM users WHERE id = %s", (user_id,))

    async def create_user(self, user_id: int):
        await self.execute(
            "INSERT IGNORE INTO users (id, registration_step) VALUES (%s, 'phone')",
            (user_id,)
        )

    async def update_user(self, user_id: int, **kwargs):
        if not kwargs:
            return
        set_clause = ", ".join(f"{k} = %s" for k in kwargs.keys())
        values = list(kwargs.values()) + [user_id]
        await self.execute(
            f"UPDATE users SET {set_clause} WHERE id = %s",
            tuple(values)
        )

    # ============ PHOTO METHODS ============

    async def add_photo(self, user_id: int, file_id: str, order: int):
        await self.execute(
            "INSERT INTO user_photos (user_id, file_id, photo_order) VALUES (%s, %s, %s)",
            (user_id, file_id, order)
        )

    async def get_photos(self, user_id: int):
        return await self.fetchall(
            "SELECT * FROM user_photos WHERE user_id = %s ORDER BY photo_order",
            (user_id,)
        )

    async def delete_photos(self, user_id: int):
        await self.execute("DELETE FROM user_photos WHERE user_id = %s", (user_id,))

    # ============ INTEREST METHODS ============

    async def add_interest(self, user_id: int, interest: str):
        await self.execute(
            "INSERT INTO user_interests (user_id, interest) VALUES (%s, %s)",
            (user_id, interest)
        )

    async def get_interests(self, user_id: int):
        rows = await self.fetchall(
            "SELECT interest FROM user_interests WHERE user_id = %s",
            (user_id,)
        )
        return [r['interest'] for r in rows]

    async def delete_interests(self, user_id: int):
        await self.execute("DELETE FROM user_interests WHERE user_id = %s", (user_id,))

    # ============ VERIFICATION METHODS ============

    async def create_verification(self, user_id: int, video_file_id: str):
        await self.execute(
            "INSERT INTO verifications (user_id, video_file_id) VALUES (%s, %s)",
            (user_id, video_file_id)
        )

    async def get_pending_verifications(self):
        return await self.fetchall(
            "SELECT v.*, u.name FROM verifications v "
            "JOIN users u ON v.user_id = u.id "
            "WHERE v.status = 'pending' ORDER BY v.created_at"
        )

    async def update_verification(self, verification_id: int, status: str, admin_id: int):
        await self.execute(
            "UPDATE verifications SET status = %s, reviewed_by = %s, reviewed_at = NOW() "
            "WHERE id = %s",
            (status, admin_id, verification_id)
        )

    # ============ LIKE/REJECT METHODS ============

    async def add_like(self, from_id: int, to_id: int):
        await self.execute(
            "INSERT IGNORE INTO likes (from_user_id, to_user_id) VALUES (%s, %s)",
            (from_id, to_id)
        )

    async def check_like(self, from_id: int, to_id: int):
        result = await self.fetchone(
            "SELECT id FROM likes WHERE from_user_id = %s AND to_user_id = %s",
            (from_id, to_id)
        )
        return result is not None

    async def add_reject(self, from_id: int, to_id: int):
        await self.execute(
            "INSERT IGNORE INTO rejects (from_user_id, to_user_id) VALUES (%s, %s)",
            (from_id, to_id)
        )

    # ============ MATCH METHODS ============

    async def create_match(self, user1_id: int, user2_id: int):
        u1, u2 = min(user1_id, user2_id), max(user1_id, user2_id)
        await self.execute(
            "INSERT IGNORE INTO matches (user1_id, user2_id) VALUES (%s, %s)",
            (u1, u2)
        )

    async def check_match(self, user1_id: int, user2_id: int):
        u1, u2 = min(user1_id, user2_id), max(user1_id, user2_id)
        result = await self.fetchone(
            "SELECT id FROM matches WHERE user1_id = %s AND user2_id = %s",
            (u1, u2)
        )
        return result is not None

    async def get_matches(self, user_id: int):
        return await self.fetchall(
            "SELECT u.* FROM matches m "
            "JOIN users u ON (u.id = m.user1_id OR u.id = m.user2_id) "
            "WHERE (m.user1_id = %s OR m.user2_id = %s) AND u.id != %s",
            (user_id, user_id, user_id)
        )

    # ============ DISCOVERY METHODS ============

    async def get_profiles_for_user(self, user_id: int, gender: str, min_age: int, max_age: int, limit: int):
        return await self.fetchall(
            "SELECT u.* FROM users u "
            "WHERE u.id != %s "
            "AND u.gender = %s "
            "AND u.age BETWEEN %s AND %s "
            "AND u.is_verified = 1 "
            "AND u.is_active = 1 "
            "AND u.is_banned = 0 "
            "AND u.id NOT IN (SELECT to_user_id FROM likes WHERE from_user_id = %s) "
            "AND u.id NOT IN (SELECT to_user_id FROM rejects WHERE from_user_id = %s) "
            "ORDER BY RAND() LIMIT %s",
            (user_id, gender, min_age, max_age, user_id, user_id, limit)
        )

    # ============ DAILY USAGE METHODS ============

    async def get_daily_usage(self, user_id: int):
        result = await self.fetchone(
            "SELECT * FROM daily_usage WHERE user_id = %s AND usage_date = CURDATE()",
            (user_id,)
        )
        if not result:
            await self.execute(
                "INSERT INTO daily_usage (user_id, usage_date) VALUES (%s, CURDATE())",
                (user_id,)
            )
            return {'views_count': 0, 'likes_count': 0}
        return result

    async def increment_views(self, user_id: int):
        await self.execute(
            "INSERT INTO daily_usage (user_id, usage_date, views_count) "
            "VALUES (%s, CURDATE(), 1) "
            "ON DUPLICATE KEY UPDATE views_count = views_count + 1",
            (user_id,)
        )

    async def increment_likes(self, user_id: int):
        await self.execute(
            "INSERT INTO daily_usage (user_id, usage_date, likes_count) "
            "VALUES (%s, CURDATE(), 1) "
            "ON DUPLICATE KEY UPDATE likes_count = likes_count + 1",
            (user_id,)
        )

    # ============ COIN METHODS ============

    async def add_coins(self, user_id: int, amount: int, tx_type: str, description: str = None):
        await self.execute(
            "UPDATE users SET coins = coins + %s WHERE id = %s",
            (amount, user_id)
        )
        await self.execute(
            "INSERT INTO coin_transactions (user_id, amount, transaction_type, description) "
            "VALUES (%s, %s, %s, %s)",
            (user_id, amount, tx_type, description)
        )

    async def spend_coins(self, user_id: int, amount: int, description: str = None):
        user = await self.get_user(user_id)
        if user['coins'] < amount:
            return False
        await self.execute(
            "UPDATE users SET coins = coins - %s WHERE id = %s",
            (amount, user_id)
        )
        await self.execute(
            "INSERT INTO coin_transactions (user_id, amount, transaction_type, description) "
            "VALUES (%s, %s, 'spend', %s)",
            (user_id, -amount, description)
        )
        return True

    # ============ WHO LIKED ME ============

    async def get_who_liked_me(self, user_id: int):
        return await self.fetchall(
            "SELECT u.* FROM likes l "
            "JOIN users u ON l.from_user_id = u.id "
            "WHERE l.to_user_id = %s "
            "AND l.from_user_id NOT IN ("
            "  SELECT from_user_id FROM likes WHERE to_user_id = l.from_user_id AND from_user_id = %s"
            ") "
            "AND l.from_user_id NOT IN ("
            "  SELECT to_user_id FROM rejects WHERE from_user_id = %s"
            ")",
            (user_id, user_id, user_id)
        )

    # ============ MESSAGE METHODS ============

    async def send_message(self, from_id: int, to_id: int, text: str, msg_type: str = 'text', file_id: str = None):
        await self.execute(
            "INSERT INTO messages (from_user_id, to_user_id, message_text, message_type, file_id) "
            "VALUES (%s, %s, %s, %s, %s)",
            (from_id, to_id, text, msg_type, file_id)
        )

    async def send_direct_message(self, from_id: int, to_id: int, text: str, cost: int):
        await self.execute(
            "INSERT INTO direct_messages (from_user_id, to_user_id, message_text, coins_spent) "
            "VALUES (%s, %s, %s, %s)",
            (from_id, to_id, text, cost)
        )


db = Database()
