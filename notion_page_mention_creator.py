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

def create_page_mentions(existing_pages, database_id):
    """
    Use the existing_pages dictionary to create all of the new page mentions using the Notion Python SDK.
    """
    for page_id, page_info in existing_pages.items():
        page_name = page_info['page_name']
        block_mention_ids = page_info['page_block_mention_ids']

        for block_id in block_mention_ids:
            # Assuming each block needs to be updated to mention the page
            # Fetch the block
            block = notion.blocks.retrieve(block_id)
            
            # Construct the updated content for the block
            # This part highly depends on the structure of your blocks and how you want to format the mention
            # Assuming you're replacing some placeholder or appending the mention at the end of the existing text
            updated_content = block['your_text_field'] + f" Mentioning {page_name}"
            
            # Update the block with the new content
            # Note: You'll need to adjust the structure of the update payload based on the specific type of block
            update_payload = {
                "your_text_field": {
                    "type": "text",
                    "text": {
                        "content": updated_content
                    }
                }
            }
            notion.blocks.update(block_id, **update_payload)


def process_bracket_words(bracket_words_dict, database_id):
    """Process words in brackets and replace them with page mentions."""
    for bracket_word in bracket_words_dict['bracket_words']:
        bracket_word_lower = bracket_word.lower()
        
        # Check if the page already exists
        if bracket_word_lower in page_name_to_id_dict:
            # The page exists, so fetch its ID and update the mention IDs
            page_id = page_name_to_id_dict[bracket_word_lower]
            existing_pages_dict[page_id]['page_block_mention_ids'].add(bracket_words_dict['page_block_id_mention'])
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
                    existing_pages_dict[created_page_id] = {
                        'page_name': bracket_word_lower,
                        'page_block_mention_ids': {bracket_words_dict['page_block_id_mention']}
                    }
                    page_name_to_id_dict[bracket_word_lower] = page_id
                else:
                    # Page exists but is not in the dictionary, retrieve its ID, and update the mention IDs
                    page_id = next((page['id'] for page in queried_pages['results'] if page['properties']['Name']['title'][0]['plain_text'].lower() == bracket_word_lower), None)
                    if page_id:
                        existing_pages_dict[page_id]['page_block_mention_ids'].add(bracket_words_dict['page_block_id_mention'])
                        page_name_to_id_dict[proper_page_name.lower()] = page_id
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
