"""
获取股票2026年至今的数据并存入数据库
使用 mootdx 库连接通达信行情服务器
"""

import sqlite3
import pandas as pd
from mootdx.quotes import Quotes
import time


def create_client():
    """创建行情客户端"""
    print("正在连接行情服务器...")
    client = Quotes.factory(market='std', server=('120.76.1.198', 7709))
    print("连接成功!")
    return client


def get_stock_list():
    """获取股票列表"""
    conn = sqlite3.connect('stock_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT code FROM stock_list')
    stocks = [row[0] for row in cursor.fetchall()]
    conn.close()
    return stocks


def calculate_fields(df):
    """计算 amplitude, pct_chg, chg, turnover 等字段"""
    # 按日期排序
    df = df.sort_index()

    # 计算涨跌额 (chg): 今日收盘价 - 昨日收盘价
    df['chg'] = df['close'].diff()

    # 计算涨跌幅 (pct_chg): (今日收盘价 - 昨日收盘价) / 昨日收盘价 * 100
    df['pct_chg'] = df['close'].pct_change() * 100

    # 计算振幅 (amplitude): (最高价 - 最低价) / 昨日收盘价 * 100
    df['amplitude'] = (df['high'] - df['low']) / df['close'].shift(1) * 100

    # 计算换手率 (turnover): 成交量 / 流通股本 * 100 (这里没有流通股本数据，暂且用成交量代替)
    # 注意：实际换手率需要流通股数据，这里暂时设为0
    df['turnover'] = 0.0

    return df


def fetch_and_store_data(client, stock_code, conn):
    """获取单只股票的数据并存储"""
    try:
        # 获取日线数据
        df = client.bars(symbol=stock_code)

        if df is None or df.empty:
            return 0

        # 过滤2026年至今的数据
        df_2026 = df[df.index >= '2026-01-01'].copy()

        if df_2026.empty:
            return 0

        # 计算派生字段
        df_2026 = calculate_fields(df_2026)

        # 准备插入数据库的数据
        cursor = conn.cursor()
        inserted_count = 0

        for idx, row in df_2026.iterrows():
            # 跳过最后一行异常数据（如volume过小）
            if row['volume'] < 1:
                continue

            # 从索引中提取日期部分
            date_str = idx.strftime('%Y-%m-%d')

            # 计算 amplitude (如果为NaN设为0)
            amplitude = row['amplitude'] if pd.notna(row['amplitude']) else 0.0
            pct_chg = row['pct_chg'] if pd.notna(row['pct_chg']) else 0.0
            chg = row['chg'] if pd.notna(row['chg']) else 0.0

            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO daily
                    (date, code, open, close, high, low, volume, amount,
                     amplitude, pct_chg, chg, turnover, valid_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    date_str,
                    stock_code,
                    row['open'],
                    row['close'],
                    row['high'],
                    row['low'],
                    row['vol'],  # 使用 vol 作为成交量
                    row['amount'],
                    amplitude,
                    pct_chg,
                    chg,
                    0.0,  # turnover 暂时设为0
                    1     # valid_data
                ))
                inserted_count += 1
            except Exception as e:
                print(f"  插入数据失败 {stock_code} {date_str}: {e}")

        return inserted_count

    except Exception as e:
        print(f"  获取 {stock_code} 数据失败: {e}")
        return 0


def main():
    print("=" * 50)
    print("股票数据获取程序 - 2026年至今")
    print("=" * 50)

    # 连接数据库
    conn = sqlite3.connect('stock_data.db')
    print(f"数据库连接成功: stock_data.db")

    # 创建行情客户端
    client = create_client()

    # 获取股票列表
    stocks = get_stock_list()
    print(f"共有 {len(stocks)} 只股票")

    # 统计
    total_inserted = 0
    failed_stocks = []
    skip_count = 0

    # 遍历股票列表
    for i, stock_code in enumerate(stocks):
        if (i + 1) % 100 == 0:
            print(f"\n进度: {i + 1}/{len(stocks)}")

        try:
            count = fetch_and_store_data(client, stock_code, conn)
            if count > 0:
                total_inserted += count
                print(f"  {stock_code}: 获取 {count} 条数据")
            else:
                skip_count += 1
        except Exception as e:
            failed_stocks.append((stock_code, str(e)))
            print(f"  {stock_code}: 失败 - {e}")

        # 每处理50只股票提交一次
        if (i + 1) % 50 == 0:
            conn.commit()

        # 添加延迟避免请求过快
        time.sleep(0.1)

    # 最终提交
    conn.commit()
    conn.close()

    print("\n" + "=" * 50)
    print("数据获取完成!")
    print(f"成功插入: {total_inserted} 条")
    print(f"无数据股票: {skip_count} 只")
    if failed_stocks:
        print(f"失败股票: {len(failed_stocks)} 只")
        for code, err in failed_stocks[:10]:
            print(f"  {code}: {err}")


if __name__ == "__main__":
    main()
