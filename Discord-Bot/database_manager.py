import sqlite3
from datetime import datetime
from urllib.parse import urlparse

class DatabaseManager:
    def __init__(self, db_path='data/bot_database.db'):
        self.connection = sqlite3.connect(db_path)
        self.create_tables()

    def create_tables(self):
        with self.connection:
            self.connection.execute('''
                CREATE TABLE IF NOT EXISTS admins (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    rep INTEGER DEFAULT 300,
                    like_count INTEGER DEFAULT 0,
                    total_duration INTEGER DEFAULT 0,
                    steam_id TEXT DEFAULT 0,
                    old_duration INTEGER DEFAULT 1,
                    is_active INTEGER
                )
            ''')
            self.connection.execute('''
                CREATE TABLE IF NOT EXISTS admin_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    start_time TEXT,
                    end_time TEXT
                )
            ''')
            self.connection.execute('''
                CREATE TABLE IF NOT EXISTS admin_check_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    start_time TEXT,
                    end_time TEXT
                )
            ''')
            self.connection.execute('''
                CREATE TABLE IF NOT EXISTS likes (
                    user_id TEXT PRIMARY KEY,
                    last_like_time TEXT
                )
            ''')
            self.connection.execute('''
                CREATE TABLE IF NOT EXISTS whitelist (
                    url TEXT PRIMARY KEY
                )
            ''')
            self.connection.execute('''
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    steam_id TEXT,
                    data TEXT,
                    user_confirmation INTEGER,
                    admin_confirmation INTEGER
                )
            ''')
            self.connection.execute('''
                CREATE TABLE IF NOT EXISTS checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    data TEXT
                )
            ''')

    def update_admin_old_duration(self, user_id, duration):
        with self.connection:
            self.connection.execute('''
                UPDATE admins
                SET old_duration = old_duration + ?
                WHERE user_id = ?
            ''', (duration, user_id))

    def update_admin_steam_id(self, user_id, steam_id):
        self.add_admin(user_id)
        with self.connection:
            self.connection.execute('''
                UPDATE admins
                SET steam_id = ?
                WHERE user_id = ?
            ''', (steam_id, user_id))

    def remove_duplicates_keep_max_like_count(self):
        with self.connection:
            # Удаляем все дубликаты, оставляя только запись с максимальным like_count для каждого user_id
            self.connection.execute('''
                DELETE FROM admins
                WHERE rowid NOT IN (
                    SELECT rowid
                    FROM (
                        SELECT rowid, user_id, MAX(like_count) AS max_like_count
                        FROM admins
                        GROUP BY user_id
                    ) sub
                    WHERE admins.user_id = sub.user_id AND admins.like_count = sub.max_like_count
                )
            ''')

    def get_all_admin_ids(self):
        with self.connection:
            cursor = self.connection.execute('''
                SELECT user_id FROM admins
            ''')
            return [row[0] for row in cursor.fetchall()]

    def get_all_admins(self):
        with self.connection:
            cursor = self.connection.execute('''
                SELECT * FROM admins
            ''')
            return cursor.fetchall()

    def get_admin_info(self, user_id):
        with self.connection:
            cursor = self.connection.execute('''
                SELECT * FROM admins WHERE user_id = ?
            ''', (user_id,))
            return cursor.fetchone()

    def add_admin(self, user_id):
        ids = self.get_all_admin_ids()
        if user_id not in ids:
            with self.connection:
                self.connection.execute('''
                    INSERT OR IGNORE INTO admins (user_id, rep, like_count, total_duration, steam_id, old_duration, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (str(user_id), 300,0,0,0,0,1))

    def get_last_check_session(self, user_id):
        with self.connection:
            cursor = self.connection.execute('''
                SELECT start_time, end_time FROM admin_check_sessions
                WHERE user_id = ?
                ORDER BY start_time DESC
                LIMIT 1
            ''', (user_id,))
            result = cursor.fetchone()
            if result:
                return {'start_time': result[0], 'end_time': result[1]}
            return None

    def update_admin_rep(self, user_id, rep_change):
        self.add_admin(user_id)
        with self.connection:
            self.connection.execute('''
                UPDATE admins
                SET rep = rep + ?
                WHERE user_id = ?
            ''', (rep_change, user_id))

    def update_admin_rep_multy(self, user_id, multy):
        self.add_admin(user_id)
        with self.connection:
            # Получаем текущее значение репутации
            current_rep = self.connection.execute('''
                SELECT rep FROM admins WHERE user_id = ?
            ''', (user_id,)).fetchone()[0]

            # Вычисляем новую репутацию, но не ниже 300
            new_rep = max(current_rep * multy, 300)

            # Обновляем значение репутации
            self.connection.execute('''
                UPDATE admins
                SET rep = ?
                WHERE user_id = ?
            ''', (new_rep, user_id))

    def get_admin_rep(self, user_id):
        with self.connection:
            cursor = self.connection.execute('''
                SELECT rep FROM admins WHERE user_id = ?
            ''', (user_id,))
            result = cursor.fetchone()
            return result[0] if result else None

    def update_admin_total_duration(self, user_id, duration):
        with self.connection:
            self.connection.execute('''
                UPDATE admins
                SET total_duration = total_duration + ?
                WHERE user_id = ?
            ''', (duration, user_id))

    def del_admin(self, user_id):
        with self.connection:
            self.connection.execute('''
                DELETE FROM admins
                WHERE user_id = ?
            ''', (user_id, ))
            self.connection.execute('''
                DELETE FROM admin_sessions
                WHERE user_id = ?
            ''', (user_id, ))
            self.connection.execute('''
                DELETE FROM admin_check_sessions
                WHERE user_id = ?
            ''', (user_id, ))

    def clear_admin(self, user_id):
        with self.connection:
            self.connection.execute('''
                UPDATE admins
                SET total_duration = 0,
                like_count = 0
                WHERE user_id = ?
            ''', (user_id, ))
            self.connection.execute('''
                DELETE FROM admins
                WHERE steam_id = 0 AND user_id = ?
            ''', (user_id, ))
            self.connection.execute('''
                DELETE FROM admin_sessions
                WHERE user_id = ?
            ''', (user_id, ))
            self.connection.execute('''
                DELETE FROM admin_check_sessions
                WHERE user_id = ?
            ''', (user_id, ))

    def get_active_check_session_time(self, user_id):
        with self.connection:
            cursor = self.connection.execute('''
                SELECT start_time FROM admin_check_sessions
                WHERE user_id = ? AND end_time IS NULL
            ''', (user_id,))
            result = cursor.fetchone()
            if result is not None:
                start_time = datetime.fromisoformat(result[0])
                duration_seconds = (datetime.now() - start_time).total_seconds()
                return duration_seconds
            return None

    def end_admin_check_session(self, user_id):
        with self.connection:
            self.connection.execute('''
                UPDATE admin_check_sessions
                SET end_time = ?
                WHERE user_id = ? AND end_time IS NULL
            ''', (datetime.now().isoformat(), user_id))

    def create_admin_check_session(self, user_id):
        with self.connection:
            self.connection.execute('''
                INSERT INTO admin_check_sessions (user_id, start_time, end_time)
                VALUES (?, ?, ?)
            ''', (user_id, datetime.now().isoformat(), None))

    def add_check(self, user_id):
        with self.connection:
            self.connection.execute('''
                INSERT INTO checks (user_id, data)
                VALUES (?, ?)
            ''', (user_id, datetime.now().isoformat()))

    def add_admin_session(self, user_id):
        self.add_admin(user_id)
        with self.connection:
            self.connection.execute('''
                INSERT INTO admin_sessions (user_id, start_time)
                VALUES (?, ?)
            ''', (user_id, datetime.now().isoformat()))

    def get_active_session_time(self, user_id):
        with self.connection:
            cursor = self.connection.execute('''
                SELECT start_time FROM admin_sessions
                WHERE user_id = ? AND end_time IS NULL
            ''', (user_id,))
            result = cursor.fetchone()
            if result is not None:
                start_time = datetime.fromisoformat(result[0])
                duration_seconds = (datetime.now() - start_time).total_seconds()
                return duration_seconds
            return 0  # Возвращаем 0, если активной сессии нет

    def get_current_status(self, user_id):
        cursor = self.connection.execute('''
            SELECT COUNT(*) FROM admin_sessions
            WHERE user_id = ? AND end_time IS NULL
        ''', (user_id,))
        count = cursor.fetchone()[0]
        return 1 if count > 0 else 0

    def get_working_admins(self):
        cursor = self.connection.execute('''
            SELECT user_id FROM admin_sessions
            WHERE end_time IS NULL
        ''')
        return [row[0] for row in cursor.fetchall()]

    def end_admin_session(self, user_id):
        with self.connection:
            self.connection.execute('''
                UPDATE admin_sessions
                SET end_time = ?
                WHERE user_id = ? AND end_time IS NULL
            ''', (datetime.now().isoformat(), user_id))

    def get_all_sessions(self):
        cursor = self.connection.execute('''
            SELECT user_id, start_time, end_time FROM admin_sessions
        ''')
        sessions = {}
        for row in cursor.fetchall():
            user_id = row[0]
            start_time = row[1]
            end_time = row[2]
            if user_id not in sessions:
                sessions[user_id] = []
            sessions[user_id].append({'start_time': start_time, 'end_time': end_time})
        return sessions

    def update_total_duration(self, user_id, duration):
        with self.connection:
            self.connection.execute('''
                UPDATE admins
                SET total_duration = ?
                WHERE user_id = ?
            ''', (duration, user_id))

    def get_total_duration_for_admin_sessions(self):
        sessions = self.get_all_sessions()
        total_durations = {}
        for user_id, session_list in sessions.items():
            total_duration = sum(self.get_session_duration(session) for session in session_list)
            total_durations[user_id] = total_duration
        return total_durations

    def get_session_duration(self, session):
        start_time = datetime.fromisoformat(session['start_time'])
        end_time = datetime.fromisoformat(session['end_time']) if session['end_time'] else datetime.now()
        duration = end_time - start_time
        return int(duration.total_seconds())

    def get_last_like_time(self, user_id):
        cursor = self.connection.execute('''
            SELECT last_like_time FROM likes WHERE user_id = ?
        ''', (user_id,))
        result = cursor.fetchone()
        return result[0] if result else None

    def get_all_like_times(self):
        cursor = self.connection.execute('''
            SELECT user_id, last_like_time FROM likes
        ''')
        like_times = {}
        for row in cursor.fetchall():
            user_id = row[0]
            last_like_time = row[1]
            like_times[user_id] = last_like_time
        return like_times

    def update_like_time(self, user_id):
        with self.connection:
            self.add_admin(user_id)
            self.connection.execute('''
                UPDATE admins
                SET like_count = like_count + 1
                WHERE user_id = ?
            ''', (user_id,))
            self.connection.execute('''
                INSERT OR REPLACE INTO likes (user_id, last_like_time)
                VALUES (?, ?)
            ''', (user_id, datetime.now().isoformat()))

    def delete_like_time(self, user_id):
        with self.connection:
            self.connection.execute('''
                DELETE FROM likes WHERE user_id = ?
            ''', (user_id,))

    def extract_domain(self, url):
        parsed_url = urlparse(url)
        return parsed_url.netloc

    def is_whitelisted(self, url):
        domain = self.extract_domain(url)
        cursor = self.connection.execute('''
            SELECT 1 FROM whitelist WHERE url = ?
        ''', (domain,))
        result = cursor.fetchone()
        return result is not None

    def add_to_whitelist(self, url):
        domain = self.extract_domain(url)
        with self.connection:
            self.connection.execute('''
                INSERT OR IGNORE INTO whitelist (url) VALUES (?)
            ''', (domain,))