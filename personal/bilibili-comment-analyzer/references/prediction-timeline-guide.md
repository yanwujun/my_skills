# 预测时间轴图生成指南

从UP主动态/视频中提取预测性内容，生成时间轴可视化图表并加入HTML报告。

## 适用场景

- UP主是**财经/股票/大宗商品**分析类（如"战国时代_姜汁汽水"）
- UP主动态中包含明确价格点位、方向判断（"XX达到XX点"、"XX会回调/上涨"）
- 需要可视化展示UP主的预测历史和时间线

## 提取预测数据

### 从动态文本中识别

常见预测模式：

| 模式 | 示例 |
|------|------|
| 明确价位 | "白银已到我的杠杆止盈点位90" |
| 方向判断 | "5000~5200肯定有回调" |
| 时间+判断 | "13日到15日，川普访华，A股创新高" |
| 回顾型预测 | "24年10月28日，认为A股25年达到4000" |

### 数据结构

每条预测记录格式：

```python
predictions = [
    # ( (year, month, day), asset_category, short_label, detail_description, accuracy_status )
    ((2024, 10, 28), 'A股', 'A股25年达4000点',
     '预判A股在2025年达到4000点',
     '✅ 2025.10 准确'),
]
```

| 字段 | 说明 |
|------|------|
| date | `(year, month, day)` 三元组 |
| asset | 资产类别，用于分色，推荐：黄金/白银/A股/美股/港股/农产品/铜 |
| label | 简短标签（10字以内，显示在时间轴节点上） |
| detail | 详细描述（在时间轴标签下方显示） |
| accuracy | ✅已兑现 / 🔲待验证 |

### 资产类别颜色定义

```python
CAT_COLORS = {
    '黄金': '#FFD700',
    '黄金/白银': '#FFA500',
    '白银': '#C0C0C0',
    'A股': '#FF4444',
    '美股': '#4A90D9',
    '港股': '#00BFFF',
    '农产品': '#228B22',
    '铜': '#CD7F32',
}
```

## 生成图表

### 字体设置（关键！否则中文变方块）

```python
import matplotlib.font_manager as fm

font_path = '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'
font_prop = fm.FontProperties(fname=font_path)
plt.rcParams['font.family'] = font_prop.get_name()
plt.rcParams['axes.unicode_minus'] = False
fm.fontManager.addfont(font_path)
```

### 图表参数

| 参数 | 推荐值 |
|------|--------|
| figsize | `(20, 12)` |
| dpi | 150 |
| 时间轴范围 | 约从最早预测前3个月到当前日期后1个月 |
| 节点间距 | 时间相差 < 15天时自动错开Y轴位置 |
| 背景色 | `#1a1a2e`（深色主题） |
| Y轴偏移 | 采用 `1 + (i % 3) * 1.8` 交替上下排列 |

### 核心渲染逻辑

```python
base_date = date(2024, 8, 1)  # 时间轴起点

def date_to_x(d):
    return (d - base_date).days

# 绘制时间轴主线
ax.axhline(y=0, color='#4a4a6a', linewidth=2, zorder=1)

# 每个预测点
for i, ((y, m, day), asset, label, detail, accuracy) in enumerate(predictions):
    dt = date(y, m, day)
    x = date_to_x(dt)
    color = CAT_COLORS.get(asset, '#888888')
    
    # 交替上下排列，避免重叠
    direction = 1 if i % 2 == 0 else -1
    y_pos = (1 + (i % 3) * 1.8) * direction
    
    # 节点圆点
    ax.scatter(x, 0, s=160, color=color, edgecolors='white', linewidth=2, zorder=5)
    
    # 连接线
    ax.plot([x, x], [0, y_pos], color=color, linewidth=1.5, alpha=0.6)
    
    # 标签
    ax.annotate(f'{dt.strftime("%Y/%m/%d")}\n[{asset}] {label}',
                xy=(x, 0), xytext=(x + 3, y_pos),
                fontsize=9, color='#e0e0e0', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5', facecolor=color,
                         edgecolor='white', alpha=0.15),
                arrowprops=dict(arrowstyle='->', color=color, lw=1.2, alpha=0.7))
```

## 嵌入HTML报告

保存 `prediction_timeline.png` 到报告目录后，在 `report.html` 中插入：

```html
<div class="section">
    <h2>📈 UP主预测时间轴</h2>
    <p style="color:#666;font-size:13px;">
        按资产类别分色：
        <span style="color:#FFD700">■</span> 黄金
        <span style="color:#C0C0C0">■</span> 白银 ...
    </p>
    <div class="chart-card full">
        <img src="prediction_timeline.png" alt="预测时间轴" style="width:100%;">
    </div>
</div>
```

## 注意事项

1. **预测数据需人工标注** — 目前自动提取准确度不够，建议人工阅读动态后手动构造预测列表
2. **时间跨度** — 如果覆盖1年以上，X轴刻度建议按月显示
3. **已兑现标记** — 用 ✅ 标记已达成的预测，收益增加说服力
4. **避免标签重叠** — 用 `(i % 3) * 1.8` 轮换3个垂直位置，配合奇偶上下翻转
5. **字体** — 保存前务必确认 `plt.savefig` 没有报 `Glyph missing from font` 警告
