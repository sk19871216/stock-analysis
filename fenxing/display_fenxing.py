import sqlite3
import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('stock_data.db')
df = pd.read_sql('''
    SELECT date, open, close, high, low
    FROM daily
    WHERE code="000016" AND valid_data=1
    ORDER BY date DESC
    LIMIT 61
''', conn)
conn.close()

df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date').reset_index(drop=True)
klines = df.to_dict('records')


def step1_find_fenxing(klines):
    def _process_contains(klines):
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
                    prev_pos = prev['pos']
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

    def _find_candidates(klines):
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

    def _filter_shared_boundary(all_fx_sorted):
        filtered = []
        last_end = -999
        last_type = None
        for i, pos, ftype in all_fx_sorted:
            left_boundary = pos - 1
            if ftype != last_type and left_boundary <= last_end:
                print(f'  删除(共享边界) 位置{pos} {ftype}')
            else:
                kline = processed[i]
                filtered.append((pos, ftype, kline))
                last_end = pos + 1
                last_type = ftype
        return filtered

    processed = _process_contains(klines)
    all_fx = _find_candidates(processed)
    all_fx.sort(key=lambda x: x[1])
    filtered = _filter_shared_boundary(all_fx)
    return processed, filtered


def step2_merge_same_type(filtered, processed):
    def _merge_once(items):
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
        merged, changed = _merge_once(items)
        items = merged
        if not changed:
            break
    return items


if __name__ == '__main__':
    print('\n' + '=' * 70)
    print('股票代码: 000016 (最近60个交易日分型分析)')
    print('=' * 70)

    processed, filtered = step1_find_fenxing(klines)

    print('\n【Step1】分型识别结果 (处理包含关系 + 去共享边界)')
    print('-' * 70)
    print(f'处理后K线数: {len(processed)}')
    print(f'识别分型数: {len(filtered)}')
    print('\n分型详情:')
    print(f'{"序号":<6} {"日期":<12} {"类型":<6} {"最高价":>10} {"最低价":>10}')
    print('-' * 70)
    for idx, ftype, kline in filtered:
        d = str(kline['date'])[:10]
        symbol = '▲ 顶' if ftype == '顶' else '▼ 底'
        print(f'{idx:<6} {d:<12} {symbol:<6} {kline["high"]:>10.2f} {kline["low"]:>10.2f}')

    print('\n【Step2】合并相邻同类型分型')
    print('-' * 70)
    merged = step2_merge_same_type(filtered, processed)
    print(f'合并后分型数: {len(merged)}')
    print('\n最终分型:')
    print(f'{"序号":<6} {"日期":<12} {"类型":<6} {"最高价":>10} {"最低价":>10}')
    print('-' * 70)
    for idx, ftype, kline in merged:
        d = str(kline['date'])[:10]
        symbol = '▲ 顶' if ftype == '顶' else '▼ 底'
        print(f'{idx:<6} {d:<12} {symbol:<6} {kline["high"]:>10.2f} {kline["low"]:>10.2f}')

    print('\n' + '=' * 70)
    print('分型趋势总结:')
    fx_sequence = ''.join([ftype[0] for idx, ftype, kline in merged])
    print(f'分型序列: {fx_sequence}')
    print(f'最近60个交易日共识别出 {len(merged)} 个有效分型')
    print('=' * 70)
