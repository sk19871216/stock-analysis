import sqlite3

with open('无数据股票列表.txt', 'r', encoding='utf-8') as f:
    codes = [line.strip() for line in f if line.strip()]

print(f"从文件读取到 {len(codes)} 个无数据股票代码")
print(f"示例: {codes[:5]}")

conn = sqlite3.connect('stock_data.db')
cursor = conn.cursor()

print("\n开始删除数据...")

deleted_daily = 0
deleted_stock_list = 0

for code in codes:
    cursor.execute("DELETE FROM daily WHERE code = ?", (code,))
    deleted_daily += cursor.rowcount
    
    cursor.execute("DELETE FROM stock_list WHERE code = ?", (code,))
    deleted_stock_list += cursor.rowcount

conn.commit()

print(f"\n删除完成:")
print(f"- 从 daily 表删除: {deleted_daily} 条记录")
print(f"- 从 stock_list 表删除: {deleted_stock_list} 条记录")

cursor.execute("SELECT COUNT(*) FROM daily")
daily_count = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM stock_list")
stock_list_count = cursor.fetchone()[0]

print(f"\n删除后统计:")
print(f"- daily 表剩余: {daily_count} 条记录")
print(f"- stock_list 表剩余: {stock_list_count} 条记录")

conn.close()
