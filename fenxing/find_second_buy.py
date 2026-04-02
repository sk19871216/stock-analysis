"""
批量测试脚本：寻找有2买信号的股票
按数据库顺序测试，找到2只有2买的股票就停止
"""

import sqlite3
import pandas as pd
import sys

sys.path.append('.')

from chanlun_signals import identify_first_buy, identify_second_buy
from macd import add_macd_to_dataframe
from fenxing_with_macd import find_fenxing, merge_same_type, extract_trends


def analyze_stock_second_buy(stock_code, query_days=120):
    """
    分析单只股票的2买信号
    
    Returns:
        list: 2买信号列表，如果没有则返回空列表
    """
    try:
        conn = sqlite3.connect('../data/stock_data.db')
        
        # 检查股票是否有足够数据
        df_check = pd.read_sql(f'''
            SELECT COUNT(*) as cnt FROM daily
            WHERE code="{stock_code}" AND valid_data=1
        ''', conn)
        
        if df_check['cnt'].iloc[0] < query_days:
            conn.close()
            return []
        
        # 加载数据
        df = pd.read_sql(f'''
            SELECT date, open, close, high, low, volume
            FROM daily
            WHERE code="{stock_code}" AND valid_data=1
            ORDER BY date DESC
            LIMIT {query_days}
        ''', conn)
        conn.close()
        
        if len(df) < 30:
            return []
        
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        
        # 计算MACD
        df_with_macd = add_macd_to_dataframe(df)
        klines = df[['date', 'open', 'close', 'high', 'low']].to_dict('records')
        
        # 分型识别
        processed, filtered = find_fenxing(klines)
        merged = merge_same_type(filtered)
        
        # 至少需要4个分型才能形成完整的1买+2买结构
        if len(merged) < 4:
            return []
        
        # 趋势提取
        trends_raw = extract_trends(merged)
        trends = []
        for i, (trend_type, start_fx, end_fx) in enumerate(trends_raw):
            trends.append({
                'index': i + 1,
                'type': trend_type,
                'start_kline_idx': start_fx[0],
                'end_kline_idx': end_fx[0],
                'start_fenxing': start_fx,
                'end_fenxing': end_fx
            })
        
        # 识别1买和2买
        first_buy_signals = identify_first_buy(merged, trends, df_with_macd, klines)
        
        if not first_buy_signals:
            return []
        
        # 过滤掉"初步信号"类型的一买
        valid_first_buys = [fb for fb in first_buy_signals 
                           if fb.macd_info.get('match_type') in ['完美符合', '符合']]
        
        if not valid_first_buys:
            return []
        
        second_buy_signals = identify_second_buy(merged, trends, df_with_macd, klines, first_buy_signals)
        
        # 过滤掉一买和二买日期相同的情况（这是特殊情况）
        filtered_signals = []
        for sb in second_buy_signals:
            related_fb = sb.macd_info.get('related_first_buy', {})
            if related_fb.get('date') != sb.date:
                filtered_signals.append(sb)
        
        return filtered_signals
        
    except Exception as e:
        return []


def main():
    print("=" * 80)
    print("Searching for Stocks with Second Buy Signal")
    print("=" * 80)
    
    # 连接数据库获取股票列表
    conn = sqlite3.connect('../data/stock_data.db')
    stocks_df = pd.read_sql('SELECT code FROM stock_list ORDER BY code', conn)
    conn.close()
    
    total_stocks = len(stocks_df)
    print(f"\nTotal stocks to test: {total_stocks}")
    print("Searching...\n")
    
    found_stocks = []
    
    for idx, row in stocks_df.iterrows():
        stock_code = row['code']
        
        if idx % 100 == 0:
            print(f"Testing stock {idx}/{total_stocks}: {stock_code}")
        
        second_buys = analyze_stock_second_buy(stock_code)
        
        if second_buys:
            for sb in second_buys:
                found_stocks.append({
                    'code': stock_code,
                    'date': sb.date,
                    'price': sb.price,
                    'match_type': sb.macd_info.get('match_type', 'N/A'),
                    'trend_index': sb.trend_index,
                    'related_first_buy': sb.macd_info.get('related_first_buy', {})
                })
                print(f"\n*** FOUND: Stock {stock_code} has 2nd buy on {sb.date} @ {sb.price:.2f}")
                
                if len(found_stocks) >= 2:
                    print("\n" + "=" * 80)
                    print("Found 2 stocks with 2nd buy signals! Stopping...")
                    print("=" * 80)
                    print("\n\nResults:")
                    print("-" * 80)
                    for i, stock in enumerate(found_stocks, 1):
                        print(f"{i}. Stock: {stock['code']}")
                        print(f"   2nd Buy Date: {stock['date']}, Price: {stock['price']:.2f}")
                        print(f"   Type: {stock['match_type']}")
                        print(f"   Related 1st Buy: {stock['related_first_buy'].get('date', 'N/A')} @ {stock['related_first_buy'].get('price', 0):.2f}")
                        print()
                    print("-" * 80)
                    return
    
    if not found_stocks:
        print("\nNo stocks with 2nd buy signal found in the dataset.")
    else:
        print("\n\nResults:")
        print("-" * 80)
        for i, stock in enumerate(found_stocks, 1):
            print(f"{i}. Stock: {stock['code']}, Date: {stock['date']}, Price: {stock['price']:.2f}")
        print("-" * 80)


if __name__ == '__main__':
    main()
