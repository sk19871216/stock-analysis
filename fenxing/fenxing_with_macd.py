"""
缠论分型分析 + MACD指标比较
基于分型识别趋势段，并比较相邻相同趋势的MACD面积和量柱高度

趋势定义:
- 下降趋势: 顶分型 → 底分型
- 上升趋势: 底分型 → 顶分型
"""

import sqlite3
import pandas as pd
import sys
from macd import (
    add_macd_to_dataframe, 
    get_trend_macd_metrics, 
    compare_trends,
    detect_divergence
)

sys.stdout.reconfigure(encoding='utf-8')

STOCK_CODE = '002466'
QUERY_DAYS = 120


def load_stock_data(code, days=120):
    """
    加载股票数据
    
    Args:
        code: 股票代码
        days: 查询天数
    
    Returns:
        DataFrame: 包含K线数据的DataFrame
    """
    conn = sqlite3.connect('../data/stock_data.db')
    df = pd.read_sql(f'''
        SELECT date, open, close, high, low, volume
        FROM daily
        WHERE code="{code}" AND valid_data=1
        ORDER BY date DESC
        LIMIT {days}
    ''', conn)
    conn.close()
    
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    
    return df


def find_fenxing(klines):
    """
    找分型
    
    Args:
        klines: K线列表
    
    Returns:
        processed: 处理后的K线
        fenxing_list: 分型列表 [(idx, type, kline), ...]
    """
    def process_contains(klines):
        if len(klines) < 3:
            return klines
        result = [klines[0].copy()]
        result[0]['pos'] = 0
        for i in range(1, len(klines)):
            cur = klines[i]
            cur_pos = i
            last = result[-1]
            last_pos = last['pos']
            if cur['high'] <= last['high'] and cur['low'] >= last['low']:
                continue
            elif last['high'] <= cur['high'] and last['low'] >= cur['low']:
                if len(result) >= 2:
                    prev = result[-2]
                    if prev['high'] < cur['high']:
                        merged_h = max(last['high'], cur['high'])
                        merged_l = max(last['low'], cur['low'])
                        fx_pos = last_pos if last['high'] >= cur['high'] else cur_pos
                    else:
                        merged_h = min(last['high'], cur['high'])
                        merged_l = min(last['low'], cur['low'])
                        fx_pos = last_pos if last['low'] <= cur['low'] else cur_pos
                    result[-1] = {'high': merged_h, 'low': merged_l, 'date': klines[fx_pos]['date'], 'pos': fx_pos}
                else:
                    result[-1] = {'high': cur['high'], 'low': cur['low'], 'date': cur['date'], 'pos': cur_pos}
            else:
                result.append({'high': cur['high'], 'low': cur['low'], 'date': cur['date'], 'pos': cur_pos})
        return result

    def find_candidates(klines):
        results = []
        for i in range(1, len(klines) - 1):
            prev, curr, next_k = klines[i-1], klines[i], klines[i+1]
            if curr['high'] > prev['high'] and curr['high'] > next_k['high'] and \
               curr['low'] > prev['low'] and curr['low'] > next_k['low']:
                results.append((i, curr['pos'], '顶'))
            if curr['low'] < prev['low'] and curr['low'] < next_k['low'] and \
               curr['high'] < prev['high'] and curr['high'] < next_k['high']:
                results.append((i, curr['pos'], '底'))
        return results

    def filter_shared_boundary(all_fx_sorted, processed):
        filtered = []
        last_end = -999
        last_type = None
        for i, pos, ftype in all_fx_sorted:
            left_boundary = pos - 1
            if ftype != last_type and left_boundary <= last_end:
                pass
            else:
                kline = processed[i]
                filtered.append((pos, ftype, kline))
                last_end = pos + 1
                last_type = ftype
        return filtered

    processed = process_contains(klines)
    all_fx = find_candidates(processed)
    all_fx.sort(key=lambda x: x[1])
    filtered = filter_shared_boundary(all_fx, processed)
    
    return processed, filtered


def merge_same_type(filtered):
    """
    合并相邻同类型分型
    """
    def merge_once(items):
        if len(items) <= 1:
            return items, False
        result = [items[0]]
        changed = False
        for i in range(1, len(items)):
            idx, ftype, kline = items[i]
            li, lf, lk = result[-1]
            if ftype == lf:
                if ftype == '顶' and kline['high'] > lk['high']:
                    result[-1] = [idx, ftype, kline]
                    changed = True
                elif ftype == '底' and kline['low'] < lk['low']:
                    result[-1] = [idx, ftype, kline]
                    changed = True
            else:
                result.append([idx, ftype, kline])
        return result, changed

    items = [[idx, ftype, kline] for idx, ftype, kline in filtered]
    while True:
        merged, changed = merge_once(items)
        items = merged
        if not changed:
            break
    
    return items


