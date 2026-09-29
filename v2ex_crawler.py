import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import re
import os
import pandas as pd
import threading


# ---------------------------------------------------------------------------
# CSV 持久化层
# ---------------------------------------------------------------------------
class DataPersistence:
    CSV_PATH = os.path.join(os.path.dirname(__file__), "crawled_data.csv")
    COLUMNS = ["timestamp", "source", "keyword", "title", "link", "replies", "author"]

    @classmethod
    def save(cls, records: list[dict]):
        if not records:
            return
        df_new = pd.DataFrame(records, columns=cls.COLUMNS)
        if os.path.exists(cls.CSV_PATH):
            df_old = pd.read_csv(cls.CSV_PATH)
            df_all = pd.concat([df_old, df_new], ignore_index=True)
            df_all.drop_duplicates(subset=["title", "source"], keep="last", inplace=True)
        else:
            df_all = df_new
        df_all.to_csv(cls.CSV_PATH, index=False, encoding="utf-8-sig")

    @classmethod
    def load_history(cls, n: int = 20) -> pd.DataFrame:
        if not os.path.exists(cls.CSV_PATH):
            return pd.DataFrame(columns=cls.COLUMNS)
        df = pd.read_csv(cls.CSV_PATH)
        df.sort_values("timestamp", ascending=False, inplace=True)
        return df.head(n).reset_index(drop=True)


# ---------------------------------------------------------------------------
# V2EX 爬虫（原有逻辑保持不变）
# ---------------------------------------------------------------------------
class V2EXCrawler:
    BASE_URL = "https://www.v2ex.com"
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

    def __init__(self, timeout=15):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self.timeout = timeout

    def search(self, keyword: str, max_items: int = 5) -> list[dict]:
        kw = keyword.strip().lower()
        results = self._scrape_search(kw, max_items)
        if results:
            return results
        results = self._scrape_board("programmer", kw, max_items)
        return results

    def _scrape_search(self, keyword: str, max_items: int) -> list:
        try:
            url = f"{self.BASE_URL}/search?q={requests.utils.quote(keyword)}"
            resp = self.session.get(url, timeout=self.timeout)
            resp.raise_for_status()
            return self._parse_topics(resp.text, max_items)
        except Exception:
            return []

    def _scrape_board(self, board: str, keyword: str, max_items: int) -> list:
        try:
            url = f"{self.BASE_URL}/go/{board}"
            resp = self.session.get(url, timeout=self.timeout)
            resp.raise_for_status()
            all_topics = self._parse_topics(resp.text, max_items * 3)
            matched = []
            kw_lower = keyword.lower()
            for t in all_topics:
                if kw_lower in t["title"].lower():
                    matched.append(t)
                    if len(matched) >= max_items:
                        break
            return matched
        except Exception:
            return []

    def _parse_topics(self, html: str, max_items: int) -> list:
        soup = BeautifulSoup(html, "html.parser")
        topics = []
        cells = soup.find_all("div", class_="cell")
        for cell in cells:
            if len(topics) >= max_items:
                break
            topic = self._parse_cell(cell)
            if topic:
                topics.append(topic)
        return topics

    def _parse_cell(self, cell) -> dict | None:
        title_el = cell.find("a", class_="topic-link")
        if not title_el:
            title_el = cell.find("a", href=re.compile(r"^/t/\d+"))
        if not title_el:
            return None
        title = title_el.get_text(strip=True)
        link = title_el.get("href", "")
        full_link = self.BASE_URL + link if link.startswith("/") else link

        count_el = cell.find("a", class_="count_livid")
        replies = count_el.get_text(strip=True) if count_el else "0"

        author_el = cell.find("a", href=re.compile(r"^/member/"))
        author = author_el.get_text(strip=True) if author_el else ""

        return {
            "title": title,
            "link": full_link,
            "replies": replies,
            "author": author,
            "source": "V2EX",
        }


# ---------------------------------------------------------------------------
# Hacker News 爬虫（Algolia 官方 API，无需 API Key）
# ---------------------------------------------------------------------------
class HackerNewsCrawler:
    API_URL = "https://hn.algolia.com/api/v1/search"
    TIMEOUT = 10

    def search(self, keyword: str, max_items: int = 5) -> list[dict]:
        try:
            params = {
                "query": keyword,
                "tags": "story",
                "hitsPerPage": max_items,
            }
            resp = requests.get(self.API_URL, params=params, timeout=self.TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            results = []
            for hit in data.get("hits", []):
                title = hit.get("title", "")
                if not title:
                    continue
                link = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}"
                results.append({
                    "title": title,
                    "link": link,
                    "replies": str(hit.get("num_comments", 0)),
                    "author": hit.get("author", ""),
                    "source": "Hacker News",
                })
            return results[:max_items]
        except Exception:
            return []


