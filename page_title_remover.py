import time
from notion_client import Client
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Notion client with your integration token
notion = Client(auth=os.getenv("NOTION_TOKEN"))

def update_page_titles(database_id):
    """
    Updates page titles in the specified Notion database.
    Removes 'The ' from the start of any page title.
    """
    try:
        has_more = True
        next_cursor = None

        while has_more:
            # Fetch all pages in the database
            query_results = notion.databases.query(
                database_id=database_id,
                start_cursor=next_cursor
            )

            for page in query_results["results"]:
                # Assuming title is in the first text object of the title property
                current_title = page["properties"]["Name"]["title"][0]["text"]["content"]
                
                # Check if the title starts with 'The ' and update if necessary
                if current_title.startswith("The "):
                    new_title = current_title[4:]  # Remove 'The ' from the start
                    # Construct the update payload
                    update_payload = {
                        "properties": {
                            "Name": {
                                "title": [
                                    {
                                        "text": {
                                            "content": new_title
                                        }
                                    }
                                ]
                            }
                        }
                    }
                    # Update the page
                    notion.pages.update(page_id=page["id"], **update_payload)
                    print(f"Updated page title from '{current_title}' to '{new_title}'")
                    time.sleep(1);

                has_more = query_results.get("has_more", False)
                next_cursor = query_results.get("next_cursor")
            
            if (has_more):
                results_length = len(query_results.get("results"))
                print(f"{results_length} have been searched. Searching next batch.")
    except Exception as e:
        print(f"An error occurred: {e} for page: " + current_title)

# Example usage
database_id = "dc8f63b3bc874a93818676af32fbad0e"
update_page_titles(database_id)
