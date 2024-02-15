"""Module providing system functions"""
import json
import os
import re
import time
import logging
from dotenv import load_dotenv
from notion_client import Client
from block_types import Block
from block_types import BulletListItem
from block_types import BlockTypeConstants
from block_types import Heading
from block_types import NumberedListItem
from block_types import Paragraph
from block_types import Toggle

# Load environment variables from .env file
load_dotenv()

# Set up the logger
logging.basicConfig(filename='notion_page_mention_creator.log', level=logging.ERROR)

#Initialize the client
notion = Client(auth=os.getenv('NOTION_TOKEN'))
block_type_constants = BlockTypeConstants()
existing_pages_dict = {}
page_name_to_id_dict = {}

def retrieve_pages(database_id):
    """Retrieve all pages from the specified database"""
    return notion.databases.query(**{'database_id': database_id})

def search_page(name):
    search_params = {
        "query": name,
        "filter": {
            "value": "page",
            "property": "object"
        }
    }
    return notion.search(**search_params)

def create_page(page_name, database_id):
    """Creates a new Notion page using the Notion Python SDK"""
    proper_page_name = title_case_except_articles(page_name)
    create_parameters = {
        'parent': {
            'type': 'database_id',
            'database_id': database_id
        },
        'properties': {
            'Name': {
                'title': [
                    {
                        'text': {
                            'content': proper_page_name
                        }
                    }
                ]
            },
            'Type': {
                'select': {
                    'name': 'Review'
                }
            }
        } 
    }

    return notion.pages.create(**create_parameters)["id"]
        
            
def title_case_except_articles(text):
    """
    Capitalizes every word in the page name if there are multiple words, except small words and articles unless they are the first word in the page name
    """
    small_words = {'the', 'a', 'an', 'in', 'on', 'at', 'to', 'by', 'with', 
                   'over', 'under', 'from', 'and', 'but', 'or', 'nor', 'for', 
                   'so', 'yet', 'as', 'if', 'then', 'that', 'than', 'when', 
                   'who', 'whom', 'whose'}
    
    words = text.split()
    new_title = []
    for word in words:
        if word.lower() in small_words and words.index(word) != 0:
            new_title.append(word.lower())
        else:
            new_title.append(word.capitalize())
    
    return ' '.join(new_title)


def process_child_block(child_block, database_id):
    """Process words in brackets and replace them with page mentions."""
    try:
        child_bock_type = get_block_type(child_block)

        if (child_bock_type == None):
            return
        
        child_block_mentions = re.findall(r'\[\[(.*?)\]\]', child_bock_type.plain_text())

        populate_page_name_by_id_dict(database_id, child_block_mentions)

        if (len(child_block_mentions) > 0):
            # Split the block text into parts at each [[]] page mention
            child_block_text_parts = re.split(r"(?<=\]\])|(?=\[\[)", child_bock_type.plain_text())

            # Initialize the rich text array
            rich_text = []

            # Iterate over the parts
            for part in child_block_text_parts:
                # If the part is a mention
                if part.startswith("[[") and part.endswith("]]"):
                    # Remove the brackets to get the page name
                    page_name = part[2:-2]

                    # Check if the page exists and get its ID
                    if (page_name.lower().startswith('the ')):
                        page_name = page_name[4:]

                    page_id = page_name_to_id_dict.get(page_name.lower())
                    
                    if (page_id == None):
                        raise Exception(f"Page ID not found for page name: {page_name}")
                    
                    # Create a mention block
                    block = {
                        "type": "mention",
                        "mention": {
                            "type": "page",
                            "page": {
                                "id": page_id
                            }
                        }
                    }
                else:
                    # If the part is not a mention, create a text block
                    block = {
                        "type": "text",
                        "text": {
                            "content": part
                        }
                    }
                # Add the block to the rich_text array
                rich_text.append(block)

            # Create the new mention block
            mention_block = {
                child_bock_type.block_type(): {
                    "rich_text": rich_text
                }
            }

            # Update the original block
            notion.blocks.update(block_id=child_block["id"], **mention_block)

            time.sleep(1)
    except Exception as e:
        logging.error(f"An error occurred: {e} for block.")

