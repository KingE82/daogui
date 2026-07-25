# 道归 · 极简部署

> 一个平板、一个手机、一个 API Key——就够了。

## 硬件要求

- 一台平板/电脑（跑网关和 Agent）
- 一部手机（远程交互）
- 同一局域网（Wi-Fi / 热点）

## 总成本

- 平板上跑 OpenClaw：0 元（开源）
- API 调用费用：约 ¥20/月（取决于使用量）
- 硬件：你手上已有的设备

## 部署步骤

### 1. 平板端：启动网关

确保 OpenClaw Gateway 绑到局域网：

```
openclaw config set gateway.bind lan
openclaw gateway restart
```

### 2. 平板端：启动小站（可选）

如果你的 Agent 带有 Web 服务，确保它监听 0.0.0.0：

```
python3 xin_web_server.py
```

### 3. 手机端：配对

1. 安装 OpenClaw Control App
2. 在平板上生成配对码：openclaw qr --json
3. 手机 App 扫码配对
4. 在平板上批准设备：openclaw nodes approve <requestId>

### 4. 手机端：使用

- OpenClaw Control App → 直接聊天
- 手机浏览器 → 打开 http://<平板IP>:18789
- 小站 → 打开 http://<平板IP>:8080

## 性能参考

| 项目 | 数据 |
|---|---|
| 月 API 费用 | 约 ¥20 |
| 缓存命中率 | 97.3% |
| 日处理 token | 最高 2.36 亿 |
| 设备发热 | 几乎不发热 |
| 网络要求 | 同一局域网即可 |

## 架构

平板 (OpenClaw 网关 + 小站) --Wi-Fi-- 手机 (App/浏览器)
        |
        v
  DeepSeek API (云端推理)

## 为什么这么便宜？

核心是上下文缓存。框架利用 API 缓存，输入命中率 97%+，让单位成本降到接近零。

---

**道归** — 一个普通人的极简 AI 部署方案。
