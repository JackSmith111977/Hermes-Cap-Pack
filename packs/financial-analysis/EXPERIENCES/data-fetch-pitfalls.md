---
type: pitfall
skill_ref: financial-analyst
keywords: [akshare, stock, data, proxy, network]
---

# 金融数据获取陷阱

## akshare 数据源
- 大部分接口直连可用（国内服务器），无需代理
- 部分国外数据源需代理（美股等）
- 建议用 `try/except` 捕获数据请求失败，回退本地缓存

## 数据格式
| 字段 | 注意事项 |
|:-----|:---------|
| 日期 | akshare 返回 YYYY-MM-DD 字符串，需 `pd.to_datetime()` |
| 成交量 | 单位是手（1手=100股），需确认 |
| 复权 | 推荐 `qfq`（前复权），`hfq`（后复权），`None`（不复权） |

## 股票代码
- A 股：6 位数字，如 `000001`（平安银行）
- 加 `sh`/`sz` 前缀时注意接口要求
- `stock_zh_a_hist` 接受纯数字代码（不带前缀）

## 数据过期
- 非交易日/停牌日返回空数据，需检查 `df.empty`
- 节假日期间无新数据，直接使用最近交易日数据
