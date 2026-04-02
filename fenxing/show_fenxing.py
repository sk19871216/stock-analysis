import sqlite3
import pandas as pd

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
                results.append((i, curr['pos'], 'DING'))
            if curr['low'] < prev['low'] and curr['low'] < next_k['low'] and \
               curr['high'] < prev['high'] and curr['high'] < next_k['high']:
                results.append((i, curr['pos'], 'DI'))
        return results

    def _filter_shared_boundary(all_fx_sorted):
        filtered = []
        last_end = -999
        last_type = None
        for i, pos, ftype in all_fx_sorted:
            left_boundary = pos - 1
            if ftype != last_type and left_boundary <= last_end:
                print(f'DELETE(shared): pos={pos} {ftype}')
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
                if ftype == 'DING' and kline['high'] > lk['high']:
                    result[-1] = [idx, ftype, kline]
                    changed = True
                elif ftype == 'DI' and kline['low'] < lk['low']:
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
    output = []

    output.append('\n' + '=' * 70)
    output.append('Stock Code: 000016 (Last 60 Trading Days Fenxing Analysis)')
    output.append('=' * 70)

    processed, filtered = step1_find_fenxing(klines)

    output.append('\n[Step1] Fenxing Identification (Containment + Remove Shared Boundary)')
    output.append('-' * 70)
    output.append(f'Processed Klines: {len(processed)}')
    output.append(f'Identified Fenxings: {len(filtered)}')
    output.append('\nFenxing Details:')
    output.append(f'{"Index":<6} {"Date":<12} {"Type":<6} {"High":>10} {"Low":>10}')
    output.append('-' * 70)
    for idx, ftype, kline in filtered:
        d = str(kline['date'])[:10]
        symbol = 'DING' if ftype == 'DING' else 'DI  '
        output.append(f'{idx:<6} {d:<12} {symbol:<6} {kline["high"]:>10.2f} {kline["low"]:>10.2f}')

    output.append('\n[Step2] Merge Adjacent Same Type Fenxings')
    output.append('-' * 70)
    merged = step2_merge_same_type(filtered, processed)
    output.append(f'Merged Fenxings: {len(merged)}')
    output.append('\nFinal Fenxings:')
    output.append(f'{"Index":<6} {"Date":<12} {"Type":<6} {"High":>10} {"Low":>10}')
    output.append('-' * 70)
    for idx, ftype, kline in merged:
        d = str(kline['date'])[:10]
        symbol = 'DING' if ftype == 'DING' else 'DI  '
        output.append(f'{idx:<6} {d:<12} {symbol:<6} {kline["high"]:>10.2f} {kline["low"]:>10.2f}')

    output.append('\n' + '=' * 70)
    output.append('Fenxing Trend Summary:')
    fx_sequence = ''.join([ftype[0] for idx, ftype, kline in merged])
    output.append(f'Fenxing Sequence: {fx_sequence}')
    output.append(f'Total valid fenxings in last 60 trading days: {len(merged)}')
    output.append('=' * 70)

    with open('fenxing_result.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))

    print('\n'.join(output))
