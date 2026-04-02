"""
000001 特定时间段分析：2025年8月1日 - 2026年1月10日
识别1买和2买
"""

import sys
import pandas as pd

DATA_DIR = r'D:\claude_code\股票\stock_data_2'

sys.path.append('.')

from chanlun_signals import identify_first_buy, identify_second_buy
from macd import add_macd_to_dataframe
from fenxing_with_macd import find_fenxing, merge_same_type, extract_trends


def load_csv_data(csv_path):
    """加载CSV格式的股票数据"""
    try:
        df = pd.read_csv(csv_path)
        df.columns = ['date', 'code', 'open', 'close', 'high', 'low', 'volume', 
                      'amount', 'amplitude', 'pct_chg', 'chg', 'turnover']
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        return df
    except Exception as e:
        return None


def analyze_stock(csv_path, start_date, end_date):
    """分析单只股票的1买和2买"""
    try:
        df = load_csv_data(csv_path)
        
        if df is None or len(df) < 30:
            return None
        
        # 过滤时间范围
        df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
        
        if len(df) < 30:
            print(f"  数据不足: 只有 {len(df)} 条数据")
            return None
        
        # 计算MACD
        df_with_macd = add_macd_to_dataframe(df)
        klines = df[['date', 'open', 'close', 'high', 'low']].to_dict('records')
        
        # 分型识别
        processed, filtered = find_fenxing(klines)
        merged = merge_same_type(filtered)
        
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
        
        # 识别1买
        first_buy_signals = identify_first_buy(merged, trends, df_with_macd, klines)
        
        # 识别2买
        second_buy_signals = identify_second_buy(merged, trends, df_with_macd, klines, first_buy_signals)
        
        # 过滤一买和二买日期相同的情况
        filtered_second_buys = []
        for sb in second_buy_signals:
            related_fb = sb.macd_info.get('related_first_buy', {})
            if related_fb.get('date') != sb.date:
                filtered_second_buys.append(sb)
        
        return {
            'data_range': f"{df['date'].iloc[0].strftime('%Y-%m-%d')} ~ {df['date'].iloc[-1].strftime('%Y-%m-%d')}",
            'data_count': len(df),
            'fenxing_count': len(merged),
            'fenxing_sequence': ''.join([fx[1] for fx in merged]),
            'trends': trends,
            'first_buys': first_buy_signals,
            'second_buys': filtered_second_buys
        }
        
    except Exception as e:
        print(f"  错误: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    print("=" * 80)
    print("000001 特定时间段分析")
    print("分析区间: 2025-08-01 ~ 2026-01-10")
    print("=" * 80)
    
    csv_path = r'D:\claude_code\股票\stock_data_2\000001.csv'
    start_date = '2025-08-01'
    end_date = '2026-01-10'
    
    result = analyze_stock(csv_path, start_date, end_date)
    
    if result is None:
        print("\n分析失败")
        return
    
    print(f"\n数据范围: {result['data_range']}")
    print(f"数据条数: {result['data_count']}")
    print(f"分型数量: {result['fenxing_count']}")
    print(f"分型序列: {result['fenxing_sequence']}")
    
    # 打印趋势
    print(f"\n趋势段 ({len(result['trends'])} 个):")
    print("-" * 80)
    for t in result['trends']:
        start_date_str = t['start_fenxing'][2]['date']
        if isinstance(start_date_str, str):
            start_date_str = start_date_str[:10]
        else:
            start_date_str = start_date_str.strftime('%Y-%m-%d')
        
        end_date_str = t['end_fenxing'][2]['date']
        if isinstance(end_date_str, str):
            end_date_str = end_date_str[:10]
        else:
            end_date_str = end_date_str.strftime('%Y-%m-%d')
        
        print(f"  趋势{t['index']}: {t['type']} ({start_date_str} ~ {end_date_str})")
    
    # 打印1买
    print(f"\n" + "=" * 80)
    print("1买信号")
    print("=" * 80)
    
    valid_first_buys = [fb for fb in result['first_buys'] 
                       if fb.macd_info.get('match_type') in ['完美符合', '符合']]
    
    if valid_first_buys:
        for i, fb in enumerate(valid_first_buys, 1):
            print(f"\n1买 #{i}")
            print(f"  日期: {fb.date}")
            print(f"  价格: {fb.price:.2f}")
            print(f"  类型: {fb.macd_info.get('match_type')}")
            print(f"  所属趋势: {fb.trend_index}")
            
            if 'divergence' in fb.macd_info:
                comp = fb.macd_info['divergence'].get('comparison', {})
                print(f"  价格新低: {'是' if comp.get('price_new_low') else '否'}")
                print(f"  绿柱面积变化: {comp.get('green_area_change_pct', 0):+.2f}%")
                print(f"    当前绿柱面积: {comp.get('current_green_area', 0):.4f} (绝对值: {comp.get('current_green_area_abs', 0):.4f})")
                print(f"    前一绿柱面积: {comp.get('prev_green_area', 0):.4f} (绝对值: {comp.get('prev_green_area_abs', 0):.4f})")
                print(f"  绿柱高度变化: {comp.get('green_bar_height_change_pct', 0):+.2f}%")
                print(f"    当前绿柱高度: {comp.get('current_green_bar_height', 0):.4f} (绝对值: {comp.get('current_green_bar_height_abs', 0):.4f})")
                print(f"    前一绿柱高度: {comp.get('prev_green_bar_height', 0):.4f} (绝对值: {comp.get('prev_green_bar_height_abs', 0):.4f})")
                print(f"  条件A满足: {'是' if comp.get('condition_a') else '否'}")
                print(f"  条件B满足: {'是' if comp.get('condition_b') else '否'}")
    else:
        print("\n未找到符合条件的1买")
    
    if result['first_buys']:
        print(f"\n所有1买候选 ({len(result['first_buys'])} 个):")
        for fb in result['first_buys']:
            print(f"  - {fb.date} @ {fb.price:.2f} [{fb.macd_info.get('match_type', 'N/A')}]")
    
    # 打印2买
    print(f"\n" + "=" * 80)
    print("2买信号")
    print("=" * 80)
    
    if result['second_buys']:
        for i, sb in enumerate(result['second_buys'], 1):
            print(f"\n2买 #{i}")
            print(f"  日期: {sb.date}")
            print(f"  价格: {sb.price:.2f}")
            print(f"  类型: {sb.macd_info.get('match_type')}")
            print(f"  所属趋势: {sb.trend_index}")
            
            related_fb = sb.macd_info.get('related_first_buy', {})
            correction = sb.macd_info.get('correction_trend', {})
            
            print(f"  相关1买:")
            print(f"    日期: {related_fb.get('date', 'N/A')}")
            print(f"    价格: {related_fb.get('price', 0):.2f}")
            print(f"  回调信息:")
            print(f"    距1买距离: {correction.get('distance_from_first_buy', 0):+.2f} ({correction.get('distance_pct', 0):+.2f}%)")
    else:
        print("\n未找到2买")
    
    print("\n" + "=" * 80)


if __name__ == '__main__':
    main()
