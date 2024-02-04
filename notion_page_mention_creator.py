"""Module providing system functions"""
import os
import re
from notion_client import Client
from block_types import BulletListItem
from block_types import BlockTypeConstants
from block_types import Heading
from block_types import NumberedListItem
from block_types import Paragraph
from block_types import Toggle

#Initialize the client
notion = Client(auth=os.getenv('NOTION_TOKEN'))
block_type_constants = BlockTypeConstants()
existing_pages = {}
page_name_to_id = {}

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
                            'content': page_name
                        }
                    }
                ]
            }
        }    
    }
    
    return notion.pages.create(**create_parameters)

def process_bracket_words(bracket_words_dict, database_id):
    """Process words in brackets and replace them with page mentions."""
    for bracket_word in bracket_words_dict['bracket_words']:
        bracket_word_lower = bracket_word.lower()
        
        # Check if the page already exists
        if bracket_word_lower in page_name_to_id:
            # The page exists, so fetch its ID and update the mention IDs
            page_id = page_name_to_id[bracket_word_lower]
            existing_pages[page_id]['page_block_mention_ids'].add(bracket_words_dict['page_block_id_mention'])
        else:
            # The page doesn't exist, so create it or fetch its ID
            queried_pages = search_page(bracket_word)
            if queried_pages:
                queried_page_names = {page['properties']['Name']['title'][0]['plain_text'].lower() for page in queried_pages['results']}
                
                if bracket_word_lower not in queried_page_names:
                    # Create a new page
                    proper_page_name = bracket_word.capitalize()
                    created_page = create_page(proper_page_name, database_id)
                    created_page_id = created_page['id']
                    
                    # Update the existing_pages and page_name_to_id dictionaries
                    existing_pages[created_page_id] = {
                        'page_name': bracket_word_lower,
                        'page_block_mention_ids': {bracket_words_dict['page_block_id_mention']}
                    }
                    page_name_to_id[bracket_word_lower] = page_id
                else:
                    # Page exists but is not in the dictionary, retrieve its ID, and update the mention IDs
                    page_id = next((page['id'] for page in queried_pages['results'] if page['properties']['Name']['title'][0]['plain_text'].lower() == bracket_word_lower), None)
                    if page_id:
                        existing_pages[page_id]['page_block_mention_ids'].add(bracket_words_dict['page_block_id_mention'])
                        page_name_to_id[proper_page_name.lower()] = page_id 
    # Replace the bracketed word with a page mention

def process_block(block, database_id):
    """Process a single block and its child blocks."""
    text = ''
    
    if block['type'] == block_type_constants.BULLET_LIST_ITEM:
        text = BulletListItem(page_block=block).plain_text()
        # Find all occurrences of '[[]]' and extract the wor within it
            
    elif 'heading' in block['type']:
        text = Heading(page_block=block, heading_type=block['type']).plain_text()
        
    elif block['type'] == block_type_constants.NUMBERED_LIST_ITEM:
        text = NumberedListItem(page_block=block).plain_text()
    
    elif block['type'] == block_type_constants.PARAGRAPH:
        text = Paragraph(block).plain_text()
        
    elif block['type'] == block_type_constants.TOGGLE:
        text = Toggle(block).plain_text()
        
    bracket_words = re.findall(r'\[\[(.*?)\]\]', text)
    bracket_words_dict = {
        'bracket_words': bracket_words,
        'page_block_id_mention': block['id']
    }
    if bracket_words:
        process_bracket_words(bracket_words_dict, database_id)
        
    if'has_children' in block and block['has_children']:
        child_blocks = notion.blocks.children.list(block_id=block['id'])
        for child_block in child_blocks['results']:
            process_block(child_block, database_id)
    
def find_and_process_bracket_words(page_id, database_id):
    """Find words surrounded by '[[]]', process them, and replace with page mention."""
    blocks = notion.blocks.children.list(page_id)
    for block in blocks['results']:
        process_block(block, database_id)
        
DATABASE_ID = 'dc8f63b3bc874a93818676af32fbad0e'

page = notion.pages.retrieve(**{'page_id': 'f313100cf2034db4b54dc925d380d341'})

# for page in pages['results']:
find_and_process_bracket_words(page['id'], DATABASE_ID)
