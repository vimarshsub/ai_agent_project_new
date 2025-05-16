import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import Tool, StructuredTool
from pydantic.v1 import BaseModel, Field 
from langchain_core.messages import HumanMessage, AIMessage

# Import custom tools
from airtable_tool import AirtableTool
from openai_analysis_tool import OpenAIDocumentAnalysisTool
from google_calendar_tool import GoogleCalendarTool
from date_utils_tool import DateUtilsTool

# Load environment variables
load_dotenv()

# Get API key from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set. Please set it in your .env file.")

# Initialize custom tools
airtable_handler = AirtableTool()
openai_analyzer = OpenAIDocumentAnalysisTool()
calendar_tool = GoogleCalendarTool()
date_utils = DateUtilsTool()

# --- Define Pydantic models for tool inputs ---
class SearchAnnouncementsInput(BaseModel):
    search_text: str = Field(description="The text to search for in announcement titles or descriptions.")

class GetAttachmentInput(BaseModel):
    announcement_id: str = Field(default=None, description="The ID of a specific announcement to get an attachment from.")
    search_term: str = Field(default=None, description="A search term to find an announcement and get its attachment.")
    get_latest: bool = Field(default=False, description="Set to true to get the attachment from the latest announcement.")

class AnalyzeDocumentInput(BaseModel):
    pdf_path: str = Field(description="The local file path to the PDF document to be analyzed.")
    analysis_type: str = Field(default="summarize", description="Type of analysis: 'summarize', 'extract_action_items', 'sentiment', or 'custom'.")
    custom_prompt: str = Field(default=None, description="A custom prompt for the analysis, used if analysis_type is 'custom' or to override defaults.")
    max_pages_to_analyze: int = Field(default=5, description="Maximum number of pages from the PDF to analyze.")

# New Pydantic models for calendar tools
class SearchEventsInput(BaseModel):
    query: str = Field(default=None, description="Search term to find events.")
    start_date: str = Field(default=None, description="Start date in 'YYYY-MM-DD' format.")
    end_date: str = Field(default=None, description="End date in 'YYYY-MM-DD' format.")
    max_results: int = Field(default=10, description="Maximum number of results to return.")

class CreateEventInput(BaseModel):
    title: str = Field(description="Title of the event.")
    start_datetime: str = Field(description="Start date and time in ISO format (YYYY-MM-DDTHH:MM:SS).")
    end_datetime: str = Field(default=None, description="End date and time in ISO format. If not provided, event will be 1 hour long.")
    description: str = Field(default=None, description="Description of the event.")
    location: str = Field(default=None, description="Location of the event.")
    attendees: list = Field(default=None, description="List of email addresses of attendees.")
    reminder_minutes: int = Field(default=None, description="Reminder time in minutes before the event.")

class CreateReminderInput(BaseModel):
    title: str = Field(description="Title of the reminder.")
    due_date: str = Field(description="Due date and time in ISO format (YYYY-MM-DDTHH:MM:SS).")
    description: str = Field(default=None, description="Description of the reminder.")

class DeleteEventInput(BaseModel):
    event_id: str = Field(description="ID of the event to delete.")

# New Pydantic models for date utils
class GetDateRangeInput(BaseModel):
    period: str = Field(description="Time period ('today', 'yesterday', 'this_week', 'last_week', 'this_month', 'last_month', 'next_month', 'this_year', 'last_year').")

class GetRelativeDateInput(BaseModel):
    reference: str = Field(description="Reference point ('today', 'yesterday', 'start_of_week', 'end_of_week', 'start_of_month', 'end_of_month').")
    offset_days: int = Field(default=0, description="Number of days to offset (can be negative).")

# --- Wrapper functions for LangChain tools with enhanced error handling ---
def get_all_announcements_wrapper():
    """Fetches all announcements. Returns list of announcements or error string."""
    if not airtable_handler.airtable:
        return "Error: Airtable connection is not available."
    return airtable_handler.get_all_announcements()

def search_announcements_wrapper(search_text: str):
    """Searches announcements. Returns list of matching announcements or error string."""
    if not airtable_handler.airtable:
        return "Error: Airtable connection is not available."
    return airtable_handler.search_announcements(search_text)

