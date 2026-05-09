"""
Web crawler for pig farming industry data.
Fetches latest news/reports from preset URLs and saves to data/raw/.
"""
import os
import re
import json
import time
import hashlib
import datetime
import requests
from bs4 import BeautifulSoup

from backend.config import DATA_DIR

# Friendly User-Agent
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

# Data sources to crawl
SOURCES = [
    {
        "name": "zhujia_api",
        "display_name": "中国养猪网",
        "url": "http://zhujia.zhuwang.cc/index/api/chartData?areaId=-1",
        "parser": "json",
        "selector": None,
        "note": "每日生猪价格/玉米/豆粕 JSON API",
    },
    {
        "name": "moa_policy",
        "display_name": "农业农村部",
        "url": "https://www.moa.gov.cn/gk/zcfg/",
        "parser": "html",
        "selector": "article, .content, .TRS_Editor, .Custom_UnionStyle",
        "note": "政策法规",
    },
    {
        "name": "shandong_market",
        "display_name": "山东省畜牧兽医局",
        "url": "http://xm.shandong.gov.cn/art/2026/3/17/art_24614_10351307.html",
        "parser": "html",
        "selector": "article, .content, .article, .TRS_Editor",
        "note": "山东省2025年生猪产业发展形势及2026年展望",
    },
    {
        "name": "caaa_data",
        "display_name": "中国畜牧业协会",
        "url": "https://pig.caaa.cn/html/pig_rd/pig_hydt/2026/0427/2467.html",
        "parser": "html",
        "selector": "article, .content, .text, .TRS_Editor",
        "note": "2026年3月全国生猪产品数据",
    },
    {
        "name": "stats_q1",
        "display_name": "国家统计局",
        "url": "https://gdzd.stats.gov.cn/dcsj/nysc/cmysc/202604/t20260420_182700.html",
        "parser": "html",
        "selector": "article, .content, .TRS_Editor, .xw-txt",
        "note": "2026年Q1畜牧业生产数据",
    },
    {
        "name": "zhuwang_article",
        "display_name": "中国养猪网",
        "url": "https://news.zhuwang.com.cn/xingyedianping/20260508/640151.html",
        "parser": "html",
        "selector": "article, .content, .article-content, .news-body",
        "note": "行业点评文章",
    },
]