def extract_trends(fenxing_list):
    """
    从分型列表提取趋势段
    
    Args:
        fenxing_list: 分型列表
    
    Returns:
        趋势段列表 [(趋势类型, 起始分型, 结束分型), ...]
    """
    trends = []
    for i in range(len(fenxing_list) - 1):
        curr_type = fenxing_list[i][1]
        next_type = fenxing_list[i + 1][1]
        
        if curr_type == '顶' and next_type == '底':
            trends.append(('下降', fenxing_list[i], fenxing_list[i + 1]))
        elif curr_type == '底' and next_type == '顶':
            trends.append(('上升', fenxing_list[i], fenxing_list[i + 1]))
    
    return trends


def get_trend_kline_indices(trend, processed):
    """
    获取趋势段对应的K线索引范围
    
    Args:
        trend: (趋势类型, 起始分型, 结束分型)
        processed: 处理后的K线列表
    
    Returns:
        K线索引列表
    """
    _, start_fx, end_fx = trend
    start_idx = start_fx[0]
    end_idx = end_fx[0]
    
    return list(range(start_idx, end_idx + 1))


def analyze_trends(trends, df_with_macd, processed):
    """
    分析所有趋势段的MACD指标
    
    Args:
        trends: 趋势段列表
        df_with_macd: 带MACD的DataFrame
        processed: 处理后的K线
    
    Returns:
        分析结果列表
    """
    dif = df_with_macd['dif']
    dea = df_with_macd['dea']
    macd_hist = df_with_macd['macd_hist']
    volumes = df_with_macd['volume']
    
    results = []
    for i, trend in enumerate(trends, 1):
        trend_type, start_fx, end_fx = trend
        kline_indices = get_trend_kline_indices(trend, processed)
        
        metrics = get_trend_macd_metrics(dif, dea, macd_hist, volumes, kline_indices)
        
        start_date = str(start_fx[2]['date'])[:10]
        end_date = str(end_fx[2]['date'])[:10]
        
        results.append({
            'index': i,
            'type': trend_type,
            'start_date': start_date,
            'end_date': end_date,
            'start_price': start_fx[2]['high'] if trend_type == '下降' else start_fx[2]['low'],
            'end_price': end_fx[2]['low'] if trend_type == '下降' else end_fx[2]['high'],
            'area': metrics['area'],
            'max_height': metrics['max_height'],
            'avg_height': metrics['avg_height'],
            'bar_count': metrics['bar_count']
        })
    
    return results


def compare_adjacent_trends(analysis_results):
    """
    比较所有相同趋势类型的MACD指标
    
    Args:
        analysis_results: 趋势分析结果列表
    
    Returns:
        比较结果列表
    """
    comparisons = []
    
    down_trends = [r for r in analysis_results if r['type'] == '下降']
    up_trends = [r for r in analysis_results if r['type'] == '上升']
    
    if len(down_trends) >= 2:
        for i in range(len(down_trends) - 1):
            curr = down_trends[i]
            next_trend = down_trends[i + 1]
            
            metrics1 = {'area': curr['area'], 'max_height': curr['max_height']}
            metrics2 = {'area': next_trend['area'], 'max_height': next_trend['max_height']}
            
            comparison = compare_trends(metrics1, metrics2)
            divergence = detect_divergence(metrics1, metrics2, '下降')
            
            comparisons.append({
                'trend_index': curr['index'],
                'type': '下降',
                'curr_trend': f"趋势{curr['index']}",
                'next_trend': f"趋势{next_trend['index']}",
                'curr_area': curr['area'],
                'next_area': next_trend['area'],
                'curr_height': curr['max_height'],
                'next_height': next_trend['max_height'],
                'area_change_pct': comparison['area_change_pct'],
                'height_change_pct': comparison['height_change_pct'],
                'divergence': divergence
            })
    
    if len(up_trends) >= 2:
        for i in range(len(up_trends) - 1):
            curr = up_trends[i]
            next_trend = up_trends[i + 1]
            
            metrics1 = {'area': curr['area'], 'max_height': curr['max_height']}
            metrics2 = {'area': next_trend['area'], 'max_height': next_trend['max_height']}
            
            comparison = compare_trends(metrics1, metrics2)
            divergence = detect_divergence(metrics1, metrics2, '上升')
            
            comparisons.append({
                'trend_index': curr['index'],
                'type': '上升',
                'curr_trend': f"趋势{curr['index']}",
                'next_trend': f"趋势{next_trend['index']}",
                'curr_area': curr['area'],
                'next_area': next_trend['area'],
                'curr_height': curr['max_height'],
                'next_height': next_trend['max_height'],
                'area_change_pct': comparison['area_change_pct'],
                'height_change_pct': comparison['height_change_pct'],
                'divergence': divergence
            })
    
    return comparisons


