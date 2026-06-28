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

    async def create_user(self, user_id: int, referral_code: str = None):
        import uuid
        code = str(uuid.uuid4())[:8]
        await self.execute(
            "INSERT IGNORE INTO users (id, registration_step, referral_code) VALUES (%s, 'phone', %s)",
            (user_id, code)
        )
        return code

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
        return await self.execute(
            "INSERT INTO verifications (user_id, video_file_id) VALUES (%s, %s)",
            (user_id, video_file_id)
        )

    async def get_pending_verifications(self):
        return await self.fetchall(
            "SELECT v.*, u.name FROM verifications v "
            "JOIN users u ON v.user_id = u.id "
            "WHERE v.status = 'pending' ORDER BY v.created_at"
        )

    async def update_verification(self, verification_id: int, status: str, admin_id: int, reason: str = None):
        await self.execute(
            "UPDATE verifications SET status = %s, reviewed_by = %s, reviewed_at = NOW(), "
            "rejection_reason = %s WHERE id = %s",
            (status, admin_id, reason, verification_id)
        )

    # ============ LIKE/REJECT METHODS ============

    async def add_like(self, from_id: int, to_id: int):
        await self.execute(
            "INSERT IGNORE INTO likes (from_user_id, to_user_id) VALUES (%s, %s)",
            (from_id, to_id)
        )
        await self.execute(
            "UPDATE users SET total_likes_sent = total_likes_sent + 1 WHERE id = %s", (from_id,)
        )
        await self.execute(
            "UPDATE users SET total_likes_received = total_likes_received + 1 WHERE id = %s", (to_id,)
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
            "SELECT id FROM matches WHERE user1_id = %s AND user2_id = %s AND is_active = 1",
            (u1, u2)
        )
        return result is not None

    async def unmatch(self, user1_id: int, user2_id: int):
        u1, u2 = min(user1_id, user2_id), max(user1_id, user2_id)
        await self.execute(
            "UPDATE matches SET is_active = 0 WHERE user1_id = %s AND user2_id = %s",
            (u1, u2)
        )

    async def get_matches(self, user_id: int):
        return await self.fetchall(
            "SELECT u.* FROM matches m "
            "JOIN users u ON (u.id = m.user1_id OR u.id = m.user2_id) "
            "WHERE (m.user1_id = %s OR m.user2_id = %s) AND u.id != %s AND m.is_active = 1",
            (user_id, user_id, user_id)
        )

    # ============ CHAT REQUEST METHODS ============

    async def create_chat_request(self, from_id: int, to_id: int):
        await self.execute(
            "INSERT INTO chat_requests (from_user_id, to_user_id) VALUES (%s, %s)",
            (from_id, to_id)
        )

    async def update_chat_request(self, request_id: int, status: str):
        await self.execute(
            "UPDATE chat_requests SET status = %s WHERE id = %s",
            (status, request_id)
        )

    async def check_chat_accepted(self, user1_id: int, user2_id: int):
        result = await self.fetchone(
            "SELECT id FROM chat_requests WHERE "
            "((from_user_id = %s AND to_user_id = %s) OR (from_user_id = %s AND to_user_id = %s)) "
            "AND status = 'accepted'",
            (user1_id, user2_id, user2_id, user1_id)
        )
        return result is not None

    # ============ DISCOVERY METHODS ============

    async def get_profiles_for_user(self, user_id: int, gender: str = None,
                                     min_age: int = None, max_age: int = None,
                                     province: str = None, city: str = None, limit: int = 1):
        conditions = [
            "u.id != %s",
            "u.registration_step = 'completed'",
            "u.is_active = 1",
            "u.is_banned = 0",
            "u.id NOT IN (SELECT to_user_id FROM likes WHERE from_user_id = %s)",
            "u.id NOT IN (SELECT to_user_id FROM rejects WHERE from_user_id = %s)",
            "u.id NOT IN (SELECT blocked_id FROM blocks WHERE blocker_id = %s)",
            "u.id NOT IN (SELECT blocker_id FROM blocks WHERE blocked_id = %s)",
        ]
        params = [user_id, user_id, user_id, user_id, user_id]

        if gender:
            conditions.append("u.gender = %s")
            params.append(gender)

        if min_age is not None and max_age is not None:
            conditions.append("u.age BETWEEN %s AND %s")
            params.extend([min_age, max_age])

        if province:
            conditions.append("u.province = %s")
            params.append(province)

        if city:
            conditions.append("u.city = %s")
            params.append(city)

        params.append(limit)
        where = " AND ".join(conditions)

        return await self.fetchall(
            f"SELECT u.* FROM users u WHERE {where} ORDER BY RAND() LIMIT %s",
            tuple(params)
        )

    # ============ SEARCH HISTORY (for premium back) ============

    async def add_search_history(self, user_id: int, viewed_id: int):
        await self.execute(
            "INSERT INTO search_history (user_id, viewed_user_id) VALUES (%s, %s)",
            (user_id, viewed_id)
        )

    async def get_previous_profile(self, user_id: int):
        result = await self.fetchone(
            "SELECT viewed_user_id FROM search_history "
            "WHERE user_id = %s ORDER BY id DESC LIMIT 1 OFFSET 1",
            (user_id,)
        )
        if result:
            return await self.get_user(result['viewed_user_id'])
        return None

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
        await self.execute(
            "UPDATE users SET total_views_sent = total_views_sent + 1 WHERE id = %s", (user_id,)
        )

    async def increment_views_received(self, target_id: int):
        await self.execute(
            "UPDATE users SET total_views_received = total_views_received + 1 WHERE id = %s", (target_id,)
        )

    async def increment_likes(self, user_id: int):
        await self.execute(
            "INSERT INTO daily_usage (user_id, usage_date, likes_count) "
            "VALUES (%s, CURDATE(), 1) "
            "ON DUPLICATE KEY UPDATE likes_count = likes_count + 1",
            (user_id,)
        )

    # ============ DIAMOND METHODS ============

    async def add_diamonds(self, user_id: int, amount: int, tx_type: str, description: str = None):
        await self.execute(
            "UPDATE users SET diamonds = diamonds + %s WHERE id = %s",
            (amount, user_id)
        )
        await self.execute(
            "INSERT INTO diamond_transactions (user_id, amount, transaction_type, description) "
            "VALUES (%s, %s, %s, %s)",
            (user_id, amount, tx_type, description)
        )

    async def spend_diamonds(self, user_id: int, amount: int, description: str = None):
        user = await self.get_user(user_id)
        if user['diamonds'] < amount:
            return False
        await self.execute(
            "UPDATE users SET diamonds = diamonds - %s WHERE id = %s",
            (amount, user_id)
        )
        await self.execute(
            "INSERT INTO diamond_transactions (user_id, amount, transaction_type, description) "
            "VALUES (%s, %s, 'spend', %s)",
            (user_id, -amount, description)
        )
        return True

    # ============ DAILY CLAIM & STREAKS ============

    async def claim_daily_diamond(self, user_id: int):
        user = await self.get_user(user_id)
        from datetime import date
        today = date.today()

        if user['last_daily_claim'] and user['last_daily_claim'] == today:
            return False

        await self.execute(
            "UPDATE users SET last_daily_claim = CURDATE() WHERE id = %s", (user_id,)
        )
        await self.add_diamonds(user_id, 1, 'daily', 'الماس رایگان روزانه')
        return True

    async def update_streak(self, user_id: int):
        from datetime import date, timedelta
        user = await self.get_user(user_id)
        today = date.today()

        if user['last_active_date'] == today:
            return user['streak_days']

        if user['last_active_date'] == today - timedelta(days=1):
            new_streak = user['streak_days'] + 1
        else:
            new_streak = 1

        await self.execute(
            "UPDATE users SET streak_days = %s, last_active_date = CURDATE() WHERE id = %s",
            (new_streak, user_id)
        )
        return new_streak

    async def claim_streak_reward(self, user_id: int, streak_type: str):
        user = await self.get_user(user_id)
        rewards = {'3': (3, 10, 'streak_3_claimed'), '7': (7, 30, 'streak_7_claimed'), '30': (30, 70, 'streak_30_claimed')}

        if streak_type not in rewards:
            return False, "نوع نامعتبر"

        days_needed, amount, claimed_field = rewards[streak_type]

        if user[claimed_field]:
            return False, "قبلاً دریافت کردی"

        if user['streak_days'] < days_needed:
            return False, f"باید {days_needed} روز متوالی بیای"

        await self.execute(f"UPDATE users SET {claimed_field} = 1 WHERE id = %s", (user_id,))
        await self.add_diamonds(user_id, amount, 'streak', f'جایزه {days_needed} روز متوالی')
        return True, f"{amount} الماس دریافت کردی!"

    # ============ REFERRAL METHODS ============

    async def process_referral(self, new_user_id: int, referrer_id: int):
        await self.execute(
            "UPDATE users SET referred_by = %s WHERE id = %s",
            (referrer_id, new_user_id)
        )
        await self.execute(
            "INSERT INTO referrals (referrer_id, referred_id) VALUES (%s, %s)",
            (referrer_id, new_user_id)
        )
        from config import REFERRAL_BONUS
        await self.add_diamonds(referrer_id, REFERRAL_BONUS, 'referral', f'دعوت کاربر جدید')

    async def get_referral_count(self, user_id: int):
        result = await self.fetchone(
            "SELECT COUNT(*) as cnt FROM referrals WHERE referrer_id = %s", (user_id,)
        )
        return result['cnt'] if result else 0

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
            "INSERT INTO direct_messages (from_user_id, to_user_id, message_text, diamonds_spent) "
            "VALUES (%s, %s, %s, %s)",
            (from_id, to_id, text, cost)
        )

    # ============ DELETE USER ============

    async def delete_user(self, user_id: int):
        await self.execute("DELETE FROM user_photos WHERE user_id = %s", (user_id,))
        await self.execute("DELETE FROM user_interests WHERE user_id = %s", (user_id,))
        await self.execute("DELETE FROM likes WHERE from_user_id = %s OR to_user_id = %s", (user_id, user_id))
        await self.execute("DELETE FROM rejects WHERE from_user_id = %s OR to_user_id = %s", (user_id, user_id))
        await self.execute("DELETE FROM matches WHERE user1_id = %s OR user2_id = %s", (user_id, user_id))
        await self.execute("DELETE FROM chat_requests WHERE from_user_id = %s OR to_user_id = %s", (user_id, user_id))
        await self.execute("DELETE FROM direct_messages WHERE from_user_id = %s OR to_user_id = %s", (user_id, user_id))
        await self.execute("DELETE FROM messages WHERE from_user_id = %s OR to_user_id = %s", (user_id, user_id))
        await self.execute("DELETE FROM diamond_transactions WHERE user_id = %s", (user_id,))
        await self.execute("DELETE FROM search_history WHERE user_id = %s", (user_id,))
        await self.execute("DELETE FROM daily_usage WHERE user_id = %s", (user_id,))
        await self.execute("DELETE FROM verifications WHERE user_id = %s", (user_id,))
        await self.execute("DELETE FROM referrals WHERE referrer_id = %s OR referred_id = %s", (user_id, user_id))
        await self.execute("DELETE FROM blocks WHERE blocker_id = %s OR blocked_id = %s", (user_id, user_id))
        await self.execute("DELETE FROM diamond_tasks WHERE user_id = %s", (user_id,))
        await self.execute("DELETE FROM users WHERE id = %s", (user_id,))

    # ============ STATS ============

    async def get_attractiveness(self, user_id: int):
        user = await self.get_user(user_id)
        views = user['total_views_received'] or 0
        likes = user['total_likes_received'] or 0
        if views == 0:
            return 0, 0, 0
        percent = round((likes / views) * 100)
        return views, likes, percent

    async def get_pickiness(self, user_id: int):
        user = await self.get_user(user_id)
        views = user['total_views_sent'] or 0
        likes = user['total_likes_sent'] or 0
        if views == 0:
            return 0, 0, 0
        percent = round((likes / views) * 100)
        return views, likes, percent


db = Database()