def get_and_download_attachment_wrapper(announcement_id: str = None, search_term: str = None, get_latest: bool = False):
    """Fetches an announcement attachment URL and downloads the file, returning its local path or an error string."""
    print(f"Attempting to get attachment: id={announcement_id}, search='{search_term}', latest={get_latest}")
    if not airtable_handler.airtable:
        return "Error: Airtable connection is not available for fetching attachment info."

    # get_attachment_from_announcement now returns (url, filename) or (error_string, None)
    result_url, result_filename = airtable_handler.get_attachment_from_announcement(
        announcement_id=announcement_id, 
        search_term=search_term, 
        get_latest=get_latest
    )

    if result_filename is None and isinstance(result_url, str) and result_url.startswith("Error:"):
        return result_url # Return the error message from get_attachment_from_announcement
    
    if result_url and result_filename:
        save_dir = "/tmp/agent_downloads"
        # os.makedirs(save_dir, exist_ok=True) # download_file handles directory creation
        print(f"Attachment URL found: {result_url}. Filename hint: {result_filename}. Downloading to {save_dir}...")
        
        downloaded_path_or_error = airtable_handler.download_file(result_url, save_path=save_dir)
        
        if isinstance(downloaded_path_or_error, str) and (downloaded_path_or_error.startswith("Error:") or not os.path.exists(downloaded_path_or_error)):
            # If download_file returned an error string, or if it returned a path that doesn't exist (should not happen with current download_file logic but good to check)
            print(f"Failed to download: {downloaded_path_or_error}")
            return downloaded_path_or_error # Return the error message from download_file
        elif os.path.exists(downloaded_path_or_error):
            print(f"File downloaded successfully to: {downloaded_path_or_error}")
            return downloaded_path_or_error
        else:
            # Fallback error if path doesn't exist and no error string was returned (unlikely)
            return f"Error: Download reported success but file not found at {downloaded_path_or_error}. Original URL: {result_url}"
    else:
        # This case should ideally be covered by the first check for error string
        return "Error: No attachment found matching the criteria or an unexpected error occurred retrieving attachment info."

def find_announcement_by_title_wrapper(search_text: str):
    """Finds an announcement by its title and returns the record or None."""
    if not airtable_handler.airtable:
        return "Error: Airtable connection is not available."
    
    all_announcements = airtable_handler.get_all_announcements()
    if isinstance(all_announcements, str) and all_announcements.startswith("Error:"):
        return all_announcements
    
    for announcement in all_announcements:
        if announcement.get("Title", "").lower() == search_text.lower():
            return announcement
    
    return f"Error: Could not find an announcement with title '{search_text}'."

def analyze_document_wrapper(pdf_path: str, analysis_type: str = "summarize", custom_prompt: str = None, max_pages_to_analyze: int = 5):
    """Analyzes a PDF document. Returns analysis string or error string."""
    if not openai_analyzer.client:
        return "Error: OpenAI client is not available for document analysis."
    return openai_analyzer.analyze_document_content(pdf_path, analysis_type, custom_prompt, max_pages_to_analyze)

# --- Wrapper functions for Google Calendar tools ---
def search_events_wrapper(query: str = None, start_date: str = None, end_date: str = None, max_results: int = 10):
    """Searches for events in Google Calendar. Returns list of events or error message."""
    return calendar_tool.search_events(query, start_date, end_date, max_results)

def create_event_wrapper(title: str, start_datetime: str, end_datetime: str = None, description: str = None, 
                         location: str = None, attendees: list = None, reminder_minutes: int = None):
    """Creates a new event in Google Calendar. Returns created event or error message."""
    return calendar_tool.create_event(title, start_datetime, end_datetime, description, location, attendees, reminder_minutes)

def create_reminder_wrapper(title: str, due_date: str, description: str = None):
    """Creates a new reminder in Google Calendar. Returns created reminder or error message."""
    return calendar_tool.create_reminder(title, due_date, description)

def delete_event_wrapper(event_id: str):
    """Deletes an event from Google Calendar. Returns result of deletion or error message."""
    return calendar_tool.delete_event(event_id)

# --- Wrapper functions for Date Utils tools ---
def get_current_date_wrapper():
    """Gets the current date. Returns date as string."""
    return date_utils.get_current_date(include_time=True)

def get_date_range_wrapper(period: str):
    """Gets start and end dates for common time periods. Returns dictionary with date range."""
    return date_utils.get_date_range(period)

def get_relative_date_wrapper(reference: str, offset_days: int = 0):
    """Gets a date relative to a reference point with an offset. Returns dictionary with date information."""
    return date_utils.get_relative_date(reference, offset_days)

