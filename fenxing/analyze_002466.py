"""
002466 First Buy Analysis - English Output
"""

import sqlite3
import pandas as pd
import sys

sys.path.append('.')

from chanlun_signals import identify_first_buy
from macd import add_macd_to_dataframe
from fenxing_with_macd import find_fenxing, merge_same_type, extract_trends


def main():
    print("=" * 80)
    print("002466 First Buy Analysis")
    print("=" * 80)
    
    STOCK_CODE = '002466'
    QUERY_DAYS = 120
    
    # Load data
    conn = sqlite3.connect('../data/stock_data.db')
    df = pd.read_sql(f'''
        SELECT date, open, close, high, low, volume
        FROM daily
        WHERE code="{STOCK_CODE}" AND valid_data=1
        ORDER BY date DESC
        LIMIT {QUERY_DAYS}
    ''', conn)
    conn.close()
    
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    
    print(f"\nData Range: {df['date'].iloc[0].strftime('%Y-%m-%d')} ~ {df['date'].iloc[-1].strftime('%Y-%m-%d')}")
    print(f"K-line Count: {len(df)}")
    
    # Calculate MACD
    df_with_macd = add_macd_to_dataframe(df)
    klines = df[['date', 'open', 'close', 'high', 'low']].to_dict('records')
    
    # Fenxing identification
    processed, filtered = find_fenxing(klines)
    merged = merge_same_type(filtered)
    
    print(f"\nFenxing Sequence: ", end='')
    for idx, ftype, kline in merged:
        print(f"'{ftype}'" if ftype == '顶' else f"'{ftype}'", end='')
    print()
    print(f"Fenxing Count: {len(merged)}")
    
    # Trend extraction
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
    
    print(f"\nExtracted {len(trends)} Trends:")
    for t in trends:
        print(f"  Trend {t['index']}: {t['type']} (Index {t['start_kline_idx']} ~ {t['end_kline_idx']})")
    
    # First Buy Identification
    print('\n' + '=' * 80)
    print('First Buy (1 Buy) Identification')
    print('=' * 80)
    
    first_buy_signals = identify_first_buy(merged, trends, df_with_macd, klines)
    
    if first_buy_signals:
        print(f"\n[FIND] Identified {len(first_buy_signals)} First Buy Signal(s)!\n")
        
        for i, signal in enumerate(first_buy_signals, 1):
            match_type = signal.macd_info.get('match_type', 'N/A')
            print(f"First Buy #{i} - [{match_type}]")
            print(f"  Date: {signal.date}")
            print(f"  Price: {signal.price:.2f}")
            print(f"  Trend Index: {signal.trend_index}")
            print(f"  Verified: {'Yes' if signal.verified else 'No'}")
            
            # MACD详细信息
            if 'divergence' in signal.macd_info:
                div_info = signal.macd_info.get('divergence', {})
                comp = div_info.get('comparison', {})
                
                print(f"  --- Divergence Details ---")
                print(f"  Price New Low: {'Yes' if comp.get('price_new_low') else 'No'}")
                print(f"  Price Change: {comp.get('price_change', 0):.2f}")
                
                # 面积对比
                print(f"  [Condition A] MACD Area:")
                print(f"    Current: {comp.get('current_macd_area', 0):.2f}")
                print(f"    Previous: {comp.get('prev_macd_area', 0):.2f}")
                print(f"    Change: {comp.get('area_change_pct', 0):+.2f}%")
                print(f"    Satisfied: {'Yes' if comp.get('condition_a') else 'No'}")
                
                # 量柱高度对比
                print(f"  [Condition B] Bar Height:")
                print(f"    Current: {comp.get('current_bar_height', 0):.4f}")
                print(f"    Previous: {comp.get('prev_bar_height', 0):.4f}")
                print(f"    Change: {comp.get('bar_height_change_pct', 0):+.2f}%")
                print(f"    Satisfied: {'Yes' if comp.get('condition_b') else 'No'}")
            else:
                print(f"  --- MACD Details ---")
                print(f"  MACD Area: {signal.macd_info.get('macd_area', 0):.2f}")
                print(f"  Bar Height: {signal.macd_info.get('bar_height', 0):.4f}")
            
            print()
    else:
        print("\n[NOT FOUND] No First Buy Signal Identified")
    
    # Downtrend Analysis
    print('\n' + '=' * 80)
    print('Downtrend Analysis')
    print('=' * 80)
    
    down_trends = [t for t in trends if t['type'] == '下降']
    print(f"\nDowntrend Count: {len(down_trends)}")
    
    for t in down_trends:
        start_fx = t['start_fenxing']
        end_fx = t['end_fenxing']
        start_date = start_fx[2]['date'] if isinstance(start_fx[2]['date'], str) else start_fx[2]['date'].strftime('%Y-%m-%d')
        end_date = end_fx[2]['date'] if isinstance(end_fx[2]['date'], str) else end_fx[2]['date'].strftime('%Y-%m-%d')
        
        print(f"\nDowntrend #{t['index']}:")
        print(f"  Date Range: {start_date} ~ {end_date}")
        print(f"  Price Range: {start_fx[2]['high']:.2f} -> {end_fx[2]['low']:.2f}")
        
        segment = df_with_macd.iloc[t['start_kline_idx']:t['end_kline_idx']+1]
        macd_min = segment['macd_hist'].min()
        macd_max = segment['macd_hist'].max()
        macd_area = segment['macd_hist'].abs().sum()
        bar_height = max(abs(macd_min), abs(macd_max))
        
        print(f"  MACD Range: {macd_min:.4f} ~ {macd_max:.4f}")
        print(f"  MACD Area: {macd_area:.2f}")
        print(f"  Bar Height: {bar_height:.4f}")
    
    print('\n' + '=' * 80)


if __name__ == '__main__':
    main()