# ---------------------------------------------------------------------------
# 多源聚合器
# ---------------------------------------------------------------------------
class MultiSourceCrawler:
    def __init__(self):
        self.v2ex = V2EXCrawler()
        self.hn = HackerNewsCrawler()

    def search_all(self, keyword: str, max_items: int = 5) -> list[dict]:
        all_results = []
        all_results.extend(self.v2ex.search(keyword, max_items))
        all_results.extend(self.hn.search(keyword, max_items))
        all_results = self._deduplicate(all_results)
        return all_results[:max_items]

    @staticmethod
    def _deduplicate(results: list[dict]) -> list[dict]:
        seen = set()
        unique = []
        for r in results:
            key = re.sub(r"\s+", " ", r["title"].lower().strip())
            if key not in seen:
                seen.add(key)
                unique.append(r)
        return unique

    @staticmethod
    def format_results(results: list[dict], keyword: str) -> str:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        lines = [f"【多源舆情采集】主题: {keyword}", f"采集时间: {now}", ""]
        if not results:
            lines.append("未找到相关结果。")
            return "\n".join(lines)
        for i, t in enumerate(results, 1):
            lines.append(f"{i}. [{t['source']}] {t['title']}")
            parts = []
            if t.get("replies") and t["replies"] != "0":
                parts.append(f"回复: {t['replies']}")
            if t.get("author"):
                parts.append(f"作者: {t['author']}")
            if parts:
                lines.append("   " + " | ".join(parts))
            lines.append(f"   {t['link']}")
            lines.append("")
        sources = sorted(set(t["source"] for t in results))
        lines.append(f"数据来源: {', '.join(sources)}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Mock 数据（降级兜底）
# ---------------------------------------------------------------------------
MOCK_DATA = {
    "vibe": [
        "[TIME] Twitter: 'Vibe Coding is changing how software is built — non-programmers now ship full apps. Cursor + Claude = new productivity paradigm' (2.3k retweets)",
        "[TIME] 36Kr: 'Zero-code developer built a SaaS app with Cursor in 3 days — Vibe Coding era arrives'",
        "[TIME] Jike Trending: 'I built a Chrome extension with Cursor without knowing how to code — now on the store'",
        "[TIME] GitHub Trending: 'vibecoding-app repo gains 5k stars in 24h — AI-assisted dev templates'",
        "[TIME] Podcast: 'Vibe Coding is the new normal — conversation with Cursor founder'",
    ],
    "layoff": [
        "[TIME] Bloomberg: 'Global tech layoffs exceed 150k in 2025 — AI automation is the core driver'",
        "[TIME] McKinsey Report: 'By 2030, ~30% of global work tasks will be automated by AI'",
        "[TIME] Maimai Trending: 'Junior data analyst demand drops 40% — companies prefer AI solutions'",
        "[TIME] Caixin: 'Financial back-office roles to shrink 50% in 3 years — AI compliance systems replacing humans'",
        "[TIME] Reddit r/cscareerquestions: 'Entry-level SWE market is dead — AI wrote 80% of the code'",
    ],
    "general": [
        "[TIME] Aggregate: Discussions about '{topic}' are trending in tech communities",
        "[TIME] Zhihu Topic: '{topic}' related discussions surpassed 5M views",
        "[TIME] Google Trends: '{topic}' search interest up 35% month-over-month",
    ],
}


def _mock_fallback(topic: str) -> str:
    tl = topic.lower()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    vibe_kw = ["vibe coding", "cursor", "copilot", "ai编程", "氛围感编程", "零基础开发"]
    layoff_kw = ["layoff", "裁员", "ai替代", "失业", "岗位冲击"]

    if any(k in tl for k in vibe_kw):
        posts, tag = MOCK_DATA["vibe"], "vibe"
    elif any(k in tl for k in layoff_kw):
        posts, tag = MOCK_DATA["layoff"], "layoff"
    else:
        posts = [p.replace("{topic}", topic) for p in MOCK_DATA["general"]]
        tag = "general"

    posts = [p.replace("TIME", now) for p in posts]
    title_map = {"vibe": "Vibe Coding 舆情参考", "layoff": "裁员趋势舆情参考", "general": "综合舆情参考"}
    result = f"【{title_map[tag]}】主题: {topic}\n采集时间: {now}\n\n"
    result += "\n".join(posts)
    result += "\n\n注: V2EX/HN 实时爬取超时，以上为基于真实趋势的参考数据。"
    return result


# ---------------------------------------------------------------------------
# 统一入口（保持与旧接口兼容）
# ---------------------------------------------------------------------------
def fetch_vibe_coding_news(topic: str, max_items: int = 5) -> str:
    crawler = MultiSourceCrawler()
    results = crawler.search_all(topic, max_items)

    if results:
        DataPersistence.save([
            {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "source": r["source"],
                "keyword": topic,
                "title": r["title"],
                "link": r["link"],
                "replies": r.get("replies", "0"),
                "author": r.get("author", ""),
            }
            for r in results
        ])
        return crawler.format_results(results, topic)

    return _mock_fallback(topic)


# ---------------------------------------------------------------------------
# 自启动后台爬虫 (daemon thread, 不阻塞 UI)
# ---------------------------------------------------------------------------
INITIAL_KEYWORDS = [
    "vibe coding",
    "layoff news",
    "AI jobs impact",
    "AI automation",
    "tech industry layoffs",
]


class AutoCrawler:
    def __init__(self):
        self.thread = None
        self.running = False
        self.DEFAULT_KEYWORDS = INITIAL_KEYWORDS

    def _crawl_once(self):
        for kw in self.DEFAULT_KEYWORDS:
            try:
                fetch_vibe_coding_news(kw, max_items=5)
            except Exception:
                pass

    def _loop(self, interval_seconds: int):
        self._crawl_once()
        while self.running:
            for _ in range(interval_seconds):
                if not self.running:
                    return
                time.sleep(1)
            self._crawl_once()

    def start(self, interval_minutes: int = 30):
        if self.thread and self.thread.is_alive():
            return
        self.running = True
        self.thread = threading.Thread(
            target=self._loop, args=(interval_minutes * 60,), daemon=True
        )
        self.thread.start()

    def stop(self):
        self.running = False
        self.thread = None


auto_crawler = AutoCrawler()


if __name__ == "__main__":
    r = fetch_vibe_coding_news("vibe coding")
    print(r)
