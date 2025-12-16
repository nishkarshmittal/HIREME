from __future__ import annotations

import json
import random
import re
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests
import pandas as pd
from bs4 import BeautifulSoup


# -----------------------------
# Config
# -----------------------------
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

SESSION = requests.Session()
SESSION.headers.update(
    {
        "User-Agent": USER_AGENT,
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "application/json,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
)

random.seed(42)


# -----------------------------
# Data model
# -----------------------------
@dataclass
class JobPost:
    """
    Structured representation of a single job post.

    Attributes
    ----------
    source : str
        Data source name (e.g., RemoteOK, Remotive).
    title : str
        Job title.
    company : str
        Company name.
    location : str
        Location string (may be "Remote").
    date_posted_raw : str
        Raw date field from the source.
    salary_raw : str
        Raw salary field from the source.
    url : str
        Job posting URL.
    description : str
        Job description text (cleaned).
    scraped_at_utc : str
        ISO timestamp for when this record was scraped.
    """
    source: str
    title: str
    company: str
    location: str
    date_posted_raw: str
    salary_raw: str
    url: str
    description: str
    scraped_at_utc: str


# -----------------------------
# Helpers
# -----------------------------
def now_utc_iso() -> str:
    """
    Get current UTC timestamp in ISO 8601 format.

    Returns
    -------
    str
        ISO timestamp.
    """
    return datetime.now(timezone.utc).isoformat()


def clean_text(s: str) -> str:
    """
    Normalize whitespace and strip leading/trailing spaces.

    Parameters
    ----------
    s : str
        Input text.

    Returns
    -------
    str
        Cleaned text.
    """
    return re.sub(r"\s+", " ", (s or "")).strip()


def polite_get(url: str, timeout: int = 30, retries: int = 3, backoff_s: float = 1.2) -> str:
    """
    Fetch a URL with retries and small backoff.

    Parameters
    ----------
    url : str
        URL to fetch.
    timeout : int
        Timeout in seconds.
    retries : int
        Number of attempts.
    backoff_s : float
        Base backoff in seconds.

    Returns
    -------
    str
        Response text.

    Raises
    ------
    RuntimeError
        If all retries fail.
    """
    last_err: Optional[Exception] = None
    for attempt in range(1, retries + 1):
        try:
            time.sleep(backoff_s * (attempt - 1) + random.random() * 0.4)
            resp = SESSION.get(url, timeout=timeout)
            if resp.status_code == 200 and resp.text:
                return resp.text
            last_err = RuntimeError(f"HTTP {resp.status_code} for {url}")
        except Exception as e:
            last_err = e
    raise RuntimeError(f"Failed to fetch {url}. Last error: {last_err}")


def posts_to_dicts(posts: List[JobPost]) -> List[Dict[str, Any]]:
    """
    Convert a list of JobPost objects to a list of dictionaries.

    Parameters
    ----------
    posts : list[JobPost]
        Job posts.

    Returns
    -------
    list[dict]
        List of dictionaries suitable for DataFrame creation.
    """
    return [asdict(p) for p in posts]


# -----------------------------
# Scrapers
# -----------------------------
def scrape_remoteok(limit: int = 200) -> List[JobPost]:
    """
    Fetch remote job postings from the RemoteOK public API.

    Parameters
    ----------
    limit : int
        Maximum number of job postings to return.

    Returns
    -------
    list[JobPost]
        Scraped job posts.
    """
    url = "https://remoteok.com/api"
    text = polite_get(url)
    data = json.loads(text)

    posts: List[JobPost] = []
    for item in data[1:]:
        if not isinstance(item, dict):
            continue

        title = clean_text(str(item.get("position") or item.get("title") or ""))
        company = clean_text(str(item.get("company") or ""))
        location = clean_text(str(item.get("location") or ""))
        date_posted_raw = clean_text(str(item.get("date") or item.get("epoch") or ""))
        salary_raw = clean_text(str(item.get("salary") or ""))

        job_url = item.get("url") or ""
        if job_url and job_url.startswith("/"):
            job_url = "https://remoteok.com" + job_url
        job_url = clean_text(str(job_url))

        desc = item.get("description") or ""
        desc = BeautifulSoup(desc, "html.parser").get_text(" ")
        desc = clean_text(desc)

        if not title or not company or not job_url:
            continue

        posts.append(
            JobPost(
                source="RemoteOK",
                title=title,
                company=company,
                location=location,
                date_posted_raw=date_posted_raw,
                salary_raw=salary_raw,
                url=job_url,
                description=desc,
                scraped_at_utc=now_utc_iso(),
            )
        )
        if len(posts) >= limit:
            break

    return posts


def scrape_remotive(limit: int = 200, category: Optional[str] = None, search: Optional[str] = None) -> List[JobPost]:
    """
    Fetch remote job postings from the Remotive public API.

    Parameters
    ----------
    limit : int
        Maximum number of job postings to return.
    category : str | None
        Optional Remotive category (example: "software-dev").
    search : str | None
        Optional search query (example: "data", "machine learning").

    Returns
    -------
    list[JobPost]
        Scraped job posts.
    """
    base = "https://remotive.com/api/remote-jobs"
    params: Dict[str, str] = {}
    if category:
        params["category"] = category
    if search:
        params["search"] = search

    resp = SESSION.get(base, params=params, timeout=30)
    if resp.status_code != 200:
        return []

    payload = resp.json()
    jobs = payload.get("jobs", []) if isinstance(payload, dict) else []
    posts: List[JobPost] = []

    for j in jobs:
        title = clean_text(str(j.get("title", "")))
        company = clean_text(str(j.get("company_name", "")))
        location = clean_text(str(j.get("candidate_required_location", ""))) or "Remote"
        date_posted_raw = clean_text(str(j.get("publication_date", "")))
        salary_raw = clean_text(str(j.get("salary", "")))
        job_url = clean_text(str(j.get("url", "")))

        desc = j.get("description", "") or ""
        desc = BeautifulSoup(desc, "html.parser").get_text(" ")
        desc = clean_text(desc)

        if not title or not company or not job_url:
            continue

        posts.append(
            JobPost(
                source="Remotive",
                title=title,
                company=company,
                location=location,
                date_posted_raw=date_posted_raw,
                salary_raw=salary_raw,
                url=job_url,
                description=desc,
                scraped_at_utc=now_utc_iso(),
            )
        )
        if len(posts) >= limit:
            break

    return posts


# -----------------------------
# Feature extraction and cleaning
# -----------------------------
SKILLS = [
    "python", "sql", "java", "javascript", "typescript", "c++", "r",
    "machine learning", "deep learning", "nlp", "computer vision",
    "pytorch", "tensorflow", "keras", "scikit-learn", "pandas", "numpy",
    "aws", "gcp", "azure", "docker", "kubernetes",
    "react", "node", "flask", "django", "fastapi",
    "postgresql", "mysql", "mongodb", "git",
]

ROLE_KEYWORDS = {
    "Data Scientist": ["data scientist", "data science"],
    "ML Engineer": ["machine learning engineer", "ml engineer", "applied scientist"],
    "Data Analyst": ["data analyst", "analytics"],
    "Software Engineer": ["software engineer", "backend engineer", "frontend engineer", "full stack", "full-stack"],
    "Data Engineer": ["data engineer", "analytics engineer"],
    "DevOps": ["devops", "site reliability", "sre", "platform engineer"],
}

REGION_KEYWORDS = {
    "West Coast": ["ca", "california", "wa", "washington", "or", "oregon"],
    "East Coast": ["ny", "new york", "nj", "new jersey", "ma", "massachusetts", "dc", "virginia", "md", "maryland", "pa", "pennsylvania"],
    "Central": ["tx", "texas", "il", "illinois", "co", "colorado", "ga", "georgia"],
}


def extract_skills(text: str, skill_list: List[str] = SKILLS) -> List[str]:
    """
    Extract skills by keyword matching from text.

    Parameters
    ----------
    text : str
        Text to scan (title + description).
    skill_list : list[str]
        Canonical skill list to match.

    Returns
    -------
    list[str]
        Skills found in the text.
    """
    t = (text or "").lower()
    found: List[str] = []
    for sk in skill_list:
        if len(sk) <= 3 or sk in {"r"}:
            if re.search(rf"\b{re.escape(sk)}\b", t):
                found.append(sk)
        else:
            if sk in t:
                found.append(sk)

    seen = set()
    out: List[str] = []
    for x in found:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def categorize_role(title: str) -> str:
    """
    Categorize a job title into a high-level role bucket.

    Parameters
    ----------
    title : str
        Job title.

    Returns
    -------
    str
        Role category label.
    """
    t = (title or "").lower()
    for role, keys in ROLE_KEYWORDS.items():
        if any(k in t for k in keys):
            return role
    return "Other"


def classify_region(location: str) -> str:
    """
    Classify a location string into region buckets using simple heuristics.

    Parameters
    ----------
    location : str
        Location text.

    Returns
    -------
    str
        Region bucket.
    """
    text = (location or "").lower()
    for region, keys in REGION_KEYWORDS.items():
        if any(k in text for k in keys):
            return region
    if "remote" in text:
        return "Remote/Unspecified"
    return "Other/Unspecified"


def parse_salary_to_yearly_usd(s: str) -> Tuple[Optional[float], Optional[float], str]:
    """
    Parse a salary string and attempt to convert it to yearly USD range.

    Parameters
    ----------
    s : str
        Salary string.

    Returns
    -------
    (float | None, float | None, str)
        min_yearly_usd, max_yearly_usd, unit_guess.
    """
    s0 = clean_text(s or "")
    if not s0:
        return None, None, "unknown"

    txt = s0.lower().replace(",", "")
    unit = "year"
    if "/hr" in txt or "per hour" in txt or "hour" in txt:
        unit = "hour"
    elif "/month" in txt or "per month" in txt:
        unit = "month"
    elif "/week" in txt or "per week" in txt:
        unit = "week"

    nums: List[float] = []
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*(k)?", txt):
        val = float(m.group(1))
        if m.group(2) == "k":
            val *= 1000.0
        nums.append(val)

    if not nums:
        return None, None, unit

    if len(nums) >= 2:
        lo, hi = float(min(nums[0], nums[1])), float(max(nums[0], nums[1]))
    else:
        lo, hi = float(nums[0]), float(nums[0])

    if unit == "hour":
        lo *= 2080.0
        hi *= 2080.0
    elif unit == "week":
        lo *= 52.0
        hi *= 52.0
    elif unit == "month":
        lo *= 12.0
        hi *= 12.0

    if lo < 15000 or hi > 700000:
        return None, None, unit

    return lo, hi, unit


def clean_posts(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean raw scraped posts into a structured dataset for analysis.

    Parameters
    ----------
    df : pandas.DataFrame
        Raw DataFrame from scraped JobPost dictionaries.

    Returns
    -------
    pandas.DataFrame
        Cleaned DataFrame with derived columns (role, region, skills, salary).
    """
    out = df.copy()

    out["title"] = out["title"].map(clean_text)
    out["company"] = out["company"].map(clean_text)
    out["location"] = out["location"].map(clean_text)
    out["description"] = out["description"].map(clean_text)
    out["source"] = out["source"].map(clean_text)
    out["url"] = out["url"].map(clean_text)

    out = out.drop_duplicates(subset=["url"]).reset_index(drop=True)

    out["role_category"] = out["title"].map(categorize_role)
    out["region"] = out["location"].map(classify_region)

    out["skills"] = (out["title"] + " " + out["description"]).map(extract_skills)
    out["num_skills"] = out["skills"].map(len)

    parsed = out["salary_raw"].map(parse_salary_to_yearly_usd)
    out["salary_min_usd_year"] = parsed.map(lambda t: t[0])
    out["salary_max_usd_year"] = parsed.map(lambda t: t[1])
    out["salary_unit_guess"] = parsed.map(lambda t: t[2])
    out["salary_mid_usd_year"] = out[["salary_min_usd_year", "salary_max_usd_year"]].mean(axis=1)

    return out


def collect_posts(remoteok_limit: int = 150, remotive_limit: int = 150) -> pd.DataFrame:
    """
    Collect posts from all configured sources and return a raw DataFrame.

    Parameters
    ----------
    remoteok_limit : int
        Max RemoteOK records.
    remotive_limit : int
        Max Remotive records.

    Returns
    -------
    pandas.DataFrame
        Raw combined dataset.
    """
    posts: List[JobPost] = []
    posts += scrape_remoteok(limit=remoteok_limit)
    posts += scrape_remotive(limit=remotive_limit, category="software-dev", search="data")
    return pd.DataFrame(posts_to_dicts(posts))