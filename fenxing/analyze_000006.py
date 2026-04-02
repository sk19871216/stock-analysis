"""
000006 股票分析
分析区间: 2025-08-01 ~ 2026-04-02
识别1买和2买信号

修改说明：
1. 只有背驰才能算1买
2. 价格新低标记为"是"/"否"
3. 相邻下降趋势最低价差距<2%标记为"伪1买"
4. 条件ABC清晰描述
5. 1买2买不能重合
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
        print(f"加载数据失败: {e}")
        return None


def analyze_stock(csv_path, start_date, end_date):
    """分析单只股票的1买和2买"""
    try:
        df = load_csv_data(csv_path)
        
        if df is None or len(df) < 30:
            return None
        
        df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
        
        if len(df) < 30:
            print(f"数据不足: 只有 {len(df)} 条数据")
            return None
        
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
        
        first_buy_signals = identify_first_buy(trends, df_with_macd, klines)
        second_buy_signals = identify_second_buy(trends, df_with_macd, first_buy_signals)
        
        return {
            'data_range': f"{df['date'].iloc[0].strftime('%Y-%m-%d')} ~ {df['date'].iloc[-1].strftime('%Y-%m-%d')}",
            'data_count': len(df),
            'fenxing_count': len(merged),
            'fenxing_sequence': ''.join([fx[1] for fx in merged]),
            'trends': trends,
            'first_buys': first_buy_signals,
            'second_buys': second_buy_signals
        }
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    print("=" * 80)
    print("000006 股票分析报告 (增强版)")
    print("=" * 80)
    
    csv_path = r'D:\claude_code\股票\stock_data_2\000006.csv'
    start_date = '2025-08-01'
    end_date = '2026-04-02'
    
    result = analyze_stock(csv_path, start_date, end_date)
    
    if result is None:
        print("\n分析失败")
        return
    
    print(f"\n📊 数据概况:")
    print(f"   数据范围: {result['data_range']}")
    print(f"   数据条数: {result['data_count']}")
    print(f"   识别分型: {result['fenxing_count']} 个")
    print(f"   分型序列: {result['fenxing_sequence']}")
    
    print(f"\n📈 趋势段分析 ({len(result['trends'])} 个):")
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
        
        trend_symbol = '📉' if t['type'] == '下降' else '📈'
        print(f"  {trend_symbol} 趋势{t['index']}: {t['type']} ({start_date_str} ~ {end_date_str})")
    
    print(f"\n" + "=" * 80)
    print("🛒 1买信号 (第一买点)")
    print("=" * 80)
    
    if result['first_buys']:
        for i, fb in enumerate(result['first_buys'], 1):
            print(f"\n【1买 #{i}】")
            print(f"   📅 日期: {fb.date}")
            print(f"   💰 价格: {fb.price:.2f}")
            
            macd_info = fb.macd_info
            
            print(f"   📉 底背驰判断:")
            print(f"      - 价格新低: {macd_info.get('price_new_low', 'N/A')}")
            print(f"      - 伪1买: {macd_info.get('is_false_first_buy', 'N/A')}")
            print(f"      - 与前段最低价差距: {macd_info.get('price_diff_pct', 0):.2f}%")
            
            print(f"   📊 MACD背驰条件:")
            print(f"      - 条件A (绿柱面积减少): {macd_info.get('cond_a_desc', 'N/A')}")
            print(f"      - 条件B (绿柱高度降低): {macd_info.get('cond_b_desc', 'N/A')}")
            print(f"      - 条件C (下跌力度减弱): {macd_info.get('cond_c_desc', 'N/A')}")
            
            print(f"   📈 详细信息:")
            print(f"      - 当前绿柱面积: {macd_info.get('green_area', 0):.4f}")
            print(f"      - 当前绿柱高度: {macd_info.get('green_bar_height', 0):.4f}")
            print(f"      - 下跌力度: {macd_info.get('force', 0):.4f} 元/天")
            print(f"      - 下跌天数: {macd_info.get('days', 0)} 天")
            
            if fb.next_day_yangxian_pct > 0:
                print(f"   📗 次日阳线: 是 ({fb.next_day_yangxian_pct:.2f}%)")
            else:
                print(f"   📗 次日阳线: 否")
    else:
        print("\n未找到1买信号（注意：现在必须满足背驰条件才能识别为1买）")
    
    print(f"\n" + "=" * 80)
    print("🛒 2买信号 (第二买点)")
    print("=" * 80)
    
    if result['second_buys']:
        for i, sb in enumerate(result['second_buys'], 1):
            print(f"\n【2买 #{i}】")
            print(f"   📅 日期: {sb.date}")
            print(f"   💰 价格: {sb.price:.2f}")
            print(f"   🔗 相关1买:")
            print(f"      - 日期: {sb.macd_info.get('fb_date', 'N/A')}")
            print(f"      - 价格: {sb.macd_info.get('fb_price', 0):.2f}")
            
            fb_price = sb.macd_info.get('fb_price', 0)
            if fb_price > 0:
                distance = sb.price - fb_price
                distance_pct = distance / fb_price * 100
                print(f"   📊 回调信息:")
                print(f"      - 距1买价格: {distance:+.2f} ({distance_pct:+.2f}%)")
            
            if sb.next_day_yangxian_pct > 0:
                print(f"   📗 次日阳线: 是 ({sb.next_day_yangxian_pct:.2f}%)")
            else:
                print(f"   📗 次日阳线: 否")
    else:
        print("\n未找到2买信号")
    
    print("\n" + "=" * 80)


if __name__ == '__main__':
    main()
