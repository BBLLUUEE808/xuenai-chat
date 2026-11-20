# 雪之下雪乃 AI 伴侣

基于 Streamlit + DeepSeek 的角色扮演聊天应用，支持流式回复、多会话保存与自定义人设。

## 本地运行

1. 安装依赖

```bash
pip install -r requirements.txt
```

2. 准备素材

将以下图片放到项目根目录（与 `app.py` 同级）。缺图不会报错，只是没有背景和头像：

- `雪之下校服.jpg` —— 页面背景
- `猫咪1.png` —— 左上角 Logo
- `雪之下1.png` —— 助手头像
- `wo.jpg` —— 用户头像

3. 配置密钥

方式一，环境变量：

```bash
export DEEPSEEK_API_KEY="sk-xxx"
```

方式二，创建 `.env` 并用 python-dotenv 加载，或在启动前 export。`.env` 已在 `.gitignore` 中，不会被提交。

4. 启动

```bash
streamlit run app.py
```

## 可选环境变量

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `DEEPSEEK_API_KEY` | 无 | 必填 |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | 如使用代理可覆盖 |
| `DEEPSEEK_MODEL` | `deepseek-chat` | 需要思路链可改为 `deepseek-reasoner` |

## 部署到 Streamlit Community Cloud

1. 把本仓库推到 GitHub（必须为 Public）
2. 打开 [share.streamlit.io](https://share.streamlit.io)，用 GitHub 登录，New app 选择本仓库，Main file path 填 `app.py`
3. 在 App 的 Settings → Secrets 中填入：

```toml
DEEPSEEK_API_KEY = "sk-xxx"
```

4. 部署完成后得到形如 `https://xxx.streamlit.app` 的公开链接，任何人可直接访问

## 设计说明

- **聊天记录按访问者隔离**：每个浏览器会生成一个 uid 写入 URL 的 `u` 参数，会话文件存放在 `sessions/<uid>/` 下，不同访问者互相看不到对方的历史。
- **云端存储是临时的**：容器重启后 `sessions/` 内容会丢失，这是免费实例的固有限制。
- **免费实例会休眠**：长时间无人访问后进入睡眠，再次打开需等待唤醒。

## 声明

角色与图片素材版权归原作者及版权方所有，本项目仅供个人学习与交流使用，请勿用于商业用途。

> （注：部分内容由豆包 AI 生成）