def _clean_text(html: str) -> str:
    """Extract clean text from HTML, removing scripts/styles/nav/ads."""
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "nav", "footer", "header", "aside",
                      "noscript", "iframe", "form", "input", "button"]):
        tag.decompose()

    # Remove common ad/nav class patterns
    for cls in ["ad", "ads", "sidebar", "nav", "menu", "footer", "header",
                 "comment", "recommend", "hot", "related", "banner"]:
        for tag in soup.select(f"[class*={cls}]"):
            tag.decompose()

    text = soup.get_text(separator="\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def _extract_main_content(html: str, selector: str) -> str:
    """Try to extract the main content area using CSS selector, fall back to full page."""
    soup = BeautifulSoup(html, "lxml")

    # Try the provided selector
    if selector:
        content_el = soup.select_one(selector)
        if content_el:
            return _clean_text(str(content_el))

    # Fallback: try common article containers
    for sel in ["article", "main", ".content", ".article-content", ".post-content",
                 ".entry-content", ".news-content", ".text", "#content"]:
        el = soup.select_one(sel)
        if el and len(el.get_text(strip=True)) > 200:
            return _clean_text(str(el))

    # Last resort: extract body text (remove obvious nav boilerplate)
    body = soup.find("body")
    if body:
        return _clean_text(str(body))
    return ""


def _content_hash(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()[:12]


def _already_crawled(content_hash: str) -> bool:
    """Check if we've already saved this content before."""
    if not os.path.exists(DATA_DIR):
        return False
    for fname in os.listdir(DATA_DIR):
        if content_hash in fname:
            return True
    return False


def _format_json_data(source_name: str, data: dict) -> str:
    """Format JSON API data into readable text."""
    if source_name == "zhujia_api":
        return _format_zhujia_data(data)
    # Generic fallback
    return json.dumps(data, ensure_ascii=False, indent=2)


def _format_zhujia_data(data: dict) -> str:
    """Format zhujia.zhuwang.cc pig price API data."""
    lines = []
    lines.append("# 生猪市场每日价格数据\n")

    # Extract date range
    if "data" in data and len(data["data"]) > 0:
        dates = [d.get("date", "") for d in data["data"] if d.get("date")]
        if dates:
            lines.append(f"数据时间范围: {dates[-1]} ~ {dates[0]}")
            lines.append("")

    lines.append("## 最新价格数据\n")
    lines.append("| 日期 | 外三元(元/kg) | 内三元(元/kg) | 土杂猪(元/kg) | 玉米(元/吨) | 豆粕(元/吨) |")
    lines.append("|------|---------------|---------------|---------------|-------------|-------------|")

    rows = data.get("data", [])[:10] if isinstance(data, dict) else []
    if isinstance(data, list):
        rows = data[:10]

    for item in rows:
        date = item.get("date", "") or item.get("date_str", "")
        pig = item.get("pigprice", "") or item.get("pig", "")
        pig_in = item.get("pig_in", "") or item.get("pigIn", "")
        pig_local = item.get("pig_local", "") or item.get("pigLocal", "")
        maize = item.get("maizeprice", "") or item.get("maize", "")
        bean = item.get("bean", "") or item.get("soybean", "")
        lines.append(f"| {date} | {pig} | {pig_in} | {pig_local} | {maize} | {bean} |")

    lines.append("")
    lines.append("数据来源: 中国养猪网 (zhujia.zhuwang.cc)")
    lines.append("外三元: 国外进口的三个品种杂交的生猪")
    lines.append("内三元: 国内三个品种杂交的生猪")
    lines.append("土杂猪: 本地品种杂交的生猪")

    # Also include raw data summary for LLM
    lines.append("\n## 原始数据记录\n")
    for item in rows[:30]:
        lines.append("- " + ", ".join(f"{k}: {v}" for k, v in item.items()))

    return "\n".join(lines)


def crawl_all() -> dict:
    """Crawl all configured sources and save new articles to data/raw/."""
    os.makedirs(DATA_DIR, exist_ok=True)

    results = {
        "total_sources": len(SOURCES),
        "success": 0,
        "failed": 0,
        "articles_saved": 0,
        "details": [],
    }

    session = requests.Session()
    session.headers.update(HEADERS)

    for source in SOURCES:
        detail = {
            "name": source["name"],
            "display_name": source.get("display_name", source["name"]),
            "url": source["url"],
            "status": "pending",
            "articles": 0,
            "error": None,
        }
        print(f"Crawling: {source['name']} ({source['url']})")

        try:
            resp = session.get(source["url"], timeout=15, allow_redirects=True)
            resp.encoding = resp.apparent_encoding or "utf-8"

            if resp.status_code != 200:
                detail["status"] = "failed"
                detail["error"] = f"HTTP {resp.status_code}"
                results["failed"] += 1
                results["details"].append(detail)
                print(f"  Failed: HTTP {resp.status_code}")
                continue

            # Handle JSON API sources
            if source["parser"] == "json":
                try:
                    data = resp.json()
                    text = _format_json_data(source["name"], data)
                except Exception as e:
                    detail["status"] = "failed"
                    detail["error"] = f"JSON parse error: {str(e)[:100]}"
                    results["failed"] += 1
                    results["details"].append(detail)
                    print(f"  Failed: JSON parse error")
                    continue
                title = source.get("note", source["name"])

                if len(text) < 100:
                    detail["status"] = "failed"
                    detail["error"] = "API returned insufficient data"
                    results["failed"] += 1
                    results["details"].append(detail)
                    print(f"  Failed: insufficient data ({len(text)} chars)")
                    continue
            else:
                text = _extract_main_content(resp.text, source["selector"])

                if len(text) < 100:
                    detail["status"] = "failed"
                    detail["error"] = "Content too short (possible anti-bot page)"
                    results["failed"] += 1
                    results["details"].append(detail)
                    print(f"  Failed: content too short ({len(text)} chars)")
                    continue

                # Try to extract a meaningful title from the page
                soup = BeautifulSoup(resp.text, "lxml")
                title = ""
                for tag in ["h1", "h2", "title"]:
                    t = soup.find(tag)
                    if t:
                        title = t.get_text(strip=True)[:80]
                        break
                if not title:
                    title = source.get("note", source["name"])

            # Check for duplicate content
            h = _content_hash(text)
            if _already_crawled(h):
                detail["status"] = "skipped"
                detail["error"] = "Content already in knowledge base"
                results["details"].append(detail)
                print(f"  Skipped: already crawled")
                continue

            # Build the document with metadata header
            date_str = datetime.date.today().strftime("%Y-%m-%d")
            doc = f"# {title or source['name'] + ' 行业资讯'}\n\n"
            doc += f"来源: {source['url']}\n"
            doc += f"抓取日期: {date_str}\n\n"
            doc += text[:3000]

            # Save to file
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"{source['name']}_{timestamp}_{h}.txt"
            filepath = os.path.join(DATA_DIR, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(doc)

            detail["status"] = "success"
            detail["articles"] = 1
            results["success"] += 1
            results["articles_saved"] += 1
            results["details"].append(detail)
            print(f"  Saved: {filename} ({len(text)} chars)")

        except requests.Timeout:
            detail["status"] = "failed"
            detail["error"] = "Request timeout"
            results["failed"] += 1
            results["details"].append(detail)
            print(f"  Failed: timeout")
        except requests.ConnectionError:
            detail["status"] = "failed"
            detail["error"] = "Connection failed"
            results["failed"] += 1
            results["details"].append(detail)
            print(f"  Failed: connection error")
        except Exception as e:
            detail["status"] = "failed"
            detail["error"] = str(e)[:200]
            results["failed"] += 1
            results["details"].append(detail)
            print(f"  Failed: {e}")

        time.sleep(2)

    return results


if __name__ == "__main__":
    import json
    results = crawl_all()
    print("\n" + "=" * 50)
    print(json.dumps(results, ensure_ascii=False, indent=2))
