# MACD面积与量柱比较功能实现计划

## 任务目标
在现有分型脚本基础上，增加MACD面积和量柱高度的比较功能。

## 重要参数
- **分型查询天数**: 120天 (增加容错性)

## 需求分析

### 趋势定义
- **下降趋势**: 顶分型 → 底分型
- **上升趋势**: 底分型 → 顶分型

### 比较内容
比较两个相邻的**相同趋势**的：
1. **MACD面积**: 趋势段内MACD柱的面积总和
2. **量柱高度**: 趋势段内最大MACD柱的高度

## 实现步骤

### Step 1: 创建MACD计算模块
- 创建 `macd.py` 在 `fenxing/` 目录下
- 实现MACD指标计算函数
  - EMA12, EMA26 计算
  - DIF, DEA, MACD柱 计算
- 实现MACD面积计算函数
- 实现量柱高度提取函数

### Step 2: 修改分型脚本
- 创建新脚本 `fenxing_with_macd.py` 或增强现有脚本
- 在分型识别后增加趋势段提取功能
- 将分型序列转换为趋势段列表

### Step 3: 实现趋势段提取
- 识别所有趋势段: `[(起始分型索引, 结束分型索引, 趋势类型), ...]`
- 趋势类型: '下降' 或 '上升'
- 提取趋势段对应的K线范围

### Step 4: 计算趋势段MACD指标
- 对每个趋势段计算:
  - MACD面积 = sum(MACD柱值 × 对应成交量) 或 sum(|MACD柱|)
  - 最大量柱高度 = max(|DIF - DEA|)
- 存储结果: `[(趋势段, 面积, 量柱高度), ...]`

### Step 5: 实现相邻趋势比较
- 比较相邻相同趋势的MACD指标
- 输出格式:
  ```
  下降趋势1: 面积=X, 量柱高度=Y
  下降趋势2: 面积=X2, 量柱高度=Y2
  比较结果: 趋势1 vs 趋势2
  ```

### Step 6: 优化和测试
- 测试脚本运行
- 添加命令行参数支持
- 输出结果保存到 `results/` 目录

## 数据结构设计

```python
# 分型结果
fenxing_list = [
    (idx, '顶'/'底', {'date': ..., 'high': ..., 'low': ...}),
    ...
]

# 趋势段
trend_segment = {
    'type': '下降'/'上升',
    'start_idx': 分型索引,
    'end_idx': 分型索引,
    'klines': [K线列表],
    'macd_area': float,
    'max_bar_height': float
}
```

## 关键算法

### MACD计算
```python
def calculate_macd(prices, fast=12, slow=26, signal=9):
    # 计算EMA
    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)
    dif = ema_fast - ema_slow
    dea = calculate_ema(dif, signal)
    macd_hist = (dif - dea) * 2
    return dif, dea, macd_hist
```

### 面积计算
```python
def calculate_macd_area(macd_hist, volumes):
    # 方法1: 简单求和
    area = sum(abs(macd_hist))
    # 方法2: 加权求和（考虑成交量）
    # area = sum(abs(macd_hist) * volumes)
    return area
```

## 文件结构
```
fenxing/
├── fenxing_debug.py      # 原始分型脚本
├── macd.py              # MACD计算模块 (新)
├── fenxing_with_macd.py # 增强版分型脚本 (新)
└── display_fenxing.py   # 结果显示脚本
```

## 输出示例
```
股票代码: 000016
分型序列: 顶-底-顶-底-顶

趋势段分析:
1. 下降趋势 (2026-01-21 ~ 2026-01-27)
   - MACD面积: 0.156
   - 最大量柱高度: 0.089

2. 上升趋势 (2026-01-27 ~ 2026-03-23)
   - MACD面积: 0.234
   - 最大量柱高度: 0.121

相邻趋势比较:
- 下降趋势1 vs 下降趋势2:
  面积变化: -33.3% (背离/同步)
  量柱变化: -26.5%
```

## 实施顺序
1. 创建 `macd.py` 模块
2. 创建 `fenxing_with_macd.py` 主脚本
3. 测试并调试
4. 添加命令行参数
5. 输出优化
