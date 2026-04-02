import sqlite3

print("=" * 70)
print("删除操作总结报告")
print("=" * 70)

conn = sqlite3.connect('stock_data.db')
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM stock_list")
current_stock_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM daily")
current_daily_count = cursor.fetchone()[0]

print(f"\n当前数据库状态:")
print(f"  - stock_list 表: {current_stock_count} 条记录")
print(f"  - daily 表: {current_daily_count} 条记录")

print(f"\n删除操作:")
print(f"  - 从 stock_list 表删除了 64 条无数据股票记录")
print(f"  - 这些股票在 daily 表中本来就没有数据（0条删除）")
print(f"  - stock_list 表从 5456 条减少到 {current_stock_count} 条")

print(f"\n说明:")
print(f"  - 文件中共有 269 个无数据股票代码")
print(f"  - 其中 64 个在数据库的 stock_list 表中存在（已删除）")
print(f"  - 另外 205 个可能在之前已经被清理或不在此数据库中")

conn.close()

print("\n" + "=" * 70)
print("删除完成！无数据股票已从数据库中清除。")
print("=" * 70)
