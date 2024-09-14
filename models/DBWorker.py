import sqlite3
from typing import Tuple

def close(connection: sqlite3.Connection) -> bool:
    try:
        connection.close()
        return True
    except Exception as e:
        print(f"Error closing connection: {e}")
        return False

class DBWorker:
    def __init__(self, DBP: str = "noted.db"):
        self.DBP = DBP
        self._buildIfNot()

    def connect(self) -> Tuple[sqlite3.Connection, sqlite3.Cursor]:
        conn = sqlite3.connect(self.DBP)
        cur = conn.cursor()
        return conn, cur

    def _buildIfNot(self) -> bool:
        result = True

        t1 = '''
        CREATE TABLE IF NOT EXISTS users(
            user_idx INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            created_on REAL NOT NULL,
            updated_on REAL NOT NULL
        )
        '''

        t2 = '''
        CREATE TABLE IF NOT EXISTS tags(
            tag_idx INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
            tag_name TEXT NOT NULL,
            user_idx INTEGER NOT NULL,
            created_on REAL NOT NULL,
            updated_on REAL NOT NULL,
            FOREIGN KEY (user_idx) REFERENCES users(user_idx) ON DELETE CASCADE ON UPDATE NO ACTION
        )
        '''

        t3 = '''
        CREATE TABLE IF NOT EXISTS notes(
            note_idx INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
            note_title TEXT NOT NULL,
            note_text TEXT NOT NULL,
            created_on REAL NOT NULL,
            updated_on REAL NOT NULL,
            user_idx INTEGER NOT NULL,
            tag_idx INTEGER NOT NULL,
            FOREIGN KEY (user_idx) REFERENCES users(user_idx) ON DELETE CASCADE ON UPDATE NO ACTION,
            FOREIGN KEY (tag_idx) REFERENCES tags(tag_idx) ON DELETE CASCADE ON UPDATE NO ACTION
        )
        '''

        conn, curr = self.connect()
        try:
            conn.execute("PRAGMA foreign_keys = ON")

            curr.execute(t1)
            conn.commit()

            curr.execute(t2)
            conn.commit()

            curr.execute(t3)
            conn.commit()

        except Exception as e:
            print("Build Error:", e)
            result = False
        finally:
            close(conn)
            return result