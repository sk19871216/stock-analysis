# 缠论买卖点识别功能实现计划

## 一、缠论买卖点定义

### 买点定义

#### 1. 一买（First Buy Point）
- **定义**: 下跌趋势末端，前一个本级别向下走势类型背驰终结点
- **位置**: 下跌趋势的最后一个中枢下方
- **条件**:
  - 价格创新低
  - 出现底背驰（MACD柱子高度或面积不创新低）
  - 形成底分型
- **MACD特征**: 价格创新低，但DIF和MACD柱子没有创新低
- **信号**: 趋势可能反转向上的第一个买点

#### 2. 二买（Second Buy Point）
- **定义**: 一买向上第一次回抽不跌破一买低点的位置
- **位置**: 一买之后，股价反弹后回调的低点
- **条件**:
  - 必须在一买之后出现
  - 回调不破一买低点
  - 形成底分型确认
- **特点**: 二买是下跌趋势结束后的二次确认点

#### 3. 三买（Third Buy Point）
- **定义**: 向上离开中枢后，回抽不进入相邻最近的中枢
- **位置**: 中枢上方，突破后回踩的位置
- **条件**:
  - 突破中枢上沿
  - 回抽不跌回中枢内部
- **特点**: 三买是上涨过程中唯一能够追涨的买点，三买过后必有上涨

### 卖点定义

#### 1. 一卖（First Sell Point）
- **定义**: 上涨趋势末端，前一个本级别向上走势类型背驰终结点
- **位置**: 上涨趋势的最后一个中枢上方
- **条件**:
  - 价格创新高
  - 出现顶背驰（MACD柱子高度或面积不创新高）
  - 形成顶分型
- **MACD特征**: 价格创新高，但DIF和MACD柱子没有创新高
- **信号**: 趋势可能反转向下的第一个卖点

#### 2. 二卖（Second Sell Point）
- **定义**: 一卖向下第一次回抽不上破一卖高点的位置
- **位置**: 一卖之后，股价下跌后反弹的高点
- **条件**:
  - 必须在一卖之后出现
  - 反弹不破一卖高点
  - 形成顶分型确认
- **特点**: 二卖是上涨趋势结束后的二次确认离场点

#### 3. 三卖（Third Sell Point）
- **定义**: 向下离开中枢后，反抽不进入相邻最近的中枢
- **位置**: 中枢下方，跌破后反抽的位置
- **条件**:
  - 跌破中枢下沿
  - 反抽不回到中枢内部
- **特点**: 三卖是下跌过程中唯一能够追跌的卖点，三卖过后必有下跌

## 二、实现架构

### 核心模块

```
fenxing/
├── macd.py                          # 已完成：MACD基础计算
├── fenxing_with_macd.py            # 已完成：分型识别和趋势分析
├── chanlun_signals.py              # 新增：买卖点信号识别模块
└── test_chanlun_signals.py        # 新增：单元测试
```

### 数据结构设计

```python
class BuySellSignals:
    """买卖点识别结果"""
    
    # 买点
    first_buy: List[SignalPoint]   # 一买列表
    second_buy: List[SignalPoint]  # 二买列表
    third_buy: List[SignalPoint]   # 三买列表
    
    # 卖点
    first_sell: List[SignalPoint]  # 一卖列表
    second_sell: List[SignalPoint] # 二卖列表
    third_sell: List[SignalPoint]  # 三卖列表

class SignalPoint:
    """信号点"""
    date: str
    price: float
    type: str  # 'buy' or 'sell'
    level: int  # 1, 2, 3
    fenxing_index: int
    trend_index: int
    macd_info: dict
    verified: bool  # 是否经过确认
```

### 背驰检测方法

```python
def detect_divergence(prices, macd_values, direction):
    """
    检测背驰
    
    Args:
        prices: 价格序列
        macd_values: MACD值序列（DIF或MACD柱子）
        direction: 'up'（底背驰） or 'down'（顶背驰）
    
    Returns:
        bool: 是否背驰
        dict: 背驰详细信息
    """
```

## 三、实现步骤

### Phase 1: 一买识别（本次任务）

#### 1.1 实现背驰检测基础方法
- [ ] `detect_price_macd_divergence()`: 检测价格与MACD背驰
- [ ] `find_divergence_points()`: 找到所有背驰点
- [ ] `validate_divergence()`: 验证背驰的有效性

#### 1.2 实现一买识别
- [ ] `identify_first_buy()`: 识别一买
  - 在下降趋势中查找
  - 价格创新低 + 底背驰
  - 底分型确认
- [ ] `validate_first_buy()`: 验证一买的有效性

#### 1.3 单元测试
- [ ] `test_divergence_detection()`: 测试背驰检测
- [ ] `test_first_buy_on_sample_data()`: 在示例数据上测试一买识别
- [ ] 验证识别结果正确性

### Phase 2: 二买识别（预留方法，不实现）

- [ ] `identify_second_buy()`: 二买识别方法框架
  - 在一买之后查找
  - 回抽不破一买低点
  - 底分型确认

### Phase 3: 三买识别（预留方法，不实现）

- [ ] `identify_third_buy()`: 三买识别方法框架
  - 突破中枢
  - 回抽不进入中枢
  - 底分型确认

### Phase 4: 卖点识别（预留方法，不实现）

- [ ] `identify_first_sell()`: 一卖识别方法框架
- [ ] `identify_second_sell()`: 二卖识别方法框架
- [ ] `identify_third_sell()`: 三卖识别方法框架

## 四、一买识别详细算法

### 输入
- 分型列表: `fenxing_list`
- 趋势段列表: `trends`
- MACD数据: `df_with_macd`
- K线数据: `klines`

### 算法流程

