import mysql.connector
from config import Config

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            port=int(getattr(Config, "DB_PORT", 3306))
        )
        return conn

    except mysql.connector.Error as err:
        print(f"❌ Database connection error: {err}")
        return None


def init_db():
    conn = get_db_connection()

    if conn:
        print("✅ Database connected successfully!")
        conn.close()