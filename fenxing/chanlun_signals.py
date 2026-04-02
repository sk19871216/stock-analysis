"""缠论买卖点识别模块 - 增强版"""
import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class SignalPoint:
    date: str
    price: float
    signal_type: str
    level: int
    fenxing_index: int
    trend_index: int
    kline_index: int
    macd_info: Dict
    verified: bool = False
    next_day_yangxian_pct: float = 0.0
    
    def to_dict(self) -> Dict:
        t = f"{self.level}"
        t = t.replace('1', '一').replace('2', '二').replace('3', '三')
        t = t + ('买' if self.signal_type == 'buy' else '卖')
        return {
            'date': self.date, 'price': self.price, 'type': t,
            'verified': self.verified,
            'next_day_yangxian_pct': self.next_day_yangxian_pct,
            **self.macd_info
        }


def extract_trend_data(trend: Dict, df) -> Dict:
    """提取趋势段的数据"""
    s, e = trend['start_kline_idx'], trend['end_kline_idx']
    seg = df.iloc[s:e+1]
    m = seg['macd_hist']
    greens = m[m < 0]
    reds = m[m > 0]
    g_area = greens.sum() if len(greens) > 0 else 0
    r_area = reds.sum() if len(reds) > 0 else 0
    g_h = greens.min() if len(greens) > 0 else 0
    r_h = reds.max() if len(reds) > 0 else 0
    sd = pd.to_datetime(trend['start_fenxing'][2]['date'])
    ed = pd.to_datetime(trend['end_fenxing'][2]['date'])
    days = max((ed - sd).days, 1)
    sp = trend['start_fenxing'][2]['high']
    ep = trend['end_fenxing'][2]['low']
    if trend['type'] == '下降':
        force = (sp - ep) / days
    else:
        force = (trend['end_fenxing'][2]['high'] - sp) / days
    return {
        'prices': seg['close'], 'highs': seg['high'], 'lows': seg['low'],
        'volume': seg['volume'], 'dif': seg['dif'], 'dea': seg['dea'],
        'macd_hist': m, 'dates': seg['date'],
        'start_idx': s, 'end_idx': e,
        'price_high': seg['high'].max(), 'price_low': seg['low'].min(),
        'macd_high': m.max(), 'macd_low': m.min(),
        'green_area': g_area, 'red_area': r_area,
        'green_bar_height': g_h, 'red_bar_height': r_h,
        'force': force, 'days': days
    }


def detect_divergence(curr: Dict, prev: Optional[Dict], direction: str = 'bottom') -> Optional[Dict]:
    """
    检测背驰
    
    底背驰条件（满足任一即可）：
    - 条件A: 绿柱面积减少（当前下跌段的绿柱面积 < 前一段的绿柱面积）
    - 条件B: 绿柱高度降低（当前下跌段的最低绿柱 < 前一段的最低绿柱）
    - 条件C: 下跌力度减弱（当前每天下跌的价格 < 前一段每天下跌的价格）
    """
    if prev is None:
        return None
    
    if direction == 'bottom':
        pl = abs(curr['price_low'] - prev['price_low']) / prev['price_low'] * 100
        in_z = pl < 2
        cg = curr['green_area'] < 0
        pg = prev['green_area'] < 0
        
        if not cg and not pg:
            return None
        
        cond_a = cond_b = cond_c = False
        
        if cg and pg:
            cond_a = abs(curr['green_area']) < abs(prev['green_area'])
        
        if cg and pg:
            cond_b = abs(curr['green_bar_height']) < abs(prev['green_bar_height'])
        
        if prev['force'] > 0:
            cond_c = curr['force'] < prev['force']
        
        if not (cond_a or cond_b or cond_c):
            return None
        
        return {
            'has_divergence': True,
            'in_zhongshu': in_z,
            'price_diff_pct': pl,
            'cond_a': cond_a,
            'cond_a_desc': '绿柱面积减少' if cond_a else '绿柱面积未减少',
            'cond_b': cond_b,
            'cond_b_desc': '绿柱高度降低' if cond_b else '绿柱高度未降低',
            'cond_c': cond_c,
            'cond_c_desc': '下跌力度减弱' if cond_c else '下跌力度未减弱',
            'current_green': curr['green_area'],
            'prev_green': prev['green_area'],
            'current_green_h': curr['green_bar_height'],
            'prev_green_h': prev['green_bar_height'],
            'current_force': curr['force'],
            'prev_force': prev['force'],
            'days': curr['days'],
            'price_new_low': curr['price_low'] < prev['price_low']
        }
    else:
        ph = abs(curr['price_high'] - prev['price_high']) / prev['price_high'] * 100
        cr = curr['red_area'] > 0
        pr = prev['red_area'] > 0
        
        if not cr and not pr:
            return None
        
        cond_a = cond_b = cond_c = False
        
        if cr and pr:
            cond_a = curr['red_area'] < prev['red_area']
        
        if cr and pr:
            cond_b = curr['red_bar_height'] < prev['red_bar_height']
        
        if prev['force'] > 0:
            cond_c = curr['force'] < prev['force']
        
        if not (cond_a or cond_b or cond_c):
            return None
        
        return {
            'has_divergence': True,
            'in_zhongshu': ph < 2,
            'price_diff_pct': ph,
            'cond_a': cond_a,
            'cond_a_desc': '红柱面积减少' if cond_a else '红柱面积未减少',
            'cond_b': cond_b,
            'cond_b_desc': '红柱高度降低' if cond_b else '红柱高度未降低',
            'cond_c': cond_c,
            'cond_c_desc': '上升力度减弱' if cond_c else '上升力度未减弱',
            'current_red': curr['red_area'],
            'prev_red': prev['red_area'],
            'current_red_h': curr['red_bar_height'],
            'prev_red_h': prev['red_bar_height'],
            'current_force': curr['force'],
            'prev_force': prev['force'],
            'days': curr['days'],
            'price_new_high': curr['price_high'] > prev['price_high']
        }


