import sqlite3

conn = sqlite3.connect('stock_data.db')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("数据库中的表:")
for table in tables:
    print(f"- {table[0]}")
    cursor.execute(f"PRAGMA table_info({table[0]})")
    columns = cursor.fetchall()
    print(f"  列: {[col[1] for col in columns]}")
    
    cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
    count = cursor.fetchone()[0]
    print(f"  记录数: {count}")
    print()

conn.close()
