import sqlite3

with open('无数据股票列表.txt', 'r', encoding='utf-8') as f:
    codes = [line.strip() for line in f if line.strip()]

conn = sqlite3.connect('stock_data.db')
cursor = conn.cursor()

found_in_db = []
not_found_in_db = []

for code in codes:
    cursor.execute("SELECT * FROM stock_list WHERE code = ?", (code,))
    stock_info = cursor.fetchone()
    
    if stock_info:
        found_in_db.append(code)
    else:
        not_found_in_db.append(code)

print(f"删除结果统计:")
print(f"=" * 60)
print(f"文件中股票总数: {len(codes)}")
print(f"数据库中找到并已删除: {len(found_in_db)}")
print(f"数据库中未找到: {len(not_found_in_db)}")
print(f"=" * 60)

if not_found_in_db:
    print(f"\n未在数据库中找到的股票代码 ({len(not_found_in_db)} 个):")
    for i, code in enumerate(not_found_in_db, 1):
        print(f"{code}", end="")
        if i % 10 == 0:
            print()
    print()

cursor.execute("SELECT COUNT(*) FROM daily")
daily_count = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM stock_list")
stock_list_count = cursor.fetchone()[0]

print(f"\n数据库最终状态:")
print(f"- daily 表: {daily_count} 条记录")
print(f"- stock_list 表: {stock_list_count} 条记录")

conn.close()
