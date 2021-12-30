import datetime
from dataclasses import dataclass, field
from typing import Any, Optional

__all__ = [
    "PageResult",
    "match_page", 
    "get_page_matching_exact_title",
    "get_monthly_page_id",
    "get_daily_page_id",
    "get_monthly_page_id",
    "get_by_month_index_id",
]

@dataclass
class PageResult:
    archived: bool = field(repr=False)
    id: str
    url: str = field(repr=False)

    created_time: str = field(repr=False)
    last_edited_time: str = field(repr=False)

    object: str = field(repr=False)

    properties: Any = field(repr=False)

    parent: Any = None
    cover: Any = field(default=None, repr=False)
    icon: Any = field(default=None, repr=False)

    @property
    def plain_text_title(self):
        return self.properties["title"]["title"][0]["plain_text"]

def get_page_matching_exact_title(notion, title: str) -> Optional[str]:
    pages = notion.search(query=title)["results"]
    pages = [PageResult(**p) for p in pages]
    pages = [p for p in pages if p.plain_text_title == title]

    assert len(pages) < 2
    return pages[0].id if pages else None

def get_by_month_index_id(notion) -> str:
    personal_journal_page = notion.search(query=f"Personal Journals by Month")["results"]
    personal_journal_page = [PageResult(**p) for p in personal_journal_page]
    assert len(personal_journal_page) == 1
    personal_journal_page = personal_journal_page[0]
    return personal_journal_page.id

def get_monthly_page_id(notion, query_date: datetime.datetime) -> Optional[str]: 
    monthly_slug = f"{query_date.year}/{query_date.month}"
    reject_daily_slug = f"{query_date.year}/{query_date.month}/"
    page_search = notion.search(query=f"Personal Journal {monthly_slug}")["results"]
    results = [PageResult(**p) for p in page_search]
    results = [r for r in results if reject_daily_slug not in r.plain_text_title and monthly_slug in r.plain_text_title]

    assert len(results) < 2
    return results[0].id if results else None

def get_daily_page_id(notion, query_date: datetime.datetime) -> Optional[str]: 
    daily_slug = f"{query_date.year}/{query_date.month}/{query_date.day}"
    page_search = notion.search(query=f"Personal Journal {daily_slug}")["results"]
    results = [PageResult(**p) for p in page_search]

    assert len(results) < 2
    return results[0].id if results else None
