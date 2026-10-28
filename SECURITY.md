# Security Policy / 安全策略

ds-search has no server component, no telemetry, and no analytics. This document describes exactly where your API key lives, where it travels, and what to do if it leaks.

## 密钥的存放与流动

- 密钥只保存在本机：环境变量 `DEEPSEEK_API_KEY`、`~/.ds-search/.env`、或 `<技能目录>/.env`（优先级依次降低，`-k` 参数最高）。
- 密钥只经 HTTPS 直发 `api.deepseek.com`（Search/Fetch 接口的 `Authorization` 头）。除 DeepSeek 官方端点外，不向任何第三方发送任何数据。
- 无遥测、无埋点、无崩溃上报；本项目没有也不需要任何服务器组件。

## 密钥卫生六不清单（实现承诺）

1. 不进日志——CLI 不打印任何包含密钥的诊断信息；
2. 不进缓存内容——`~/.ds-search/cache/` 只存 API 响应与调用元数据，绝不存密钥；
3. 不进错误信息——401 等错误输出只含指引文案；
4. 不进 fixtures——`tests/fixtures/` 中的录制响应均经脱敏检查（`tests/test_schema.py` 以 `sk-[a-f0-9]{16,}` 正则守护）；
5. 不进 `--stats` 输出——统计只含次数/token/耗时/命中率；
6. 不进 git——提交前以 `git grep` 核查；`.gitignore` 拦截一切 `.env`。

## 泄漏救济

若怀疑密钥泄漏（如误提交、误贴到公开场合）：

1. 立即到 [platform.deepseek.com](https://platform.deepseek.com) 控制台**吊销该 Key 并新建**（吊销即刻生效，旧 Key 全部失效）；
2. 更新 `~/.ds-search/.env` 为新 Key；
3. 若密钥曾进入 git 历史，仅删除文件不够——历史提交仍可被检索，**必须以吊销为准**，必要时清理历史（filter-repo / 重建仓库）。

## 供应链

- 零第三方依赖：CLI 仅使用 Python 标准库（urllib/json/hashlib 等），无 pip install 步骤，无传递性依赖风险。
- 安装器只把 `skills/ds-search/` 一个自包含目录复制到目标 Agent 的技能目录，不执行远程脚本、不修改系统配置。

## 报告漏洞

请通过 GitCode 仓库 issue 私密描述（或联系仓库所有者），不要在公开 issue 中附密钥或可复现的请求样例。