def identify_first_buy(trends: List[Dict], df, klines) -> List[SignalPoint]:
    """
    识别1买（第一买点）
    
    规则：
    1. 必须有背驰才能算1买（删除非背驰的"初步1买"）
    2. 判断价格是否新低
    3. 判断是否伪1买（与前一个下降趋势最低价差距<2%）
    """
    results = []
    downs = [t for t in trends if t['type'] == '下降']
    
    for i, t in enumerate(downs):
        td = extract_trend_data(t, df)
        pd_t = None
        for j in range(i-1, -1, -1):
            if downs[j]['type'] == '下降':
                pd_t = extract_trend_data(downs[j], df)
                break
        
        div = detect_divergence(td, pd_t, 'bottom')
        ef = t['end_fenxing']
        
        if div and ef[1] == '底':
            ndi = td['end_idx'] + 1
            yangxian = 0.0
            if ndi < len(df):
                nd = df.iloc[ndi]
                if nd['close'] > nd['open']:
                    yangxian = (nd['close'] - nd['open']) / nd['open'] * 100
            
            is_false_first_buy = False
            price_diff_pct = 0.0
            
            if pd_t:
                price_diff_pct = abs(td['price_low'] - pd_t['price_low']) / pd_t['price_low'] * 100
                is_false_first_buy = price_diff_pct < 2
            
            results.append(SignalPoint(
                date=str(ef[2]['date'])[:10],
                price=ef[2]['low'],
                signal_type='buy',
                level=1,
                fenxing_index=ef[0],
                trend_index=t['index'],
                kline_index=td['end_idx'],
                macd_info={
                    'in_zhongshu': div['in_zhongshu'],
                    'price_diff_pct': price_diff_pct,
                    'cond_a': div['cond_a'],
                    'cond_a_desc': div['cond_a_desc'],
                    'cond_b': div['cond_b'],
                    'cond_b_desc': div['cond_b_desc'],
                    'cond_c': div['cond_c'],
                    'cond_c_desc': div['cond_c_desc'],
                    'green_area': td['green_area'],
                    'green_bar_height': td['green_bar_height'],
                    'force': td['force'],
                    'days': td['days'],
                    'price_new_low': '是' if div['price_new_low'] else '否',
                    'is_false_first_buy': '是' if is_false_first_buy else '否'
                },
                verified=True,
                next_day_yangxian_pct=yangxian
            ))
    
    return results


def identify_second_buy(trends: List[Dict], df, first_buys: List[SignalPoint]) -> List[SignalPoint]:
    """
    识别2买（第二买点）
    
    规则：
    1. 2买不能与1买重合（日期不能相同）
    2. 1买后的上升趋势回调
    3. 回调低点不破1买价格
    """
    results = []
    for fb in first_buys:
        fb_idx = fb.trend_index
        fb_price = fb.price
        fb_date = fb.date
        
        for i, t in enumerate(trends):
            if t['index'] > fb_idx and t['type'] == '上升':
                for j in range(i+1, len(trends)):
                    if trends[j]['type'] == '下降':
                        td = extract_trend_data(trends[j], df)
                        cl = trends[j]['end_fenxing'][2]['low']
                        cl_date = str(trends[j]['end_fenxing'][2]['date'])[:10]
                        
                        if cl_date == fb_date:
                            continue
                        
                        if cl >= fb_price:
                            ndi = td['end_idx'] + 1
                            yangxian = 0.0
                            if ndi < len(df):
                                nd = df.iloc[ndi]
                                if nd['close'] > nd['open']:
                                    yangxian = (nd['close'] - nd['open']) / nd['open'] * 100
                            
                            results.append(SignalPoint(
                                date=cl_date,
                                price=cl,
                                signal_type='buy',
                                level=2,
                                fenxing_index=trends[j]['end_fenxing'][0],
                                trend_index=trends[j]['index'],
                                kline_index=td['end_idx'],
                                macd_info={
                                    'fb_date': fb_date,
                                    'fb_price': fb_price,
                                    'green_area': td['green_area'],
                                    'force': td['force']
                                },
                                verified=True,
                                next_day_yangxian_pct=yangxian
                            ))
                        break
                break
    return results
