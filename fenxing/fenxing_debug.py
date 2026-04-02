"""
缠论分型算法 - 分步调试版本
Step1: 找分型(含包含处理+去共享边界)
Step2: 合并相邻同类型
Step3: 判断间隔
"""
import sqlite3
import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

# ==================== 数据加载 ====================
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


# ==================== Step1 ====================
def step1_find_fenxing(klines):
    """
    1. 处理K线包含关系
    2. 识别所有分型候选
    3. 去掉有公共边界K线的分型
    """
    # ---- 1. 处理包含关系 ----
    def _process_contains(klines):
        """
        处理包含关系，返回处理后K线列表
        每条K线增加 'pos' 字段：如果是合并后K线，pos=H/L更高/低K线在原始序列的位置
        """
        if len(klines) < 3:
            return klines
        result = [klines[0].copy()]
        result[0]['pos'] = 0  # 第一根K线位置为0
        for i in range(1, len(klines)):
            cur = klines[i]
            cur_pos = i
            last = result[-1]
            last_pos = last['pos']
            if cur['high'] <= last['high'] and cur['low'] >= last['low']:
                # cur被last包含，跳过
                continue
            elif last['high'] <= cur['high'] and last['low'] >= cur['low']:
                # last被cur包含，需要合并
                if len(result) >= 2:
                    prev = result[-2]
                    prev_pos = prev['pos']
                    if prev['high'] < cur['high']:
                        # 向上走势
                        merged_h = max(last['high'], cur['high'])
                        merged_l = max(last['low'], cur['low'])
                        # 顶分型取H更高的那根K线
                        fx_pos = last_pos if last['high'] >= cur['high'] else cur_pos
                    else:
                        # 向下走势
                        merged_h = min(last['high'], cur['high'])
                        merged_l = min(last['low'], cur['low'])
                        # 底分型取L更低的那根K线
                        fx_pos = last_pos if last['low'] <= cur['low'] else cur_pos
                    result[-1] = {'high': merged_h, 'low': merged_l, 'date': klines[fx_pos]['date'], 'pos': fx_pos}
                else:
                    # 没有prev，取cur
                    result[-1] = {'high': cur['high'], 'low': cur['low'], 'date': cur['date'], 'pos': cur_pos}
            else:
                result.append({'high': cur['high'], 'low': cur['low'], 'date': cur['date'], 'pos': cur_pos})
        return result

    # ---- 2. 找分型候选 ----
    def _find_candidates(klines):
        """
        返回 (processed序列索引i, 原始K线位置pos, 类型) 的列表
        分型位置用pos（对应原始K线），但区间计算用i（处理后序列）
        """
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

    # ---- 3. 去掉有公共边界的分型 ----
    def _filter_shared_boundary(all_fx_sorted):
        """
        all_fx_sorted: [(processed索引i, pos原始位置, ftype), ...]
        分型由3根原始K线组成: [pos-1, pos, pos+1]
        分型a的右边界是pos_a + 1
        分型b的左边界是pos_b - 1
        只有当 分型a 和 分型b 类型不同 且 b的左边界 <= a的右边界 时，才删除b
        如果类型相同，交由Step2合并处理
        """
        filtered = []
        last_end = -999  # 上一个分型的右边界 (pos_a + 1)
        last_type = None
        for i, pos, ftype in all_fx_sorted:
            # 分型的左边界是pos-1，右边界是pos+1
            left_boundary = pos - 1
            # 只有不同类型才检查共享边界；同类型在Step2合并
            if ftype != last_type and left_boundary <= last_end:
                print(f'  [删除(共享边界)] 位置{pos} {ftype}  与上一个{last_type}分型共享边界K线')
            else:
                # 保留分型，用processed索引i获取kline，但位置用pos
                kline = processed[i]
                filtered.append((pos, ftype, kline))
                last_end = pos + 1  # 更新为当前分型的右边界
                last_type = ftype
        return filtered

    processed = _process_contains(klines)
    all_fx = _find_candidates(processed)

    # 按pos排序
    all_fx.sort(key=lambda x: x[1])

    filtered = _filter_shared_boundary(all_fx)

    return processed, filtered  # 返回处理后K线和最终分型


# ==================== Step2 ====================
def step2_merge_same_type(filtered, processed):
    """
    合并相邻同类型分型
    顶分型: 保留H更高的
    底分型: 保留L更低的
    """
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


# ==================== Step3 ====================
def step3_check_gap(items):
    """
    每相邻两组之间必须间隔一条K线
    分型a的范围是[idx_a-1, idx_a, idx_a+1]，右边界是idx_a+1
    分型b的范围是[idx_b-1, idx_b, idx_b+1]，左边界是idx_b-1
    中间间隔K线数 = idx_b - 1 - (idx_a + 1) = idx_b - idx_a - 2
    """
    filtered = []
    for item in items:
        if not filtered:
            filtered.append(item)
        else:
            prev_idx = filtered[-1][0]   # 上一个保留分型的位置idx_a
            curr_idx = item[0]            # 当前分型的位置idx_b
            gap = curr_idx - prev_idx - 2  # 中间间隔K线数
            d = str(item[2]['date'])[:10]
            if gap >= 1:                    # 至少隔1条K线
                filtered.append(item)
            else:
                print(f'  [删除(间隔不足)] 位置{curr_idx} {d} {item[1]}  与位置{prev_idx}间隔{gap}<1  (共享了边界)')
    return filtered


# ==================== 入口 ====================
if __name__ == '__main__':
    print('=' * 60)
    print('Step1: 找分型(处理包含 + 去共享边界)')
    print('=' * 60)
    processed, filtered = step1_find_fenxing(klines)
    print(f'\n处理后K线数: {len(processed)}')
    print(f'Step1 结果: {len(filtered)} 个分型')
    for idx, ftype, kline in filtered:
        d = str(kline['date'])[:10]
        symbol = '+' if ftype == '顶' else '-'
        print(f'  [{idx}] {d}  {symbol}{ftype}  H={kline["high"]:.2f}  L={kline["low"]:.2f}')

    print('\n' + '=' * 60)
    print('Step2: 合并相邻同类型')
    print('=' * 60)
    merged = step2_merge_same_type(filtered, processed)
    print(f'Step2 结果: {len(merged)} 个分型')
    for idx, ftype, kline in merged:
        d = str(kline['date'])[:10]
        symbol = '+' if ftype == '顶' else '-'
        print(f'  [{idx}] {d}  {symbol}{ftype}  H={kline["high"]:.2f}  L={kline["low"]:.2f}')

    # print('\n' + '=' * 60)
    # print('Step3: 判断间隔')
    # print('=' * 60)
    # final = step3_check_gap(merged)
    # print(f'\nStep3 结果: {len(final)} 个分型')
    # for idx, ftype, kline in final:
    #     d = str(kline['date'])[:10]
    #     symbol = '+' if ftype == '顶' else '-'
    #     print(f'  [{idx}] {d}  {symbol}{ftype}  H={kline["high"]:.2f}  L={kline["low"]:.2f}')
