# Excel 表格操作速查

> 从 `xlsx-guide` skill 降级（SQS 47.2/100 — 主题偏向 productivity 包）
> 来源: `~/.hermes/skills/xlsx-guide/SKILL.md`

## 基本用法

```bash
pip install openpyxl
```

```python
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

wb = Workbook()
ws = wb.active
ws.title = "工作表1"

# 写入数据
ws['A1'] = '标题'
ws['A1'].font = Font(bold=True, size=14)
ws['A1'].alignment = Alignment(horizontal='center')

# 批量写入
data = [['姓名', '分数'], ['张三', 95], ['李四', 88]]
for row in data:
    ws.append(row)

# 保存
wb.save('output.xlsx')
```

> ⚠️ **注意**：本技能偏向 productivity（通用生产力），未来可能迁移到独立的 productivity 能力包。
