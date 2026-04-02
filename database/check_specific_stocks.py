import sqlite3

conn = sqlite3.connect('stock_data.db')
cursor = conn.cursor()

test_codes = ['603056', '920000', '920001', '920002']

print("直接检查几个具体的股票代码:")
for code in test_codes:
    cursor.execute("SELECT * FROM stock_list WHERE code = ?", (code,))
    result = cursor.fetchone()
    print(f"{code}: {'存在' if result else '不存在'}")

cursor.execute("SELECT code FROM stock_list LIMIT 10")
print("\n数据库中前10个股票代码:")
for row in cursor.fetchall():
    print(f"  {row[0]}")

conn.close()
