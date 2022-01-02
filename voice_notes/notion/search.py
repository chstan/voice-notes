"""Tools for searching for pages."""
import datetime
from dataclasses import dataclass, field
from typing import Any, Optional

__all__ = [
    "Page",
    "match_page",
    "get_page_matching_exact_title",
    "get_monthly_page_id",
    "get_daily_page_id",
    "get_monthly_page_id",
    "get_by_month_index_id",
]


@dataclass
class Page:
    """Representation of a Notion page."""

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
        """Get the plain text title by looking into the properties rich text objects."""
        return self.properties["title"]["title"][0]["plain_text"]


def get_page_matching_exact_title(notion, title: str) -> Optional[str]:
    """Find a unique page whose plain text title exactly matches `title`."""
    pages = notion.search(query=title)["results"]
    pages = [Page(**p) for p in pages]
    pages = [p for p in pages if p.plain_text_title == title]

    assert len(pages) < 2
    return pages[0].id if pages else None


def get_by_month_index_id(notion) -> str:
    """Fetch the ID of the top level journal index."""
    personal_journal_page = notion.search(query=f"Personal Journals by Month")[
        "results"
    ]
    personal_journal_page = [Page(**p) for p in personal_journal_page]
    assert len(personal_journal_page) == 1
    personal_journal_page = personal_journal_page[0]
    return personal_journal_page.id


def get_monthly_page_id(notion, query_date: datetime.datetime) -> Optional[str]:
    """Fetch the ID of a monthly journal page index for `query_date`."""
    monthly_slug = f"{query_date.year}/{query_date.month}"
    reject_daily_slug = f"{query_date.year}/{query_date.month}/"
    page_search = notion.search(query=f"Personal Journal {monthly_slug}")["results"]
    results = [Page(**p) for p in page_search]
    results = [
        r
        for r in results
        if reject_daily_slug not in r.plain_text_title
        and monthly_slug in r.plain_text_title
    ]

    assert len(results) < 2
    return results[0].id if results else None


def get_daily_page_id(notion, query_date: datetime.datetime) -> Optional[str]:
    """Fetch the ID of a daily journal page for `query_date`."""
    daily_slug = (
        f"Personal Journal {query_date.year}/{query_date.month}/{query_date.day}"
    )
    return get_page_matching_exact_title(notion, daily_slug)
