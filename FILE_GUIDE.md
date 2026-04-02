# 股票数据分析系统 - 文件功能指南

> 本系统是基于缠论(K线分型)的股票技术分析工具，包含数据获取、分型识别、买卖点检测等功能。

---

## 📁 项目目录结构

```
股票2/
├── stock_fetch/          # 数据获取模块
├── database/            # 数据库管理模块
├── fenxing/             # 核心分析模块（缠论分型）
├── data/                # 数据存储目录
├── results/             # 分析结果输出目录
├── push_to_github.py    # GitHub推送工具
└── README.md            # 项目说明文档
```

---

## 📥 stock_fetch/ - 数据获取模块

### fetch_stock_data.py
**功能**: 从通达信行情服务器获取股票日线数据

**使用方法**:
```bash
cd stock_fetch
python fetch_stock_data.py
```

**说明**:
- 使用 `mootdx` 库连接通达信服务器
- 自动获取股票列表中的所有股票
- 数据包含: 日期、开盘价、收盘价、最高价、最低价、成交量、成交额、振幅、涨跌幅等
- 支持获取2026年至今的数据

---

## 🗄️ database/ - 数据库管理模块

### check_db.py
**功能**: 查看数据库结构

**使用方法**:
```bash
cd database
python check_db.py
```

**输出**: 显示所有表名、列信息、记录数量

---

### check_specific_stocks.py
**功能**: 检查特定股票代码在数据库中的存在情况

**使用方法**:
```bash
cd database
python check_specific_stocks.py
```

**用途**: 验证特定股票是否已入库

---

### preview_stocks.py
**功能**: 预览无数据股票列表中的股票在数据库的状态

**使用方法**:
```bash
cd database
python preview_stocks.py
```

---

### delete_no_data_stocks.py
**功能**: 删除无数据股票记录

**使用方法**:
```bash
cd database
python delete_no_data_stocks.py
```

**注意**: 需配合 `data/无数据股票列表.txt` 使用

---

### verify_deletion.py
**功能**: 验证删除操作的结果

**使用方法**:
```bash
cd database
python verify_deletion.py
```

---

### final_report.py
**功能**: 生成数据库清理操作的总结报告

**使用方法**:
```bash
cd database
python final_report.py
```

---

## 📈 fenxing/ - 核心分析模块（缠论分型）

这是系统的核心模块，包含分型识别、背驰检测、买卖点判断等功能。

### 🔬 核心库文件

#### macd.py
**功能**: MACD指标计算模块

**主要函数**:
- `calculate_macd()` - 计算MACD、DIF、DEA
- `calculate_macd_area()` - 计算MACD面积
- `get_max_bar_height()` - 获取最大量柱高度
- `detect_divergence()` - 检测背离
- `add_macd_to_dataframe()` - 为DataFrame添加MACD列

---

#### chanlun_signals.py ⭐⭐⭐
**功能**: 缠论买卖点识别核心模块

**重要更新** (最新修改):
1. 只有背驰才能算1买
2. 价格新低标记为"是"/"否"
3. 相邻下降趋势最低价差距<2%标记为"伪1买"
4. 条件ABC清晰描述
5. 1买2买不能重合

**主要函数**:
- `extract_trend_data()` - 提取趋势段数据
- `detect_divergence()` - 检测背驰（底背驰/顶背驰）
- `identify_first_buy()` - 识别1买（第一买点）
- `identify_second_buy()` - 识别2买（第二买点）

**MACD背驰条件**（满足任一即可）:
- **条件A**: 绿柱面积减少（当前下跌段 < 前一段）
- **条件B**: 绿柱高度降低（当前最低绿柱 < 前一段最低绿柱）
- **条件C**: 下跌力度减弱（价格跌幅/天数）

---

#### fenxing_with_macd.py
**功能**: 分型+MACD综合分析脚本

**主要函数**:
- `find_fenxing()` - 找分型
- `merge_same_type()` - 合并相邻同类型分型
- `extract_trends()` - 从分型列表提取趋势段

---

### 📊 分型识别脚本

#### fenxing_debug.py
**功能**: 带详细注释的调试版本，分步显示分型识别过程

**使用方法**:
```bash
cd fenxing
python fenxing_debug.py
```

**输出**:
- Step1: 处理包含关系 + 去共享边界
- Step2: 合并相邻同类型
- Step3: 判断间隔

---

#### display_fenxing.py
**功能**: 中文输出分型结果

**使用方法**:
```bash
cd fenxing
python display_fenxing.py
```

---

#### show_fenxing.py
**功能**: 英文输出分型结果，结果保存到文件

**使用方法**:
```bash
cd fenxing
python show_fenxing.py
```

**输出文件**: `results/fenxing_result.txt`

---

### 🛒 个股分析脚本

#### analyze_000006.py ⭐
**功能**: 000006股票完整分析脚本（最新增强版）

**使用方法**:
```bash
cd fenxing
python analyze_000006.py
```

**分析内容**:
- 数据概况（范围、数量、分型数）
- 趋势段分析
- 1买信号（含背驰条件、伪1买判断、次日阳线）
- 2买信号（含相关1买、回调信息、次日阳线）

