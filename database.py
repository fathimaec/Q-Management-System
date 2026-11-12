import sqlite3
def connect_db():
    conn=sqlite3.connect("queue.db")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def create_table():
    conn=connect_db()
    c=conn.cursor()
    c.execute("""
              CREATE TABLE IF NOT EXISTS Users(
              user_id INTEGER PRIMARY KEY AUTOINCREMENT,
              full_name TEXT NOT NULL,
              user_name TEXT UNIQUE NOT NULL,
              password TEXT NOT NULL)""")
    conn.commit()
    conn.close()


def create_queue():
    conn=connect_db()
    c=conn.cursor()
    c.execute("""
             CREATE TABLE IF NOT EXISTS Queue(
             queue_id INTEGER PRIMARY KEY AUTOINCREMENT,
             user_id INTEGER NOT NULL,
             token_number INTEGER NOT NULL,
             status TEXT DEFAULT 'WAITING' CHECK(status IN('WAITING','SERVING','COMPLETED','SKIPPED')),
             created_at TEXT DEFAULT CURRENT_TIMESTAMP,
             called_at TEXT,
             completed_at TEXT,
             service_date TEXT NOT NULL DEFAULT (DATE('now')),
             FOREIGN KEY(user_id) REFERENCES Users(user_id),
             UNIQUE(service_date,token_number)
             )""")
    conn.commit()
    conn.close()


def create_admin():
    conn=connect_db()
    c=conn.cursor()
    c.execute("""
            CREATE TABLE IF NOT EXISTS Admin(
            admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL)""")
    c.execute("SELECT * FROM Admin WHERE user_name=?",("admin",))
    result=c.fetchone()
    if result is None:
        c.execute("""
                 INSERT INTO Admin(user_name,password)
                 VALUES(?,?)""",("admin","admin123"))      
    conn.commit()
    conn.close()

def create_all_tables():
    create_table()
    create_queue()
    create_admin()

create_all_tables()
print("Table created successfully...!")