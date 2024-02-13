class Block:
    def __init__(self, page_block) -> None:
        self.page_block = page_block

    def plain_text(self) -> str:
        raise NotImplementedError

    def update_payload(self, updated_text: str) -> dict:
        raise NotImplementedError
    
    def block_type(self) -> str:
        raise NotImplementedError
    
class BulletListItem(Block):
    def plain_text(self):
        return self.page_block["bulleted_list_item"]["rich_text"][0]["plain_text"]
    
    def update_payload(self, updated_text: str):
        return {
            "bulleted_list_item": {
                "rich_text": [{"type": "text", "text": {"content": updated_text}}]
            }
        }
    
    def block_type(self) -> str:
        return BlockTypeConstants.BULLET_LIST_ITEM
    
    
class NumberedListItem(Block):
    def plain_text(self):
        return self.page_block["numbered_list_item"]["rich_text"][0]["plain_text"]
    
    def update_payload(self, updated_text: str):
        return {
            "numbered_list_item": {
                "rich_text": [{"type": "text", "text": {"content": updated_text}}]
            }
        }
    
    def block_type(self) -> str:
        return BlockTypeConstants.NUMBERED_LIST_ITEM
    
class Heading(Block):
    def __init__(self, page_block, heading_type) -> None:
        super().__init__(page_block)
        self.heading_type = heading_type
        
    def plain_text(self):
        return self.page_block[self.heading_type]["rich_text"][0]["plain_text"]
    
    def update_payload(self, updated_text: str):
        return {
            self.heading_type: {
                "rich_text": [{"type": "text", "text": {"content": updated_text}}]
            }
        }
    
    def block_type(self) -> str:
        return self.heading_type
    
class Toggle(Block):
    
    def plain_text(self):
        return self.page_block['toggle']['rich_text'][0]['plain_text']
    
    def update_payload(self, updated_text: str):
        return {
            "toggle": {
                "rich_text": [{"type": "text", "text": {"content": updated_text}}]
            }
        }
    
    def block_type(self) -> str:
        return BlockTypeConstants.TOGGLE
        
class Paragraph(Block):
    def plain_text(self):
        final_text = []
        for line in self.page_block['paragraph']['rich_text']:
            final_text.append(line['plain_text'])
        return ''.join(final_text)
    
    def update_payload(self, updated_text: str):
        return {
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": updated_text}}]
            }
        }
    
    def block_type(self) -> str:
        return BlockTypeConstants.PARAGRAPH
        
    
class BlockTypeConstants:  
    BULLET_LIST_ITEM = "bulleted_list_item"
    NUMBERED_LIST_ITEM = "numbered_list_item"
    PARAGRAPH = 'paragraph'
    TOGGLE = 'toggle'