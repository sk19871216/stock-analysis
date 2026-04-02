import sqlite3

with open('无数据股票列表.txt', 'r', encoding='utf-8') as f:
    codes = [line.strip() for line in f if line.strip()]

print(f"从文件读取到 {len(codes)} 个股票代码\n")

conn = sqlite3.connect('stock_data.db')
cursor = conn.cursor()

print("检查这些股票在数据库中的存在情况:")
print("-" * 60)

for code in codes[:10]:
    cursor.execute("SELECT COUNT(*) FROM daily WHERE code = ?", (code,))
    daily_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT * FROM stock_list WHERE code = ?", (code,))
    stock_info = cursor.fetchone()
    
    print(f"代码 {code}:")
    print(f"  - daily表记录数: {daily_count}")
    print(f"  - stock_list表: {'存在' if stock_info else '不存在'}")
    if stock_info:
        print(f"    详情: {stock_info}")
    print()

print("-" * 60)
print(f"(仅显示前10条，共 {len(codes)} 条)")

conn.close()
