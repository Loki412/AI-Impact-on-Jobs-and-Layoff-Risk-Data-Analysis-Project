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