# --- Create LangChain Tools ---
tools = [
    Tool(
        name="GetAllAnnouncements",
        func=lambda _: get_all_announcements_wrapper(),
        description="Fetches all announcements from Airtable. Use this when the user wants to see all available announcements. Returns a list of announcements or an error message."
    ),
    StructuredTool.from_function(
        func=search_announcements_wrapper,
        name="SearchAnnouncements",
        description="Searches announcements in Airtable by text in their Title or Description fields. Returns a list of matching announcements or an error message.",
        args_schema=SearchAnnouncementsInput
    ),
    StructuredTool.from_function(
        func=get_and_download_attachment_wrapper,
        name="GetAndDownloadAnnouncementAttachment",
        description="Retrieves and downloads an attachment from an announcement. Specify how to find the announcement: by its ID, by a search term, or request the latest. Returns the local path to the downloaded PDF file or an error message.",
        args_schema=GetAttachmentInput
    ),
    StructuredTool.from_function(
        func=find_announcement_by_title_wrapper,
        name="FindAnnouncementByTitle",
        description="Finds an announcement by its exact title. Returns the announcement record or an error message.",
        args_schema=SearchAnnouncementsInput
    ),
    StructuredTool.from_function(
        func=analyze_document_wrapper,
        name="AnalyzeDocumentContent",
        description="Analyzes the content of a downloaded PDF document using OpenAI. Requires the local path to the PDF. Analysis types include summarize, extract_action_items, or sentiment. A custom prompt can also be provided. Returns the analysis or an error message.",
        args_schema=AnalyzeDocumentInput
    ),
    # Google Calendar Tools
    StructuredTool.from_function(
        func=search_events_wrapper,
        name="SearchCalendarEvents",
        description="Searches for events in Google Calendar. You can specify a search term, date range, and maximum number of results to return. Returns a list of events or an error message.",
        args_schema=SearchEventsInput
    ),
    StructuredTool.from_function(
        func=create_event_wrapper,
        name="CreateCalendarEvent",
        description="Creates a new event in Google Calendar. You must specify the title and start time. Optionally specify end time, description, location, attendees, and reminder time. Returns the created event or an error message.",
        args_schema=CreateEventInput
    ),
    StructuredTool.from_function(
        func=create_reminder_wrapper,
        name="CreateCalendarReminder",
        description="Creates a new reminder in Google Calendar. You must specify the title and due date. Optionally specify a description. Returns the created reminder or an error message.",
        args_schema=CreateReminderInput
    ),
    StructuredTool.from_function(
        func=delete_event_wrapper,
        name="DeleteCalendarEvent",
        description="Deletes an event from Google Calendar. You must specify the event ID. Returns the result of the deletion or an error message.",
        args_schema=DeleteEventInput
    ),
    # Date Utils Tools
    Tool(
        name="GetCurrentDate",
        func=lambda _: get_current_date_wrapper(),
        description="Gets the current date and time in ISO format. Useful when you need the current date for creating events or searching date ranges."
    ),
    StructuredTool.from_function(
        func=get_date_range_wrapper,
        name="GetDateRange",
        description="Gets start and end dates for common time periods like 'today', 'this_week', 'last_month', etc. Useful for searching events within specific date ranges. Returns a dictionary with formatted date strings.",
        args_schema=GetDateRangeInput
    ),
    StructuredTool.from_function(
        func=get_relative_date_wrapper,
        name="GetRelativeDate",
        description="Gets a date relative to a reference point with an offset in days. For example, 'tomorrow' would be ('today', 1) and 'last Monday' might be ('start_of_week', -7). Returns a dictionary with date information.",
        args_schema=GetRelativeDateInput
    )
]

# --- Initialize LLM and Agent ---
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=OPENAI_API_KEY)

MEMORY_KEY = "chat_history"
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant that can interact with Airtable, analyze documents, manage Google Calendar, and perform date calculations. You have access to tools for these tasks. If a tool returns an error, inform the user clearly about the error. When a user asks about an attachment after mentioning a specific announcement, use the FindAnnouncementByTitle tool first to get details about that announcement, then use GetAndDownloadAnnouncementAttachment with the search_term parameter set to the announcement title. For calendar-related tasks, help users create, find, and manage their events and reminders effectively. You can also provide date calculations and ranges when users need to know about specific time periods. Always maintain context between conversation turns."),
    MessagesPlaceholder(variable_name=MEMORY_KEY),
    ("user", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent = create_openai_functions_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

# --- Main execution block for testing ---
if __name__ == "__main__":
    print("Agent initialized. Testing with example queries...")
    
    # Use the same chat history mechanism as in main.py for consistency
    # This is a list of tuples: [("user", "query1"), ("assistant", "response1")]
    raw_chat_history = [] 

    queries = [
        "Show all announcements",
        "Search for announcements about Q99 NonExistent", # Test search with no results
        "Get the attachment for announcement ID recNONEXISTENT", # Test get attachment with bad ID
        "Summarize the latest announcement attachment", # This might fail if no attachments or if Airtable is empty
        "Analyze the document at /tmp/non_existent_document.pdf", # Test analysis with bad path
        "Search for announcements about Q2 results", # Assuming Q2 might exist from previous tests
        "What's the date range for this month?", # Test date utils
        "Create a calendar event for tomorrow at 2pm", # Test calendar integration
        # "Find an announcement with the word 'important' and tell me what its attachment says about action items" # More complex query
    ]

    for query in queries:
        print(f"\n--- User Query: {query} ---")
        try:
            # Convert raw_chat_history to Langchain's expected format
            langchain_chat_history_messages = []
            for utype, message in raw_chat_history:
                if utype == "user":
                    langchain_chat_history_messages.append(HumanMessage(content=message))
                elif utype == "assistant":
                    langchain_chat_history_messages.append(AIMessage(content=message))
            
            result = agent_executor.invoke({"input": query, MEMORY_KEY: langchain_chat_history_messages})
            output = result.get("output", "Error: No output from agent.")
            print(f"--- Agent Output: ---")
            print(output)
            raw_chat_history.append(("user", query))
            raw_chat_history.append(("assistant", output))
        except Exception as e:
            error_output = f"Critical Error processing query '{query}': {e}"
            print(f"--- Agent Output (Critical Error): ---")
            print(error_output)
            raw_chat_history.append(("user", query))
            raw_chat_history.append(("assistant", error_output))


