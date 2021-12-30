from enum import Enum
from typing import Any, List

__all__ = [
    "BlockType",
    "Block",
    "simple_title_properties",
    "parent_ref",
]

def parent_ref(page_id: str):
    return {
        "type": "page_id",
        "page_id": page_id,
    }

class BlockType(str, Enum):
    # Not complete, but enough to get the general idea and to implement what we need
    # you can find the rest here: https://developers.notion.com/reference/block
    Paragraph = "paragraph"
    Heading1 = "heading_1"
    Heading2 = "heading_2"
    Heading3 = "heading_3"
    BulletedListItem = "bulleted_list_item"
    NumberedListItem = "numbered_list_item"
    File = "file"
    ToDo = "to_do"
    Toggle = "toggle"
    ChildPage = "child_page"

def simple_title_properties(title: str):
    return {
        "type": "title",
        "title": [{ "type": "text", "text": {"content": title}}]
    }

def plain_text(text):
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
        }
    }

def code(text):
    block = plain_text(text)

    block["annotations"]["code"] = True
    return block

def bold(text):
    block = plain_text(text)
    
    block["annotations"]["bold"] = True
    return block


class Block:
    @staticmethod
    def wrap_rich_text_list(possibly_text):
        if not isinstance(possibly_text, list):
            possibly_text = [possibly_text]
        
        as_rich_text = []
        for possible_item in possibly_text:
            if isinstance(possible_item, str):
                possible_item = plain_text(possible_item)
            
            as_rich_text.append(possible_item)
    
        return as_rich_text

    @staticmethod
    def todo(text, checked=False, children=None):
        text = Block.wrap_rich_text_list(text)

        if children is None:
            children = []

        return {
            "object": "block",
            "type": BlockType.ToDo,
            BlockType.ToDo: {
                "text": text,
                "checked": checked,
                "children": children 
            },

        }
    @staticmethod
    def h1(text):
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
        text = Block.wrap_rich_text_list(text)
        return {
            "object": "block",
            "type": BlockType.Heading3,
            BlockType.Heading3: {
                "text": text,
            },
        }

    @staticmethod
    def file(external_url, caption):
        caption = Block.wrap_rich_text_list(caption)
        return {
            "object": "block",
            "type": BlockType.File,
            "caption": caption,
            BlockType.File: {
                "type": "external",
                "external": {
                    "url": external_url,
                },
            }
        }

    @staticmethod
    def href(link_url, text):
        text = plain_text(text)
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
        text = Block.wrap_rich_text_list(text)
        if children is None:
            children = []

        return {
            "object": "block",
            "type": BlockType.Paragraph,
            BlockType.Paragraph: {
                "text": text,
                "children": children,
            }
        }

    @staticmethod
    def child_page(title: str):
        title = Block.wrap_rich_text_list(title)
        return {
            "object": "block",
            "type": "child_page",
            "child_page": {
                "title": title
            }
        }

    @staticmethod
    def prepend_child(block, child):
        block_type = block["type"]
        block[block_type]["children"] = [child] + block[block_type]["children"]
        return block