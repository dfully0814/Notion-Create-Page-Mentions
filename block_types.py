class BulletListItem:
    def __init__(self, page_block) -> None:
        self.page_block = page_block
        
    def plain_text(self):
        return self.page_block["bulleted_list_item"]["rich_text"][0]["plain_text"]

class NumberedListItem:
    def __init__(self, page_block) -> None:
        self.page_block = page_block
        
    def plain_text(self):
        return self.page_block["numbered_list_item"]["rich_text"][0]["plain_text"]
    
class Heading:
    def __init__(self, page_block, heading_type) -> None:
        self.page_block = page_block
        self.heading_type = heading_type
        
    def plain_text(self):
        return self.page_block[self.heading_type]["rich_text"][0]["plain_text"]
    
class Toggle:
    def __init__(self, page_block) -> None:
        self.page_block = page_block
    
    def plain_text(self):
        return self.page_block['toggle']['rich_text'][0]['plain_text']
        
class Paragraph:
    def __init__(self, page_block) -> None:
        self.page_block = page_block
        
    def plain_text(self):
        final_text = []
        for line in self.page_block['paragraph']['rich_text']:
            final_text.append(line['plain_text'])
        return ''.join(final_text)
        
    
class BlockTypeConstants:  
    BULLET_LIST_ITEM = "bulleted_list_item"
    NUMBERED_LIST_ITEM = "numbered_list_item"
    PARAGRAPH = 'paragraph'
    TOGGLE = 'toggle'