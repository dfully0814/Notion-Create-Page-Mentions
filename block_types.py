class BulletListItem:
    def __init__(self, page_block) -> None:
        self.page_block = page_block
        
    def plain_text(self):
        return self.page_block["bulleted_list_item"]["rich_text"][0]["plain_text"]
    
    def type_name(self):
        return "bulleted_list_item"
    
class BlockTypeConstants:  
    BULLET_LIST_ITEM = "bulleted_list_item"
    def bullet_list_item(self):
        return self.BULLET_LIST_ITEM