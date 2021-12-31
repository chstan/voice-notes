"""Utilities for generating JSON objects representing Notion blocks and rich text."""
from enum import Enum
from typing import Any, List

__all__ = [
    "BlockType",
    "Block",
    "RichText",
    "simple_title_properties",
    "parent_ref",
]


def parent_ref(page_id: str):
    """Format a `page_id` as a parent reference for new page creation."""
    return {
        "type": "page_id",
        "page_id": page_id,
    }


class BlockType(str, Enum):
    """Enumerates supported block types for Notion.

    Not complete, but enough to get the general idea and to implement what we need
    you can find the rest here: https://developers.notion.com/reference/block
    """

    Paragraph = "paragraph"
    Heading1 = "heading_1"
    Heading2 = "heading_2"
    Heading3 = "heading_3"
    BulletedListItem = "bulleted_list_item"
    NumberedListItem = "numbered_list_item"
    File = "file"
    ToDo = "to_do"
    Toggle = "toggle"


def simple_title_properties(title: str):
    """Generate a full property block for a new page consisting only of a title."""
    return {"type": "title", "title": [{"type": "text", "text": {"content": title}}]}


class RichText:
    """Namespaced utilities for creating Notion rich text objects."""

    @staticmethod
    def plain_text(text):
        """Create a plain rich text object.

        This is used as a utility method for other rich text
        creation routines.
        """
        return {
            "plain_text": text,
            "annotations": {
                "bold": False,
                "italic": False,
                "strikethrough": False,
                "underline": False,
                "code": False,
                "color": "default",
            },
            "type": "text",
            "text": {
                "content": text,
            },
        }

    @staticmethod
    def code(text):
        """Create a code-type rich text object."""
        block = RichText.plain_text(text)

        block["annotations"]["code"] = True
        return block

    @staticmethod
    def bold(text):
        """Create a bold rich text object."""
        block = RichText.plain_text(text)

        block["annotations"]["bold"] = True
        return block


class Block:
    """Namespaced utilities for creating Notion block objects."""

    @staticmethod
    def wrap_rich_text_list(possibly_text):
        """Ensure that the argument is a list of rich text objects.

        If the argument is singular, it will be turned into a list.
        Each item will have `RichText.plain_text` called on it if
        it is only a `str`.
        """
        if not isinstance(possibly_text, list):
            possibly_text = [possibly_text]

        as_rich_text = []
        for possible_item in possibly_text:
            if isinstance(possible_item, str):
                possible_item = RichText.plain_text(possible_item)

            as_rich_text.append(possible_item)

        return as_rich_text

    @staticmethod
    def todo(text, checked=False, children=None):
        """Create a TO_DO block."""
        text = Block.wrap_rich_text_list(text)

        if children is None:
            children = []

        return {
            "object": "block",
            "type": BlockType.ToDo,
            BlockType.ToDo: {"text": text, "checked": checked, "children": children},
        }

    @staticmethod
    def h1(text):
        """Create a `heading_1` block. These cannot have children."""
        text = Block.wrap_rich_text_list(text)
        return {
            "object": "block",
            "type": BlockType.Heading1,
            BlockType.Heading1: {
                "text": text,
            },
        }

    @staticmethod
    def h2(text):
        """Create a `heading_2` block. These cannot have children."""
        text = Block.wrap_rich_text_list(text)
        return {
            "object": "block",
            "type": BlockType.Heading2,
            BlockType.Heading2: {
                "text": text,
            },
        }

    @staticmethod
    def h3(text):
        """Create a `heading_3` block. These cannot have children."""
        text = Block.wrap_rich_text_list(text)
        return {
            "object": "block",
            "type": BlockType.Heading3,
            BlockType.Heading3: {
                "text": text,
            },
        }

    @staticmethod
    def href(link_url, text):
        """Create a paragraph block which represents a link with standard styling."""
        text = RichText.plain_text(text)
        text["href"] = link_url
        text["text"]["link"] = {
            "type": "url",
            "url": link_url,
        }
        text["annotations"]["underline"] = True
        text["annotations"]["color"] = "blue"

        return Block.paragraph([text], [])

    @staticmethod
    def paragraph(text, children: List[Any] = None):
        """Create a paragraph block."""
        text = Block.wrap_rich_text_list(text)
        if children is None:
            children = []

        return {
            "object": "block",
            "type": BlockType.Paragraph,
            BlockType.Paragraph: {
                "text": text,
                "children": children,
            },
        }

    @staticmethod
    def prepend_child(block, child):
        """Insert a new child at the front of the block children.

        Like the rest of the methods here, this is for constructing block objects
        and consequently does not actually talk to the API.
        """
        block_type = block["type"]
        block[block_type]["children"] = [child] + block[block_type]["children"]
        return block