```
1. 遍历所有下降趋势段 (趋势.type == '下降')
   
2. 对每个下降趋势段:
   a. 提取该趋势段的:
      - 价格序列 (从起始分型到结束分型)
      - MACD柱子序列
      - DIF序列
   
   b. 检测底背驰:
      - 找到趋势段内价格最低点 (创新低)
      - 对比该点的MACD值与前一个下降趋势的MACD值
      - 如果价格创新低但MACD没有创新低 → 底背驰
   
   c. 底分型确认:
      - 在价格最低点附近查找底分型
      - 验证底分型的有效性
   
   d. 记录一买候选点

3. 验证一买候选点:
   - 必须在前一个下降趋势的末端
   - 必须有有效的底背驰
   - 必须有底分型确认
```

### 代码框架

```python
def identify_first_buy(fenxing_list, trends, df_with_macd, klines):
    """
    识别一买
    
    Args:
        fenxing_list: 分型列表
        trends: 趋势段列表
        df_with_macd: 带MACD的K线数据
        klines: 原始K线列表
    
    Returns:
        List[SignalPoint]: 一买列表
    """
    first_buy_points = []
    
    # 1. 获取所有下降趋势
    down_trends = [t for t in trends if t['type'] == '下降']
    
    # 2. 遍历下降趋势
    for trend in down_trends:
        # 3. 提取趋势段数据
        trend_data = extract_trend_data(trend, df_with_macd, klines)
        
        # 4. 检测底背驰
        divergence = detect_bottom_divergence(trend_data)
        
        # 5. 底分型确认
        if divergence and validate_fenxing_bottom(trend_data):
            # 6. 创建一买信号点
            signal = create_signal_point(trend, 'first_buy', divergence)
            first_buy_points.append(signal)
    
    return first_buy_points
```

## 五、背驰检测详细实现

### 底背驰检测

```python
def detect_bottom_divergence(trend_data):
    """
    检测底背驰
    
    条件:
    1. 价格创出新低
    2. MACD柱子高度或DIF值没有创新低
    3. 背驰段与前一下降段的MACD面积对比
    
    Returns:
        dict: {
            'has_divergence': bool,
            'price_low_point': dict,
            'macd_info': dict,
            'comparison': dict
        }
    """
    # 1. 找到价格最低点和对应的MACD值
    price_low_idx = find_price_lowest(trend_data['prices'])
    price_low_value = trend_data['prices'][price_low_idx]
    macd_at_low = trend_data['macd_hist'][price_low_idx]
    
    # 2. 与前一下降趋势的MACD对比
    prev_trend_macd = get_previous_trend_macd(trend_data)
    
    # 3. 判断背驰条件
    if (price_low_value < prev_trend_macd['price_low'] and 
        macd_at_low > prev_trend_macd['macd_low']):
        return {
            'has_divergence': True,
            'price_low_point': {'index': price_low_idx, 'value': price_low_value},
            'macd_info': {'value': macd_at_low, 'index': price_low_idx},
            'comparison': {
                'price_change_pct': calculate_change(prev_trend_macd['price_low'], price_low_value),
                'macd_change_pct': calculate_change(prev_trend_macd['macd_low'], macd_at_low)
            }
        }
    
    return {'has_divergence': False}
```

### 顶背驰检测

```python
def detect_top_divergence(trend_data):
    """
    检测顶背驰
    
    条件:
    1. 价格创出新高
    2. MACD柱子高度或DIF值没有创新高
    3. 背驰段与前一上升段的MACD面积对比
    
    Returns:
        dict: 类似于底背驰返回结构
    """
    # 类似于底背驰，方向相反
```

## 六、中枢识别（为三买/三卖准备）

### 中枢识别框架

```python
def identify_zhongshu(klines, level='daily'):
    """
    识别中枢
    
    中枢定义:
    - 某级别中，至少三个连续、已完成的次级别走势类型重叠区间
    
    Returns:
        List[Zhongshu]: 中枢列表
    """
    pass

class Zhongshu:
    """中枢类"""
    start_idx: int
    end_idx: int
    zg: float  # 中枢上沿
    zd: float  # 中枢下沿
    duration: int  # 中枢持续时间
```

## 七、测试策略

### 单元测试文件: `test_chanlun_signals.py`

```python
import unittest
from chanlun_signals import *

class TestChanlunSignals(unittest.TestCase):
    """缠论买卖点测试"""
    
    def test_divergence_detection(self):
        """测试背驰检测"""
        pass
    
    def test_first_buy_on_downtrend(self):
        """测试下降趋势中的一买识别"""
        pass
    
    def test_first_buy_validation(self):
        """测试一买验证"""
        pass
    
    # 以下为预留测试（Phase 2-4实现）
    def test_second_buy_method_exists(self):
        """测试二买方法存在"""
        self.assertTrue(hasattr(chanlun_signals, 'identify_second_buy'))
    
    def test_third_buy_method_exists(self):
        """测试三买方法存在"""
        self.assertTrue(hasattr(chanlun_signals, 'identify_third_buy'))
```

## 八、实施顺序

1. **创建 `chanlun_signals.py` 模块**
   - 定义数据结构
   - 实现背驰检测函数
   - 实现一买识别函数
   - 预留二买、三买、一卖、二卖、三卖方法框架

2. **创建测试文件 `test_chanlun_signals.py`**
   - 编写单元测试
   - 测试背驰检测
   - 测试一买识别

3. **运行单元测试**
   - 确保一买识别功能正确
   - 验证其他方法框架存在但未实现

4. **根据测试结果调整代码**
   - 修复识别错误
   - 优化算法

5. **后续Phase（用户确认后）**
   - 实现二买
   - 实现三买
   - 实现所有卖点
