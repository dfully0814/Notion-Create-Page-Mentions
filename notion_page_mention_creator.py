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
existing_pages = set()

def retrieve_pages(database_id):
    """Retrieve all pages from the specified database"""
    return notion.databases.query(**{'database_id': database_id})

def get_page_name(name, database_id):
    search_params = {
        "query": name,
        "filter": {
            "value": "page",
            "property": "object"
        }
    }
    return notion.search(**search_params)

def create_page(name, database_id):
    return '12345'

def process_bracket_words(bracket_words, database_id):
    """Process words in brackets and replace them with page mentions."""
    for bracket_name in bracket_words:
        if bracket_name.lower() not in existing_pages:
            page_results = get_page_name(bracket_name, database_id)
            
            if page_results:
                for result in page_results['results']:
                    page_name = result['properties']['Name']['title'][0]['plain_text']
                    if page_name.lower() == bracket_name.lower():
                        existing_pages.add(page_name.lower())
                        break
            else:
                page_results = create_page(bracket_name[0].upper() + bracket_name[1:], database_id)
        # Replace the bracketed word with a page mention
        text_content = text_content.replace(f'[[{bracket_name}]]', f'<Notion page mention with id {page_results}>')
    return text_content

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
    if bracket_words:
        process_bracket_words(bracket_words, database_id)
        
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
