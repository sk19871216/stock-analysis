"""
002466 一买二买分析脚本
"""

import sqlite3
import pandas as pd
import sys

sys.path.append('.')

from chanlun_signals import identify_first_buy, identify_second_buy
from macd import add_macd_to_dataframe
from fenxing_with_macd import find_fenxing, merge_same_type, extract_trends


def main():
    print("=" * 80)
    print("002466 First Buy & Second Buy Analysis")
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
        print(f"'{ftype}'", end='')
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
            
            if 'divergence' in signal.macd_info:
                comp = signal.macd_info.get('divergence', {}).get('comparison', {})
                print(f"  Price New Low: {'Yes' if comp.get('price_new_low') else 'No'}")
                print(f"  [Condition A] MACD Area Change: {comp.get('area_change_pct', 0):+.2f}%")
                print(f"  [Condition B] Bar Height Change: {comp.get('bar_height_change_pct', 0):+.2f}%")
            print()
    else:
        print("\n[NOT FOUND] No First Buy Signal Identified")
    
    # Second Buy Identification
    print('\n' + '=' * 80)
    print('Second Buy (2 Buy) Identification')
    print('=' * 80)
    
    second_buy_signals = identify_second_buy(merged, trends, df_with_macd, klines, first_buy_signals)
    
    if second_buy_signals:
        print(f"\n[FIND] Identified {len(second_buy_signals)} Second Buy Signal(s)!\n")
        
        for i, signal in enumerate(second_buy_signals, 1):
            match_type = signal.macd_info.get('match_type', 'N/A')
            related_fb = signal.macd_info.get('related_first_buy', {})
            correction_info = signal.macd_info.get('correction_trend', {})
            
            print(f"Second Buy #{i} - [{match_type}]")
            print(f"  Date: {signal.date}")
            print(f"  Price: {signal.price:.2f}")
            print(f"  Trend Index: {signal.trend_index}")
            print(f"  --- Related First Buy ---")
            print(f"    Date: {related_fb.get('date', 'N/A')}")
            print(f"    Price: {related_fb.get('price', 0):.2f}")
            print(f"  --- Correction Info ---")
            print(f"    Distance from First Buy: {correction_info.get('distance_from_first_buy', 0):+.2f}")
            print(f"    Distance %: {correction_info.get('distance_pct', 0):+.2f}%")
            print(f"  MACD Area: {signal.macd_info.get('macd_area', 0):.2f}")
            print()
    else:
        print("\n[NOT FOUND] No Second Buy Signal Identified")
    
    # Summary
    print('\n' + '=' * 80)
    print('Summary')
    print('=' * 80)
    
    if first_buy_signals:
        print(f"\nFirst Buys: {len(first_buy_signals)}")
        for i, signal in enumerate(first_buy_signals, 1):
            print(f"  #{i}: {signal.date} @ {signal.price:.2f} [{signal.macd_info.get('match_type', 'N/A')}]")
    
    if second_buy_signals:
        print(f"\nSecond Buys: {len(second_buy_signals)}")
        for i, signal in enumerate(second_buy_signals, 1):
            print(f"  #{i}: {signal.date} @ {signal.price:.2f} [{signal.macd_info.get('match_type', 'N/A')}]")
    
    print('\n' + '=' * 80)


if __name__ == '__main__':
    main()
