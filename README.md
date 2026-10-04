# AI-Impact-on-Jobs-and-Layoff-Risk-Data-Analysis-Project
VibeTrends AI — AIGC Job Impact & Vibe Coding Diagnostic Platform

1. Core Features
   Tab 1: Dynamic Visualization
       Natural language -> LLM generates Plotly code -> overwrites dynamic.py
       -> importlib hot-reload -> interactive chart rendered
       Includes 4 one-click preset analysis cards (Automation vs Risk,
       Creativity Safe Haven, AI Learning Curve, Tech Generation Divide)

    Tab 2: AI Career Advisor (Agent + Tool Use)
        Three routing modes:
          - Data calculation -> stats_analytics (real Pandas aggregation)
          - Live trends     -> data_fetcher (V2EX + Hacker News multi-source crawler)
          - General advisory -> Statistics + LLM insight generation
        Full st.status() Thought -> Action -> Observation chain display

    Tab 3: Data Explorer
        Multi-dimensional sidebar filters (Industry / Risk / Education / Size)
        + KPI metrics + Plotly overview chart
        + Crawl history display (from CSV persistence layer)

2. Requirements
   Python 3.11+
   pip install streamlit pandas plotly openai requests beautifulsoup4

3. Run
   python -m streamlit run app.py

4. API Key Setup
   The app includes a built-in DeepSeek API key — no manual setup required.
   Just run the app and it will work immediately.

   To use a different provider, expand "Override API Settings" in the sidebar:
   - DeepSeek (Built-in): https://api.deepseek.com  model: deepseek-chat (default)
   - SiliconFlow: https://api.siliconflow.cn/v1  model: MiniMaxAI/MiniMax-M2.5
   - Custom:      manual base_url and model

5. Multi-Source Crawler & Data Persistence
   When user asks "Vibe Coding trends" / "layoff news" in Tab 2,
   Agent calls v2ex_crawler.py to scrape real-time discussions from:
     - V2EX (Chinese tech community) - HTML parsing
     - Hacker News (English tech community) - Algolia REST API
   Results are merged, deduplicated, and saved to crawled_data.csv.
   Auto-crawler runs every 30 minutes on startup (configurable).
   Tab 3 displays crawl history from CSV persistence layer.

6. Project Files
   app.py             Main Streamlit app (UI + Agent + Tool functions)
   ai_api.py          LLM gateway (OpenAI-compatible streaming)
   data_query.py      Dynamic plot prompt management
   dynamic.py         AI-generated Plotly sandbox (hot-reloaded)
   v2ex_crawler.py    Multi-source crawler (V2EX + Hacker News) + CSV persistence
   crawled_data.csv   Auto-generated crawl data (deduplicated)
   ai-impact-jobs-layoff-risk-dataset.csv  16-column dataset (20000 rows)

7. Data Sources
   Static Data:
     - Kaggle: AI Impact on Jobs and Layoff Risk Dataset (20000 rows x 16 columns)
   Real-time Data:
     - V2EX: Chinese tech community discussions (HTML scraping)
     - Hacker News: English tech community discussions (Algolia API)
   Persistence:
     - crawled_data.csv: Auto-generated, deduplicated crawl results

VibeTrends AI —— AIGC 岗位影响评估与 Vibe Coding 诊断平台 
1. 核心功能 Tab 1：动态可视化
  自然语言输入 -> LLM 生成 Plotly 代码 -> 覆盖写入 dynamic.py -> 通过 importlib 热重载 -> 渲染交互式图表。
  内置 4 张一键生成的预设分析卡片：自动化与风险、创意安全区、AI 学习曲线、技术代际鸿沟。 Tab 2：AI 职业顾问（Agent + 工具调用）
  支持三种路由模式： 数据计算 -> stats_analytics（基于 Pandas 的真实数据聚合） 实时趋势 -> data_fetcher（V2EX + Hacker News 多源爬虫） 通用咨询 -> 统计数据 + LLM 洞察生成
  完整展示 st.status() 的思考 -> 行动 -> 观察 执行链路。   Tab 3：数据探索器
  多维度侧边栏筛选（行业 / 风险 / 学历 / 规模）+ KPI 指标 + Plotly 概览图表 + 爬取历史展示（读取 CSV 持久化层）。

2. 运行环境要求
  Python 3.11+
  pip install streamlit pandas plotly openai requests beautifulsoup4

3. 启动方式
  python -m streamlit run app.py

4. API Key 配置
  需手动配置。
  如需切换其他服务商，可在侧边栏展开“覆盖 API 设置”：
  DeepSeek：https://api.deepseek.com，模型：deepseek-chat（默认）
  SiliconFlow：https://api.siliconflow.cn/v1，模型：MiniMaxAI/MiniMax-M2.5
  自定义：手动输入 base_url 和模型名称

5. 多源爬虫与数据持久化
  当用户在 Tab 2 询问“Vibe Coding 趋势”或“裁员新闻”时，Agent 会调用 v2ex_crawler.py 抓取实时讨论： V2EX（中文技术社区）- HTML 解析 Hacker News（英文技术社区）- Algolia REST API
  抓取结果会自动合并、去重，并保存至 crawled_data.csv。
  应用启动时默认每 30 分钟自动爬取一次（可配置）。Tab 3 会从 CSV 持久化层读取并展示爬取历史。

6. 项目文件说明
   app.py：Streamlit 主应用（UI + Agent + 工具函数）
   ai_api.py：LLM 网关（兼容 OpenAI 的流式输出）
   data_query.py：动态图表 Prompt 管理 dynamic.py：AI 生成的 Plotly 代码沙箱（支持热重载）
   v2ex_crawler.py：多源爬虫（V2EX + Hacker News）+ CSV 持久化
   crawled_data.csv：自动生成的爬取数据（已去重）
   ai-impact-jobs-layoff-risk-dataset.csv：包含 16 个字段、20000 行数据的静态数据集

7. 数据来源
   静态数据：Kaggle 上的《AI 对就业的影响与裁员风险数据集》（20000 行 x 16 列）
   实时数据：V2EX（中文技术社区讨论，HTML 抓取）、Hacker News（英文技术社区讨论，Algolia API）
   数据持久化：crawled_data.csv（自动生成的去重爬取结果）
