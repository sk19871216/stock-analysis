# 股票数据分析系统

## 项目结构

```
股票2/
├── data/                          # 数据文件目录
│   ├── stock_data.db             # SQLite数据库（包含股票日线数据）
│   └── 无数据股票列表.txt         # 无数据股票代码列表
│
├── stock_fetch/                   # 股票数据获取模块
│   └── fetch_stock_data.py       # 从通达信服务器获取股票数据
│
├── fenxing/                       # 分型分析模块
│   ├── fenxing_debug.py          # 分型算法调试版本
│   ├── display_fenxing.py       # 分型结果显示（中文）
│   └── show_fenxing.py           # 分型结果显示（英文）
│
├── database/                      # 数据库管理模块
│   ├── check_db.py               # 查看数据库结构
│   ├── check_specific_stocks.py   # 检查特定股票数据
│   ├── delete_no_data_stocks.py  # 删除无数据股票
│   ├── preview_stocks.py         # 预览股票数据
│   ├── verify_deletion.py        # 验证删除操作
│   └── final_report.py          # 生成最终报告
│
├── results/                       # 结果输出目录
│   ├── fenxing_result.txt        # 分型分析结果
│   └── fenxing_result_000016.txt # 000016股票分型结果
│
└── README.md                      # 项目说明文档

```

## 模块说明

### 1. 数据获取 (stock_fetch/)
**功能**: 从通达信行情服务器获取股票日线数据

**使用方法**:
```bash
cd stock_fetch
python fetch_stock_data.py
```

**说明**:
- 使用 mootdx 库连接通达信服务器
- 自动获取股票列表中的所有股票
- 数据包含: 日期、开盘价、收盘价、最高价、最低价、成交量、成交额等
- 支持 2026年至今的数据

### 2. 分型分析 (fenxing/)
**功能**: 基于缠论的分型识别算法

**使用方法**:
```bash
# 方法1: 调试版本（显示详细处理过程）
cd fenxing
python fenxing_debug.py

# 方法2: 显示结果（修改代码中的股票代码）
python display_fenxing.py

# 方法3: 生成结果文件
python show_fenxing.py
```

**说明**:
- Step1: 识别分型候选，处理K线包含关系，去除共享边界
- Step2: 合并相邻同类型分型
- Step3: 判断分型间隔（可选）

### 3. 数据库管理 (database/)
**功能**: 数据库维护和数据清理

**使用方法**:
```bash
# 查看数据库结构
cd database
python check_db.py

# 检查特定股票
python check_specific_stocks.py

# 预览股票数据
python preview_stocks.py

# 删除无数据股票
python delete_no_data_stocks.py

# 验证删除操作
python verify_deletion.py

# 生成最终报告
python final_report.py
```

### 4. 数据文件 (data/)
**内容**:
- `stock_data.db`: SQLite数据库，包含以下表:
  - `daily`: 股票日线数据
  - `stock_list`: 股票列表

**数据库结构**:
```sql
-- daily 表
CREATE TABLE daily (
    id INTEGER PRIMARY KEY,
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

-- stock_list 表
CREATE TABLE stock_list (
    code TEXT PRIMARY KEY,
    fetched INTEGER,
    last_fetch TEXT
);
```

## 快速开始

### 1. 获取股票数据
```bash
cd stock_fetch
python fetch_stock_data.py
```

### 2. 分析股票分型
```bash
cd fenxing
# 编辑 fenxing_debug.py 中的股票代码（默认: 000016）
python fenxing_debug.py
```

### 3. 查看分型结果
结果会直接显示在终端，同时保存到 `results/` 目录

## 注意事项

1. **数据库路径**: 所有脚本默认使用 `data/stock_data.db`，无需额外配置
2. **编码问题**: 脚本使用 UTF-8 编码，确保数据文件也是 UTF-8 编码
3. **数据更新**: 建议定期运行 `fetch_stock_data.py` 更新数据
4. **分型参数**: 可根据需要调整分型算法的参数

## 技术栈

- **数据库**: SQLite3
- **数据获取**: mootdx (通达信行情接口)
- **数据处理**: pandas
- **分析算法**: 缠论分型算法

## 作者

股票数据分析系统 - 基于缠论的分型分析工具

## 许可证

MIT License
