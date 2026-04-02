"""
002466 一买分析脚本
使用缠论买卖点识别模块分析是否有1买信号
"""

import sqlite3
import pandas as pd
import sys

sys.path.append('.')

from chanlun_signals import identify_first_buy
from macd import add_macd_to_dataframe
from fenxing_with_macd import find_fenxing, merge_same_type, extract_trends

sys.stdout.reconfigure(encoding='utf-8')

STOCK_CODE = '002466'
QUERY_DAYS = 120


def main():
    print('=' * 80)
    print(f'002466 一买分析')
    print('=' * 80)
    
    # 1. 加载数据
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
    
    print(f'\n数据范围: {df["date"].iloc[0]} ~ {df["date"].iloc[-1]}')
    print(f'K线数量: {len(df)}')
    
    # 2. 计算MACD
    df_with_macd = add_macd_to_dataframe(df)
    klines = df[['date', 'open', 'close', 'high', 'low']].to_dict('records')
    
    # 3. 分型识别
    processed, filtered = find_fenxing(klines)
    merged = merge_same_type(filtered)
    
    print(f'\n分型序列: ', end='')
    for idx, ftype, kline in merged:
        print(ftype[0], end='')
    print()
    print(f'识别分型数: {len(merged)}')
    
    # 4. 趋势提取
    trends_raw = extract_trends(merged)
    
    # 转换趋势格式
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
    
    print(f'\n提取趋势段: {len(trends)} 个')
    for t in trends:
        print(f"  趋势{t['index']}: {t['type']} (索引 {t['start_kline_idx']} ~ {t['end_kline_idx']})")
    
    # 5. 一买识别
    print('\n' + '=' * 80)
    print('一买识别分析')
    print('=' * 80)
    
    first_buy_signals = identify_first_buy(merged, trends, df_with_macd, klines)
    
    if first_buy_signals:
        print(f'\n✅ 识别到 {len(first_buy_signals)} 个一买信号！\n')
        
        for i, signal in enumerate(first_buy_signals, 1):
            print(f'一买 #{i}')
            print(f'  日期: {signal.date}')
            print(f'  价格: {signal.price:.2f}')
            print(f'  分型索引: {signal.fenxing_index}')
            print(f'  趋势索引: {signal.trend_index}')
            print(f'  K线索引: {signal.kline_index}')
            print(f'  验证状态: {"已验证" if signal.verified else "未验证"}')
            
            if 'divergence' in signal.macd_info:
                div_info = signal.macd_info.get('divergence', {})
                print(f'  背驰信息:')
                print(f'    - 背驰类型: {div_info.get("divergence_type", "N/A")}')
                print(f'    - 价格变化: {div_info.get("comparison", {}).get("price_change", 0):.2f}')
                print(f'    - MACD变化: {div_info.get("comparison", {}).get("macd_change", 0):.4f}')
            
            print(f'  MACD详情:')
            print(f'    - 价格低点: {signal.macd_info.get("price_low", "N/A"):.2f}')
            print(f'    - MACD低点: {signal.macd_info.get("macd_low", "N/A"):.4f}')
            print(f'    - MACD面积: {signal.macd_info.get("macd_area", "N/A"):.2f}')
            print()
    else:
        print('\n❌ 未识别到一买信号')
        print('\n可能原因:')
        print('  1. 当前没有形成有效的底背驰')
        print('  2. 分型识别数量不足')
        print('  3. 趋势段数量不足以形成背驰比较')
        print('  4. 下跌趋势数量少于2个，无法进行背驰比较')
    
    # 6. 检查下降趋势
    print('\n' + '=' * 80)
    print('下降趋势分析')
    print('=' * 80)
    
    down_trends = [t for t in trends if t['type'] == '下降']
    print(f'\n下降趋势数量: {len(down_trends)}')
    
    for t in down_trends:
        start_fx = t['start_fenxing']
        end_fx = t['end_fenxing']
        print(f'\n下降趋势 #{t["index"]}:')
        print(f'  时间范围: {str(start_fx[2]["date"])[:10]} ~ {str(end_fx[2]["date"])[:10]}')
        print(f'  价格范围: {start_fx[2]["high"]:.2f} → {end_fx[2]["low"]:.2f}')
        
        # 获取该趋势的MACD数据
        segment = df_with_macd.iloc[t['start_kline_idx']:t['end_kline_idx']+1]
        print(f'  MACD柱子范围: {segment["macd_hist"].min():.4f} ~ {segment["macd_hist"].max():.4f}')
        print(f'  MACD面积: {segment["macd_hist"].abs().sum():.2f}')
    
    print('\n' + '=' * 80)


if __name__ == '__main__':
    main()
