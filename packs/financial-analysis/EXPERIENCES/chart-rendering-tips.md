---
type: pitfall
skill_ref: financial-analyst
keywords: [matplotlib, chart, chinese-font, headless, rendering]
---

# 金融图表渲染陷阱

## 无头渲染
在服务器环境（无显示器）必须设置：
```python
import matplotlib
matplotlib.use('Agg')  # 必须在导入 pyplot 之前
```
否则报错 `_tkinter.TclError: no display name and no $DISPLAY environment variable`

## 中文字体
| 服务器类型 | 常见字体 | 安装方法 |
|:-----------|:---------|:---------|
| Ubuntu | WenQuanYi Zen Hei | `apt install fonts-wqy-zenhei` |
| 通用 | SimHei, Noto Sans CJK | pip 安装或系统级安装 |

字体回退链：
```python
plt.rcParams['font.sans-serif'] = ['WenQuanYi Zen Hei', 'SimHei', 'Arial Unicode MS']
```

## 图表布局
- 4 面板图（K线+成交量+MACD+RSI）尺寸推荐 `(12, 10)`，dpi 150
- 日期轴格式化：`mdates.DateFormatter('%Y-%m-%d')`
- 用 `fig.autofmt_xdate()` 自动旋转日期标签

## 交付顺序
1. 先发送图表图片（让用户看到）
2. 再发送文字分析（让用户理解）