def main():
    print('=' * 80)
    print(f'分型分析 + MACD指标比较')
    print(f'股票代码: {STOCK_CODE}')
    print(f'查询天数: {QUERY_DAYS}天')
    print('=' * 80)
    
    df = load_stock_data(STOCK_CODE, QUERY_DAYS)
    print(f'\n加载数据: {len(df)} 条K线')
    print(f'数据范围: {df["date"].iloc[0]} ~ {df["date"].iloc[-1]}')
    
    klines = df[['date', 'open', 'close', 'high', 'low']].to_dict('records')
    
    processed, filtered = find_fenxing(klines)
    merged = merge_same_type(filtered)
    
    print(f'\n分型识别结果:')
    print(f'  处理后K线数: {len(processed)}')
    print(f'  识别分型数: {len(merged)}')
    print(f'\n分型序列: ', end='')
    for idx, ftype, kline in merged:
        print(ftype[0], end='')
    print()
    
    trends = extract_trends(merged)
    print(f'\n提取趋势段: {len(trends)} 个')
    for i, (trend_type, start, end) in enumerate(trends, 1):
        print(f'  趋势{i}: {trend_type} ({str(start[2]["date"])[:10]} ~ {str(end[2]["date"])[:10]})')
    
    df_with_macd = add_macd_to_dataframe(df)
    
    analysis_results = analyze_trends(trends, df_with_macd, processed)
    
    print('\n' + '=' * 80)
    print('趋势段MACD分析结果:')
    print('=' * 80)
    for result in analysis_results:
        print(f"\n趋势{result['index']} ({result['type']})")
        print(f"  时间范围: {result['start_date']} ~ {result['end_date']}")
        print(f"  价格区间: {result['start_price']:.2f} ~ {result['end_price']:.2f}")
        print(f"  MACD面积: {result['area']:.4f}")
        print(f"  最大量柱高度: {result['max_height']:.4f}")
        print(f"  平均量柱高度: {result['avg_height']:.4f}")
        print(f"  K线数量: {result['bar_count']}")
    
    comparisons = compare_adjacent_trends(analysis_results)
    
    print('\n' + '=' * 80)
    print('相邻相同趋势比较:')
    print('=' * 80)
    for comp in comparisons:
        print(f"\n{comp['curr_trend']} vs {comp['next_trend']} ({comp['type']}趋势)")
        print(f"  {comp['curr_trend']}: 面积={comp['curr_area']:.4f}, 量柱高度={comp['curr_height']:.4f}")
        print(f"  {comp['next_trend']}: 面积={comp['next_area']:.4f}, 量柱高度={comp['next_height']:.4f}")
        print(f"  面积变化: {comp['area_change_pct']:+.2f}%")
        print(f"  量柱高度变化: {comp['height_change_pct']:+.2f}%")
        print(f"  信号: {comp['divergence']}")
    
    output_file = f'../results/fenxing_macd_{STOCK_CODE}.txt'
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('=' * 80 + '\n')
            f.write(f'分型分析 + MACD指标比较\n')
            f.write(f'股票代码: {STOCK_CODE}\n')
            f.write(f'查询天数: {QUERY_DAYS}天\n')
            f.write('=' * 80 + '\n\n')
            
            f.write('分型序列: ')
            for idx, ftype, kline in merged:
                f.write(ftype[0])
            f.write('\n\n')
            
            f.write('趋势段分析结果:\n')
            f.write('-' * 80 + '\n')
            for result in analysis_results:
                f.write(f"\n趋势{result['index']} ({result['type']})\n")
                f.write(f"  时间范围: {result['start_date']} ~ {result['end_date']}\n")
                f.write(f"  价格区间: {result['start_price']:.2f} ~ {result['end_price']:.2f}\n")
                f.write(f"  MACD面积: {result['area']:.4f}\n")
                f.write(f"  最大量柱高度: {result['max_height']:.4f}\n")
            
            f.write('\n\n相邻趋势比较:\n')
            f.write('-' * 80 + '\n')
            for comp in comparisons:
                f.write(f"\n{comp['curr_trend']} vs {comp['next_trend']} ({comp['type']}趋势)\n")
                f.write(f"  面积变化: {comp['area_change_pct']:+.2f}%\n")
                f.write(f"  量柱高度变化: {comp['height_change_pct']:+.2f}%\n")
                f.write(f"  信号: {comp['divergence']}\n")
        
        print(f'\n结果已保存到: {output_file}')
    except Exception as e:
        print(f'\n保存结果失败: {e}')
    
    print('\n' + '=' * 80)


if __name__ == '__main__':
    main()