**输出示例**:
```
【1买 #1】
   日期: 2025-09-15
   价格: 7.23
   价格新低: 否
   伪1买: 否
   与前段最低价差距: 2.70%
   MACD背驰条件:
      - 条件A (绿柱面积减少): 绿柱面积减少
      - 条件B (绿柱高度降低): 绿柱高度降低
      - 条件C (下跌力度减弱): 下跌力度未减弱
   次日阳线: 是 (2.01%)
```

---

#### analyze_000001_period.py
**功能**: 000001特定时间段分析（2025-08-01 ~ 2026-03-30）

**使用方法**:
```bash
cd fenxing
python analyze_000001_period.py
```

---

#### analyze_000002.py
**功能**: 000002股票1买2买分析（2025-08-01至今）

**使用方法**:
```bash
cd fenxing
python analyze_000002.py
```

---

#### analyze_002466.py
**功能**: 002466（天齐锂业）一买分析

**使用方法**:
```bash
cd fenxing
python analyze_002466.py
```

---

### 🔍 批量测试脚本

#### find_second_buy.py
**功能**: 批量搜索有2买信号的股票

**使用方法**:
```bash
cd fenxing
python find_second_buy.py
```

**说明**: 按数据库顺序测试，找到2只有2买的股票就停止

---

#### find_second_buy_csv.py
**功能**: 从CSV文件批量搜索2买信号

---

### 🧪 测试和调试脚本

| 文件 | 功能 |
|------|------|
| `test_000004.py` | 测试000004数据加载 |
| `test_000006.py` | 测试000006数据加载 |
| `test_chanlun_signals.py` | 测试chanlun_signals模块 |
| `debug_second_buy.py` | 调试2买识别逻辑 |
| `check_dates.py` | 检查数据日期范围 |
| `analyze_first_buy.py` | 专门分析1买信号 |
| `analyze_000004.py` | 分析000004股票 |

---

### 📦 其他文件

| 文件 | 功能 |
|------|------|
| `chanlun_signals_backup.py` | chanlun_signals备份版本 |
| `chanlun_signals_fixed.py` | chanlun_signals修复版本 |

---

## 🗂️ data/ - 数据目录

| 文件 | 说明 |
|------|------|
| `stock_data.db` | SQLite数据库文件（实际存在但不在列表中） |
| `无数据股票列表.txt` | 没有数据的股票代码列表 |

### 数据库结构

```sql
-- daily 表（股票日线数据）
CREATE TABLE daily (
    date TEXT,
    code TEXT,
    open REAL,
    close REAL,
    high REAL,
    low REAL,
    volume REAL,
    amount REAL,
    amplitude REAL,
    pct_chg REAL,
    chg REAL,
    turnover REAL,
    valid_data INTEGER
);

-- stock_list 表（股票列表）
CREATE TABLE stock_list (
    code TEXT PRIMARY KEY,
    fetched INTEGER,
    last_fetch TEXT
);
```

---

## 📤 results/ - 结果输出目录

| 文件 | 说明 |
|------|------|
| `fenxing_result.txt` | 分型分析结果 |
| `fenxing_result_000016.txt` | 000016股票分型结果 |
| `fenxing_macd_*.txt` | 分型+MACD综合分析结果 |

---

## 🚀 快速开始

### 1. 分析单只股票（推荐方式）

```bash
cd fenxing
python analyze_000006.py
```

修改脚本中的股票代码即可分析其他股票：
```python
csv_path = r'D:\claude_code\股票\stock_data_2\000006.csv'
start_date = '2025-08-01'
end_date = '2026-04-02'
```

---

### 2. 批量搜索2买信号

```bash
cd fenxing
python find_second_buy.py
```

---

### 3. 查看分型识别过程

```bash
cd fenxing
python fenxing_debug.py
```

---

## 📖 缠论核心概念

### 分型
K线图中，顶分型是中间K线最高、相邻K线低于中间K线；底分型是中间K线最低、相邻K线高于中间K线。

### 趋势
- **下降趋势**: 顶分型 → 底分型
- **上升趋势**: 底分型 → 顶分型

### 背驰
当前趋势段的力度比前一段减弱，表现为MACD指标的变化：
- 底背驰: 绿柱面积/高度减少，下跌力度减弱
- 顶背驰: 红柱面积/高度减少，上升力度减弱

### 买卖点
- **1买**: 下降趋势结束时的底背驰买点
- **2买**: 1买后上升回调、不破1买的买点

---

## ⚙️ 配置说明

### 数据路径
```python
DATA_DIR = r'D:\claude_code\股票\stock_data_2'
```

### 数据库路径
所有脚本默认使用 `../data/stock_data.db`

### MACD参数
默认参数: fast=12, slow=26, signal=9

---

## 📝 注意事项

1. **编码问题**: 脚本使用 UTF-8 编码
2. **数据依赖**: 确保CSV数据文件存在
3. **伪1买**: 与前段最低价差距<2%的1买标记为"伪1买"
4. **背驰判断**: 必须满足条件A/B/C任一才能算背驰

---

## 🔧 常见问题

**Q: 为什么没有识别到1买？**
A: 检查数据是否足够（至少30条），且是否有满足背驰条件的下降趋势。

**Q: 伪1买是什么意思？**
A: 与前一个下降趋势最低价差距<2%，可能是同一个低点被识别为两个趋势的结束点。

**Q: 如何修改分析的时间范围？**
A: 修改脚本中的 `start_date` 和 `end_date` 变量。

---

## 📞 联系与支持

本系统为缠论技术分析工具，仅供参考，不构成投资建议。
