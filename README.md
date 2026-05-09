# 生猪养殖行业分析智能体

基于 RAG（检索增强生成）技术的 2026 年生猪养殖行业分析工具。自动检索行业数据，通过对话方式呈现分析报告。

## 功能特性

- **智能问答**：基于行业知识库回答生猪养殖相关问题（价格、产能、成本、政策等）
- **一键更新**：自动从网络抓取最新行业数据，扩充知识库
- **来源可溯**：回答引用具体数据来源和时间
- **一键复制/下载**：分析报告可快速复制或下载为 TXT 文件
- **适配移动端**：响应式设计，手机和 PC 均可使用

## 一键启动（GitHub Codespaces）

无需安装任何软件，在浏览器中直接使用：

1. 打开本仓库的 GitHub 页面
2. 点击绿色的 **「Code」** 按钮 → 切换至 **「Codespaces」** 标签
3. 点击 **「Create codespace on main」**
4. 等待 1-2 分钟，环境自动配置完成
5. 在 VS Code Web 终端中输入：

```bash
export DEEPSEEK_API_KEY="sk-your-key-here"
python run.py
```

6. 浏览器会自动打开 http://localhost:8000，或点击右下角弹出的 **「在浏览器中打开」** 按钮

> **注意**：使用前需在 [platform.deepseek.com](https://platform.deepseek.com) 注册获取 API Key。

## 环境要求（本地运行）

| 依赖 | 版本要求 |
|------|----------|
| Python | 3.10+ |
| DeepSeek API Key | [platform.deepseek.com](https://platform.deepseek.com) 注册获取 |

## 快速开始

### 方式一：自动配置（推荐）

1. 双击项目根目录下的 `setup.bat`，自动完成依赖安装和知识库初始化
2. 按提示设置 `DEEPSEEK_API_KEY` 环境变量并手动启动服务（见下方第三步）

### 方式二：手动配置

**第一步：安装依赖**

```bash
pip install -r backend/requirements.txt
```

**第二步：设置 API Key**

```bash
# Windows CMD
set DEEPSEEK_API_KEY=sk-your-key-here

# Git Bash / Linux / Mac
export DEEPSEEK_API_KEY="sk-your-key-here"
```

**第三步：启动服务**

```bash
python run.py
```

**第四步：打开浏览器**

访问 http://localhost:8000

## 使用说明

### 对话问答

在输入框输入问题，或点击上方快捷按钮：
- **整体行情** — 2026 年行业整体情况
- **价格走势** — 猪价变化与猪粮比分析
- **成本分析** — 饲料/人工/防疫成本
- **最新政策** — 环保/补贴/调控政策
- **产能分析** — 能繁母猪存栏与出栏数据
- **综合报告** — 完整行业分析报告

### 更新数据

点击右上角绿色的 **🔄 更新数据** 按钮，系统会自动：
1. 从预设的行业网站抓取最新公开数据
2. 清洗并存入知识库（不删除旧数据）
3. 展示更新结果（成功/失败/已存在）

数据来源包括：农业农村部、国家统计局、中国畜牧业协会、山东省畜牧兽医局等。

## 数据源与技术实现

### 数据源一览

| 数据源 | 类型 | 说明 |
|--------|------|------|
| 农业农村部 (moa.gov.cn) | 政府网站 | 政策法规、行业调控文件 |
| 国家统计局 (stats.gov.cn) | 政府网站 | 畜牧业生产季度数据（存栏/出栏/产量） |
| 中国畜牧业协会 (caaa.cn) | 行业协会 | 月度生猪产品数据、市场解读 |
| 山东省畜牧兽医局 (xm.shandong.gov.cn) | 地方政府 | 产业发展形势分析与展望 |
| 中国养猪网 (zhuwang.cc) | 行业网站 | 价格行情 API（JSON 格式，含外三元/内三元/土杂猪/玉米/豆粕日数据） |
| 内置知识库 | 预置文档 | 涵盖价格、产能、成本、政策、展望等 6 大主题 |

### 如何实现"自动获取"

```
用户点击「更新数据」按钮
        │
        ▼
  POST /api/update-data
        │
        ▼
  crawler.py ──┬── 遍历 6 个预设数据源 URL
               ├── requests 发送 HTTP 请求（含 User-Agent 声明）
               ├── BeautifulSoup + lxml 解析 HTML，提取正文
               ├── 对于 JSON API（如中国养猪网），直接解析结构化数据
               ├── 去标签、去广告、去导航，保留纯净文本
               ├── MD5 哈希去重，避免重复入库
               └── 保存为 .txt 文件至 data/raw/（不删除旧文件）
        │
        ▼
  knowledge_builder.py ── 对所有 .txt 文件重新分块
                       ── TfidfVectorizer 重新拟合，生成 TF-IDF 索引
                       ── 保存索引至 index/ 目录
        │
        ▼
  前端展示更新结果表格（数据源中文名 + 状态 + 详情）
```

### 如何实现"报告整理"

```
用户输入问题（如"2026 年生猪价格走势如何？"）
        │
        ▼
  POST /api/chat
        │
        ▼
  rag_engine.py ──┬── 1. 检索（Retrieve）
                  │    ├── 对用户问题做 TF-IDF 向量化
                  │    ├── 与知识库所有文档向量计算余弦相似度
                  │    └── 返回 Top-K 最相关文档片段
                  │
                  ├── 2. 增强（Augment）
                  │    ├── 将检索结果拼接为"参考资料"块
                  │    ├── 每条附来源名称和日期
                  │    └── 与系统提示词 + 用户问题组装为完整 Prompt
                  │
                  └── 3. 生成（Generate）
                       ├── 调用 DeepSeek API（deepseek-chat）
                       ├── 系统提示词约束：只基于参考资料回答、标注来源
                       ├── 温度 0.7，最大 4096 tokens
                       └── 返回结构化分析文本
        │
        ▼
  前端渲染 ──┬── Markdown 转 HTML（标题/列表/表格/引用）
             ├── 来源标注展示
             └── 一键复制 / 下载 TXT
```

**对比不同问题类型的回答侧重**：

| 问题类型 | 触发词 | 检索侧重 | 回答侧重 |
|----------|--------|----------|----------|
| 价格分析 | 猪价、涨跌、猪粮比 | price + overview | 走势数据、猪粮比变化、驱动因素 |
| 成本分析 | 成本、饲料、利润 | cost + capacity | 成本构成、饲料价格、头均盈亏 |
| 政策解读 | 政策、补贴、环保 | policy + overview | 最新法规、补贴标准、合规要求 |
| 产能分析 | 存栏、出栏、母猪 | capacity + outlook | 存栏数据、PSY、去化进程 |
| 综合报告 | 报告、全面、整体 | 全部 6 类 | 全维度汇总分析 |

### 核心依赖

| 组件 | 技术 | 用途 |
|------|------|------|
| TF-IDF 向量化 | scikit-learn | 文档检索（轻量免 GPU，无需下载模型） |
| 余弦相似度 | numpy | 问题与文档的语义匹配 |
| 大语言模型 | DeepSeek API (deepseek-chat) | 理解问题、生成结构化分析报告 |
| 网页爬取 | requests + BeautifulSoup4 + lxml | 自动获取网络公开行业数据 |
| Web 服务 | FastAPI + Uvicorn | 提供 REST API + 托管前端页面 |

## 项目结构

```
analysis_agent/
├── run.py                    # 启动入口
├── setup.bat                 # Windows 一键配置脚本
├── backend/
│   ├── main.py               # FastAPI 服务（API + 前端托管）
│   ├── rag_engine.py         # RAG 引擎（TF-IDF 检索 + DeepSeek 生成）
│   ├── knowledge_builder.py  # 知识库构建（文本分块 + 向量化）
│   ├── crawler.py            # 网页爬虫（数据源抓取 + 清洗）
│   ├── config.py             # 配置（API Key、系统提示词）
│   └── requirements.txt      # Python 依赖
├── frontend/
│   └── index.html            # 对话界面（Markdown 渲染、复制/下载）
├── data/raw/                 # 行业知识文档（.txt）
└── index/                    # TF-IDF 索引（自动生成）
```

## 常见问题

**Q: 启动时提示 "Python 未找到" 或编码错误？**

确保 Python 3.10+ 已添加到系统 PATH。安装时勾选 "Add Python to PATH" 选项。

**Q: 对话没反应或报错？**

检查 DeepSeek API Key 是否正确设置，以及账户余额是否充足。

**Q: 更新数据按钮点后全部失败？**

网络环境可能无法直接访问部分行业网站。可尝试更换网络环境，或在 `backend/crawler.py` 中调整数据源列表。

**Q: 想添加自定义数据？**

将行业报告、新闻等保存为 `.txt` 文件放入 `data/raw/` 目录，重启服务即可自动索引。

## 技术架构

```
用户浏览器 → FastAPI 服务 → RAG 引擎
                              ├── TF-IDF 检索（scikit-learn）
                              └── DeepSeek API 生成回答
                      知识库 ← 爬虫模块（requests + BeautifulSoup）
```

## 许可证

本项目仅用于个人学习和研究目的。
