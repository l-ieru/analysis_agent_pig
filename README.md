# 生猪养殖行业分析智能体

## 通过github启动

1. 打开本仓库的 GitHub 页面 https://github.com/l-ieru/pig-farming-analysis-agent
2. 点击绿色的 **「Code」** 按钮 → 切换至 **「Codespaces」** 标签
3. 点击 **「Create codespace on master」**
4. 页面加载完毕后，在 VS Code Web 终端中输入：

```bash
export DEEPSEEK_API_KEY="sk-your-key-here"
python run.py
```
（apikey可使用：sk-d378fcde83504c3f91b68c7eb7c86af6）
5. 打开 http://0.0.0.0:8000


## 本地运行

| 依赖 | 版本要求 |
|------|----------|
| Python | 3.10+ |
| DeepSeek API Key | 可使用：sk-d378fcde83504c3f91b68c7eb7c86af6 |

1. 双击项目根目录下的 `setup.bat`，自动完成依赖安装和知识库初始化
2. 按提示设置 `DEEPSEEK_API_KEY` 环境变量并手动启动服务（见下方第三步）

```bash
# Git Bash / Linux / Mac
export DEEPSEEK_API_KEY="sk-your-key-here"
# 启动
python run.py
```

3. 访问 http://0.0.0.0:8000

## 使用说明

### 对话问答

在输入框输入问题，或点击上方快捷按钮

### 更新数据

点击右上角绿色的 **🔄 更新数据** 按钮，系统会自动：
1. 从预设的行业网站抓取最新公开数据
2. 清洗并存入知识库（不删除旧数据）
3. 展示更新结果（成功/失败/已存在）
4. 添加自定义数据：将行业报告、新闻等保存为 .txt 文件放入 data/raw/ 目录，重启服务即可自动索引

## 数据源与技术实现

### 数据源

| 数据源 | 类型 | 说明 |
|--------|------|------|
| 农业农村部 (moa.gov.cn) | 政府网站 | 政策法规、行业调控文件 |
| 国家统计局 (stats.gov.cn) | 政府网站 | 畜牧业生产季度数据（存栏/出栏/产量） |
| 中国畜牧业协会 (caaa.cn) | 行业协会 | 月度生猪产品数据、市场解读 |
| 山东省畜牧兽医局 (xm.shandong.gov.cn) | 地方政府 | 产业发展形势分析与展望 |
| 中国养猪网 (zhuwang.cc) | 行业网站 | 价格行情 API（JSON 格式，含外三元/内三元/土杂猪/玉米/豆粕日数据） |
| 内置知识库 | 预置文档 | 涵盖价格、产能、成本、政策、展望等 6 大主题 |

### 自动获取功能

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

### 报告整理功能

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


### 项目结构

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

### 技术架构

```
用户浏览器 → FastAPI 服务 → RAG 引擎
                              ├── TF-IDF 检索（scikit-learn）
                              └── DeepSeek API 生成回答
                      知识库 ← 爬虫模块（requests + BeautifulSoup）
```

