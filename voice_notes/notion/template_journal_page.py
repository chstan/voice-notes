"""Utilities for templating new journal pages."""

import datetime

from .search import (
    Page,
    get_by_month_index_id,
    get_daily_page_id,
    get_monthly_page_id,
)
from .basics import parent_ref, simple_title_properties, Block

__all__ = ["new_monthly_page", "new_daily_page", "get_or_create_daily_page_id"]


def new_monthly_page(for_date: datetime.datetime):
    """Generate properties and block content for a monthyl journal page index."""
    title_for_page = f"Personal Journal {for_date.year}/{for_date.month}"
    properties = {"title": simple_title_properties(title_for_page)}
    children = []
    return properties, children


def new_daily_page(for_date: datetime.datetime):
    """Generate properties and block content for a daily journal page."""
    title_for_page = f"Personal Journal {for_date.year}/{for_date.month}/{for_date.day}"
    properties = {"title": simple_title_properties(title_for_page)}
    children = [
        Block.h1("Agenda"),
        Block.todo("Plan your day"),
        Block.h1("General notes"),
        Block.h1("Voice notes"),
    ]

    return properties, children


def get_or_create_daily_page_id(notion, query_date: datetime.datetime) -> str:
    """Fetch or create the ID of a daily journal page corresponding to `query_date`."""
    journal_page_id = get_by_month_index_id(notion)
    monthly_page_id = get_monthly_page_id(notion, query_date)

    # Check if we need to make a monthly level organization page
    if not monthly_page_id:
        properties, children = new_monthly_page(query_date)
        created_page = notion.pages.create(
            parent=parent_ref(journal_page_id),
            properties=properties,
            children=children,
        )
        monthly_page_id = Page(**created_page).id

    # Check if we need to make a daily level organization page
    daily_page_id = get_daily_page_id(notion, query_date)

    if not daily_page_id:
        properties, children = new_daily_page(query_date)
        created_page = notion.pages.create(
            parent=parent_ref(monthly_page_id),
            properties=properties,
            children=children,
        )
        daily_page_id = Page(**created_page).id

    return daily_page_id
