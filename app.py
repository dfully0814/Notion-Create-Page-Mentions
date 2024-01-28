import os
import re
from block_types import BulletListItem
from block_types import BlockTypeConstants
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()

notion = Client(auth=os.environ["NOTION_TOKEN"])

# loop through each notion page in the database
page = notion.pages.retrieve(page_id="c5a6f4a33cbd4fd196e88376c103e54b")

# set collection of text-based page block child types to use for searching
PAGE_BLOCK_CHILD_TYPES = {
    "heading_1",
    "heading_2",
    "heading_3"
    "rich_text",
    "bulleted_list_item",
    "numbered_list_item",
    "paragraph",
    "quote",
    "to_do",
    "toggle"
}

page_block_children = notion.blocks.children.list(block_id=page["id"])
all_matches_by_page_block_id = {}

def has_page_mentions(text):
    # Regular expression to use for finding bracketed page mentions
    pattern = r'\[\[(.*?)\]\]'
    # All pattern matches
    matches = re.findall(pattern, text)
    return bool(matches)

def update_child_page_block_with_mentions(all_matches_by_page_block_id):
    for page_block_id, page_block_text in all_matches_by_page_block_id.items():
        updated_block_content = {
            "paragraph": {
                "text": [
                    # Exiting text content
                    {
                        "type": "text",
                        "text": {
                            "content": page_block_text
                        }
                    },
                    # Add page mention
                ]
            }
        }
        

for child_block in page_block_children["results"]:
    block_plain_text = ""

    if child_block["type"] == BlockTypeConstants().bullet_list_item():
        block_plain_text = BulletListItem(page_block=child_block).plain_text()

    if (has_page_mentions(block_plain_text)):
        all_matches_by_page_block_id[child_block["id"]] = block_plain_text

print(all_matches_by_page_block_id)
    