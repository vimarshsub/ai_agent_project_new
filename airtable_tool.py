
import os
import requests
from airtable import Airtable

# --- Airtable Configuration (Hardcoded as per user request) ---
AIRTABLE_API_KEY = "patsURhjwJWu40rpv.eb8960d151bfcbd141a55521d7072a4a11b6dcdc17af7d206f35813cf37a4863"
AIRTABLE_BASE_ID = "appLu7BlsSJ0MzwXt"
AIRTABLE_TABLE_NAME = "Announcements"
# --- End Airtable Configuration ---

class AirtableTool:
    def __init__(self):
        try:
            self.airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)
            # Perform a simple test call to ensure connection, e.g., get one record
            self.airtable.get_all(max_records=1) 
        except Exception as e:
            print(f"Error initializing Airtable connection: {e}")
            self.airtable = None # Set to None if initialization fails

    def get_all_announcements(self):
        """Fetches all announcements from the Airtable base."""
        if not self.airtable:
            return "Error: Airtable connection not initialized."
        try:
            records = self.airtable.get_all()
            if not records:
                return "No announcements found."
            return [record["fields"] for record in records if "fields" in record]
        except Exception as e:
            error_msg = f"Error fetching all announcements: {str(e)}"
            print(error_msg)
            return error_msg

    def search_announcements(self, search_text):
        """Searches announcements by text in Title or Description fields."""
        if not self.airtable:
            return "Error: Airtable connection not initialized."
        try:
            search_text_lower = search_text.lower()
            all_announcements_result = self.get_all_announcements()
            if isinstance(all_announcements_result, str) and all_announcements_result.startswith("Error:"):
                return all_announcements_result # Propagate error from get_all_announcements
            if all_announcements_result == "No announcements found.":
                 return f"No announcements found to search within for 	'{search_text}	'."

            matched_announcements = []
            for record_fields in all_announcements_result:
                title = record_fields.get("Title", "").lower()
                description = record_fields.get("Description", "").lower()
                if search_text_lower in title or search_text_lower in description:
                    matched_announcements.append(record_fields)
            
            if not matched_announcements:
                return f"No announcements found matching 	'{search_text}	'."
            return matched_announcements
        except Exception as e:
            error_msg = f"Error searching announcements for 	'{search_text}	': {str(e)}"
            print(error_msg)
            return error_msg

    def _get_first_attachment_url(self, record_fields):
        """Helper to get the URL and filename of the first attachment from a record."""
        attachments = record_fields.get("Attachments")
        if attachments and isinstance(attachments, list) and len(attachments) > 0:
            first_attachment = attachments[0]
            if isinstance(first_attachment, dict) and "url" in first_attachment:
                return first_attachment["url"], first_attachment.get("filename", "downloaded_file")
        return None, None # Return None, None if no suitable attachment found

    def get_attachment_from_announcement(self, announcement_id=None, search_term=None, get_latest=False):
        """
        Gets the attachment URL and filename from a specific announcement.
        Priority: announcement_id, then search_term, then get_latest.
        Returns a tuple (url, filename) or an error string.
        """
        if not self.airtable:
            return "Error: Airtable connection not initialized.", None
        
        target_record_fields = None
        try:
            if announcement_id:
                record = self.airtable.get(announcement_id)
                if record and "fields" in record:
                    target_record_fields = record["fields"]
                else:
                    return f"Error: Announcement with ID 	'{announcement_id}	' not found.", None
            elif search_term:
                results = self.search_announcements(search_term)
                if isinstance(results, str): # Error or no results from search
                    return f"Could not find announcement via search term 	'{search_term}	' to get attachment: {results}", None
                if results: # results is a list of records
                    target_record_fields = results[0] # Get the first matching announcement
                else:
                    return f"No announcement found matching search term 	'{search_term}	' to get attachment from.", None
            elif get_latest:
                records = self.airtable.get_all(sort=[("SentTime", "desc")])
                if records and "fields" in records[0]:
                    target_record_fields = records[0]["fields"]
                else:
                    return "Error: Could not retrieve the latest announcement or no announcements exist.", None
            else:
                return "Error: No criteria (ID, search term, or latest) provided to find an announcement.", None
            
            if target_record_fields:
                url, filename = self._get_first_attachment_url(target_record_fields)
                if url and filename:
                    return url, filename
                else:
                    ann_title = target_record_fields.get("Title", "[Unknown Title]")
                    return f"No attachment found in the announcement titled 	'{ann_title}	'.", None
            else:
                # This case should ideally be caught by earlier checks
                return "Error: No matching announcement found to get attachment from.", None

        except Exception as e:
            error_msg = f"Error getting attachment: {str(e)}"
            print(error_msg)
            return error_msg, None

    def download_file(self, url, save_path="/tmp"):
        """Downloads a file from a URL to a local path. Returns filepath or error string."""
        if not url:
            return "Error: No URL provided for download."
        try:
            response = requests.get(url, stream=True, timeout=30) # Added timeout
            response.raise_for_status() 
            
            content_disposition = response.headers.get("content-disposition")
            filename = None
            if content_disposition:
                import re
                fname = re.findall("filename=(.+)", content_disposition)
                if fname:
                    filename = fname[0].strip("\"").strip("'") # Handle both quote types
            if not filename:
                from urllib.parse import unquote
                filename = unquote(url.split("/")[-1].split("?")[0])
            
            if not filename: # Fallback filename
                filename = "downloaded_attachment"

            # Ensure filename has an extension, default to .pdf if not obvious
            if "." not in os.path.basename(filename):
                content_type = response.headers.get("content-type", "").lower()
                if "pdf" in content_type:
                    filename += ".pdf"
                elif "openxmlformats-officedocument.wordprocessingml.document" in content_type:
                    filename += ".docx"
                elif "plain" in content_type:
                    filename += ".txt"
                else:
                     filename += ".pdf" # Default as per user's earlier statement
            
            # Sanitize filename to prevent path traversal or invalid characters
            # A more robust sanitization might be needed depending on expected filenames
            filename = "".join(c for c in filename if c.isalnum() or c in (".", "-", "_")).rstrip()
            if not filename:
                filename = "sanitized_download.pdf"

            local_filepath = os.path.join(save_path, filename)
            os.makedirs(save_path, exist_ok=True)
            
            with open(local_filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"File downloaded successfully to {local_filepath}")
            return local_filepath
        except requests.exceptions.Timeout:
            error_msg = f"Error downloading file from {url}: Request timed out."
            print(error_msg)
            return error_msg
        except requests.exceptions.RequestException as e:
            error_msg = f"Error downloading file from {url}: {str(e)}"
            print(error_msg)
            return error_msg
        except IOError as e:
            error_msg = f"Error saving file to {local_filepath}: {str(e)}"
            print(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"An unexpected error occurred during download: {str(e)}"
            print(error_msg)
            return error_msg

# Example Usage (for testing purposes, will be removed or commented out)
if __name__ == '__main__':
    tool = AirtableTool()
    if not tool.airtable:
        print("AirtableTool could not be initialized. Exiting tests.")
        exit()

    print("--- All Announcements ---")
    all_announcements = tool.get_all_announcements()
    if isinstance(all_announcements, list):
        if all_announcements:
            for ann in all_announcements[:2]: # Print first 2
                print(f"Title: {ann.get('Title')}, SentTime: {ann.get('SentTime')}")
        else:
            print("No announcements found (empty list).") 
    else: # Error string
        print(all_announcements)

    print("\n--- Search Announcements (e.g., 'Q2') ---")
    query = "Q2"
    searched_announcements = tool.search_announcements(query)
    if isinstance(searched_announcements, list):
        if searched_announcements:
            for ann in searched_announcements[:2]: # Print first 2 results
                print(f"Title: {ann.get('Title')}, Description: {ann.get('Description')}")
        else:
            print(f"No announcements found for query 	'{query}	' (empty list).")
    else: # Error string
        print(searched_announcements)

    print("\n--- Get Attachment from Latest Announcement ---")
    latest_attachment_url, latest_filename = tool.get_attachment_from_announcement(get_latest=True)
    if latest_filename is None and latest_attachment_url.startswith("Error:"):
        print(latest_attachment_url) # Print error message
    elif latest_attachment_url:
        print(f"Latest attachment URL: {latest_attachment_url}, Filename: {latest_filename}")
        # downloaded_file_path = tool.download_file(latest_attachment_url, "/tmp/test_downloads")
        # print(f"Download result: {downloaded_file_path}")
    else:
        print("No attachment found for the latest announcement or unexpected issue.")

    print("\n--- Get Attachment by Search (e.g., 'report') ---")
    search_term_for_attach = "report" 
    searched_attachment_url, searched_filename = tool.get_attachment_from_announcement(search_term=search_term_for_attach)
    if searched_filename is None and searched_attachment_url.startswith("Error:"):
        print(searched_attachment_url)
    elif searched_attachment_url:
        print(f"Attachment URL for search 	'{search_term_for_attach}	': {searched_attachment_url}, Filename: {searched_filename}")
        # downloaded_search_file_path = tool.download_file(searched_attachment_url, "/tmp/test_downloads")
        # print(f"Download result: {downloaded_search_file_path}")
    else:
        print(f"No attachment found for search term 	'{search_term_for_attach}	' or unexpected issue.")

    # Test with a non-existent ID
    print("\n--- Get Attachment by Non-existent Announcement ID ---")
    specific_ann_id = "recNONEXISTENTID"
    id_attachment_url, id_filename = tool.get_attachment_from_announcement(announcement_id=specific_ann_id)
    if id_filename is None and id_attachment_url.startswith("Error:"):
        print(id_attachment_url)
    elif id_attachment_url:
        print(f"Attachment URL for ID 	'{specific_ann_id}	': {id_attachment_url}, Filename: {id_filename}")
    else:
        print(f"No attachment found for ID 	'{specific_ann_id}	' or unexpected issue.")


