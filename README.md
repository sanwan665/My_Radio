# 🎵 AI 智能音乐电台

一个基于 Python 的智能音乐电台，支持天气感知、AI 对话和网易云音乐集成。

---

## ✨ 功能特性

- 🤖 **AI 智能对话** - 与大模型自然对话，理解用户意图
- 🎵 **智能推荐** - 根据天气、时间、心情和对话内容推荐歌曲
- 🌤️ **天气感知** - 根据当前天气推荐适合的音乐
- ☁️ **网易云同步** - 自动同步你的网易云音乐歌单到本地数据库
- 💾 **本地数据库** - 轻量级 SQLite 数据库管理歌曲
- 🎧 **在线播放** - 通过网易云 API 获取播放链接并播放

---

## 🚀 快速开始

### 1️⃣ 安装 Python

确保安装了 Python 3.8+（推荐 3.10+）：
```bash
python --version
```

### 2️⃣ 安装依赖

```bash
cd My_Radio
pip install -r requirements.txt
```

### 3️⃣ 配置环境

#### 方式一：使用模板配置（推荐）

1. 复制 `.env.example` 并重命名为 `.env`
2. 打开 `.env` 文件，填写以下配置：

```env
# 🎵 网易云配置（必须）
# 获取方式：登录网易云网页版 → F12 → Application → Cookies → 复制整个 Cookie 值
NETEASE_COOKIE=你的网易云Cookie

# 🤖 大模型配置（必须才能使用AI对话）
# 如果没有自己的API，可以暂时留空（部分功能受限）
LLM_API_KEY=你的大模型API密钥

# 🌤️ 天气API（可选，已有默认配置）
# 默认使用内置的天气服务，如需更准确的天气可填写自己的API
WEATHER_API_KEY=
CITY=Shanghai
```

#### 方式二：手动创建配置文件

如果没有 `.env.example`，手动创建 `.env` 文件：

```env
# 网易云 Cookie（必须）
NETEASE_COOKIE=

# 大模型 API（必须）
LLM_API_KEY=

# 天气配置（可选）
WEATHER_API_KEY=
CITY=Shanghai
```

### 4️⃣ 同步网易云歌单

首次使用需要同步你的网易云歌单到本地数据库：

```bash
python sync.py
```

同步完成后，你的收藏歌曲会被保存到本地数据库中。

### 5️⃣ 运行程序

```bash
python main.py
```

---

## 📖 使用说明

### 🤖 AI 对话模式

在主菜单输入 `对话` 进入 AI 对话模式：

```
欢迎使用 AI 智能音乐电台！
请输入命令（推荐/对话/列表/帮助/退出）: 对话

你> 今天天气真好
AI> 阳光明媚的日子，来首轻快的音乐怎么样？

🎵 为你推荐: 晴天 - 周杰伦
🎧 要播放这首歌吗？: 好的
正在播放...
```

**对话功能：**
- 与 AI 自然聊天
- AI 会根据对话内容推荐歌曲
- 支持自然语言回答（如"好的呀"、"算了不用"等）

### 📋 命令行模式

主菜单支持以下命令：

| 命令 | 功能 |
|------|------|
| `推荐` | 获取智能音乐推荐 |
| `对话` | 进入 AI 对话模式 |
| `列表` | 查看数据库中的歌曲 |
| `搜索 [关键词]` | 搜索歌曲 |
| `同步` | 重新同步网易云歌单 |
| `帮助` | 显示所有命令 |
| `退出` | 退出程序 |

### 🎧 播放控制

- 播放新歌曲时，当前歌曲会自动停止
- 歌曲播放完成后自动停止
- 临时文件会自动清理，不会占用磁盘空间

---

## 🔧 配置说明

### 网易云 Cookie 获取方法

1. 打开浏览器，访问 [网易云音乐网页版](https://music.163.com)
2. 登录你的账号
3. 按 `F12` 打开开发者工具
4. 切换到 `Application` 标签页
5. 在左侧找到 `Cookies` → `https://music.163.com`
6. 右键点击任意 Cookie，选择 `Copy` → `Copy all cookies`
7. 粘贴到 `.env` 文件的 `NETEASE_COOKIE` 字段

### 大模型配置

支持多种大模型，只需配置 `LLM_API_KEY`：

```env
# 阿里云千问（推荐）
LLM_API_KEY=sk-xxx

# OpenAI
LLM_API_KEY=sk-xxx

# DeepSeek
LLM_API_KEY=sk-xxx
```

### 天气配置

```env
# 使用默认天气服务（无需配置）
WEATHER_API_KEY=

# 使用 OpenWeatherMap（可选）
WEATHER_API_KEY=your_openweather_key
CITY=Beijing
```

---

## 📁 项目结构

```
My_Radio/
├── main.py                    # 主程序入口
├── database.py               # 数据库管理模块
├── sync.py                   # 网易云歌单同步
├── requirements.txt          # 依赖列表
├── .env                      # 环境配置（用户创建）
├── .env.example              # 配置模板
├── music.db                  # 歌曲数据库（自动生成）
├── preferences.db            # 用户偏好数据库（自动生成）
├── src/
│   ├── recommender.py        # 推荐系统核心
│   ├── player.py             # 音乐播放器
│   ├── command_parser.py     # 命令解析器
│   ├── aliyun_llm.py         # 大模型客户端
│   ├── weather_service.py    # 天气服务
│   ├── sentiment_analysis.py # 情绪分析
│   ├── netease_openapi.py    # 网易云开放平台API
│   └── preference_store.py   # 偏好存储
└── templates/
    └── index.html            # Web界面模板
```

---

## ❓ 常见问题

### Q1: Cookie 过期了怎么办？

A: 重新登录网易云网页版，按照上面的步骤重新获取 Cookie 并更新 `.env` 文件。

### Q2: 播放时提示"获取播放链接失败"？

A: 可能是 Cookie 过期或网易云 API 限制。请尝试重新获取 Cookie。

### Q3: AI 对话功能无法使用？

A: 请确保正确配置了 `LLM_API_KEY`。如果没有 API，可以暂时使用命令行模式。

### Q4: 如何同步特定歌单？

A: 当前版本默认同步"我喜欢的音乐"歌单。如需同步其他歌单，请修改 `sync.py` 文件。

---

## 📝 更新日志

### v1.0.0
- ✅ AI 对话模式
- ✅ 天气感知推荐
- ✅ 网易云歌单同步
- ✅ 在线音乐播放
- ✅ 命令行界面

---

## 📄 许可证

MIT License

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**享受音乐，享受生活！** 🎶