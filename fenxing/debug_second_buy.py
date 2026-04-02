"""
调试脚本：分析为什么找不到2买
"""

import sqlite3
import pandas as pd
import sys

sys.path.append('.')

from chanlun_signals import identify_first_buy, identify_second_buy
from macd import add_macd_to_dataframe
from fenxing_with_macd import find_fenxing, merge_same_type, extract_trends


def analyze_stock_debug(stock_code, query_days=120):
    """分析单只股票的结构"""
    try:
        conn = sqlite3.connect('../data/stock_data.db')
        
        df = pd.read_sql(f'''
            SELECT date, open, close, high, low, volume
            FROM daily
            WHERE code="{stock_code}" AND valid_data=1
            ORDER BY date DESC
            LIMIT {query_days}
        ''', conn)
        conn.close()
        
        if len(df) < 30:
            return None
        
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        
        df_with_macd = add_macd_to_dataframe(df)
        klines = df[['date', 'open', 'close', 'high', 'low']].to_dict('records')
        
        processed, filtered = find_fenxing(klines)
        merged = merge_same_type(filtered)
        
        if len(merged) < 4:
            return None
        
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
        
        down_trends = [t for t in trends if t['type'] == '下降']
        
        return {
            'code': stock_code,
            'fenxing_count': len(merged),
            'total_trends': len(trends),
            'down_trends': len(down_trends),
            'fenxing_sequence': ''.join([fx[1] for fx in merged])
        }
        
    except:
        return None


def main():
    print("=" * 80)
    print("Debug: Analyzing Stock Structure")
    print("=" * 80)
    
    conn = sqlite3.connect('../data/stock_data.db')
    stocks_df = pd.read_sql('SELECT code FROM stock_list ORDER BY code LIMIT 100', conn)
    conn.close()
    
    print(f"\nAnalyzing first 100 stocks...\n")
    
    stats = {
        'total': 0,
        'valid_structures': 0,
        'with_down_trends_2plus': 0,
        'with_first_buy': 0,
        'with_second_buy': 0
    }
    
    sample_data = []
    
    for idx, row in stocks_df.iterrows():
        stock_code = row['code']
        stats['total'] += 1
        
        result = analyze_stock_debug(stock_code)
        
        if result is None:
            continue
        
        stats['valid_structures'] += 1
        
        if result['down_trends'] >= 2:
            stats['with_down_trends_2plus'] += 1
            
            # 详细分析这只股票
            conn = sqlite3.connect('../data/stock_data.db')
            df = pd.read_sql(f'''
                SELECT date, open, close, high, low, volume
                FROM daily
                WHERE code="{stock_code}" AND valid_data=1
                ORDER BY date DESC
                LIMIT 120
            ''', conn)
            conn.close()
            
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)
            df_with_macd = add_macd_to_dataframe(df)
            klines = df[['date', 'open', 'close', 'high', 'low']].to_dict('records')
            
            processed, filtered = find_fenxing(klines)
            merged = merge_same_type(filtered)
            
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
            
            first_buys = identify_first_buy(merged, trends, df_with_macd, klines)
            valid_first_buys = [fb for fb in first_buys if fb.macd_info.get('match_type') in ['完美符合', '符合']]
            
            if valid_first_buys:
                stats['with_first_buy'] += 1
                second_buys = identify_second_buy(merged, trends, df_with_macd, klines, first_buys)
                
                if second_buys:
                    stats['with_second_buy'] += 1
                    print(f"\n*** FOUND 2ND BUY: Stock {stock_code}")
                    print(f"    Fenxing: {''.join([fx[1] for fx in merged])}")
                    print(f"    Trends: {len(trends)} ({len([t for t in trends if t['type']=='下降'])} down)")
                    print(f"    First Buys: {len(valid_first_buys)}")
                    for fb in valid_first_buys:
                        print(f"      - {fb.date} @ {fb.price:.2f} [{fb.macd_info.get('match_type')}]")
                    print(f"    Second Buys: {len(second_buys)}")
                    for sb in second_buys:
                        print(f"      - {sb.date} @ {sb.price:.2f}")
                    return
    
    print("\n" + "=" * 80)
    print("Statistics (first 100 stocks):")
    print(f"  Total tested: {stats['total']}")
    print(f"  Valid structures (4+ fenxing): {stats['valid_structures']}")
    print(f"  With 2+ downtrends: {stats['with_down_trends_2plus']}")
    print(f"  With valid 1st buy: {stats['with_first_buy']}")
    print(f"  With 2nd buy: {stats['with_second_buy']}")
    print("=" * 80)


if __name__ == '__main__':
    main()