def populate_page_name_by_id_dict(database_id, child_block_mentions):
    try:
        for child_block_mention in child_block_mentions:
            child_block_mention_lower = child_block_mention.lower()[4:] if child_block_mention.lower().startswith('the ') else child_block_mention.lower()
            # We haven't yet found the page id for the page name
            if child_block_mention_lower not in page_name_to_id_dict:
                searched_pages = search_page(child_block_mention_lower)
                if searched_pages['results']:
                    exact_match_page_id = None
                    for page in searched_pages['results']:

                        # Compare each page's name to see if there's an exact match
                        if 'Name' not in page['properties']:
                            continue

                        page_name = page['properties']['Name']['title'][0]['plain_text'].lower()
                        if child_block_mention_lower == page_name:
                            exact_match_page_id = page['id']
                            break  # Stop searching once we've found an exact match
                    if exact_match_page_id:
                        # An exact match was found, use this page's ID
                        page_name_to_id_dict[child_block_mention_lower] = exact_match_page_id
                    else:
                        # No exact match found, create a new page
                        page_id = create_page(child_block_mention_lower, database_id)
                        page_name_to_id_dict[child_block_mention_lower] = page_id
                else:
                    # Search returned no results, create a new page
                    page_id = create_page(child_block_mention_lower, database_id)
                    page_name_to_id_dict[child_block_mention_lower] = page_id
    except Exception as e:
        logging.error(f"An error occurred: {e} for block.")

def process_block(child_block, database_id):
    """Process a single block and its child blocks."""

    process_child_block(child_block, database_id)
        
    if 'has_children' in child_block and child_block['has_children'] == True:
        child_blocks = notion.blocks.children.list(block_id=child_block['id'])

        for child_block in child_blocks['results']:
            process_block(child_block, database_id)

def get_block_type(child_block) -> Block:
    """
    Returns a block object based on the block type
    """
    block_type = None

    if child_block['type'] == block_type_constants.BULLET_LIST_ITEM:
        block_type = BulletListItem(page_block=child_block)
        # Find all occurrences of '[[]]' and extract the wor within it
            
    elif 'heading' in child_block['type']:
        block_type = Heading(page_block=child_block, heading_type=child_block['type'])
        
    elif child_block['type'] == block_type_constants.NUMBERED_LIST_ITEM:
        block_type = NumberedListItem(page_block=child_block)
    
    elif child_block['type'] == block_type_constants.PARAGRAPH:
        block_type = Paragraph(child_block)
        
    elif child_block['type'] == block_type_constants.TOGGLE:
        block_type = Toggle(child_block)

    return block_type
            
def find_and_process_bracket_words(page_id, database_id):
    """Find words surrounded by '[[]]', process them, and replace with page mention."""
    child_blocks = notion.blocks.children.list(page_id)
    for child_block in child_blocks['results']:
        process_block(child_block, database_id)
    
DATABASE_ID = ''

has_more = True
next_cursor = None

while has_more:
    # Fetch all pages in the database
    pages = notion.databases.query(
        database_id=DATABASE_ID,
        start_cursor=next_cursor
    )

    for page in pages["results"]:
        try:
            print(f"Processing blocks for page: {page['properties']['Name']['title'][0]['plain_text']}")

            # for page in pages['results']:
            find_and_process_bracket_words(page['id'], DATABASE_ID)

            print(f"Blocks for {page['properties']['Name']['title'][0]['plain_text']} successfully processed.")

        except Exception as e:
            logging.error(f"An error occurred: {e} for block.")
        
    has_more = pages.get("has_more", False)
    next_cursor = pages.get("next_cursor")
