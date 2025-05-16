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

# Load environment variables
load_dotenv()

# Get API key from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set. Please set it in your .env file.")

# Initialize custom tools
airtable_handler = AirtableTool()
openai_analyzer = OpenAIDocumentAnalysisTool()

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

def find_announcement_by_title_wrapper(title: str):
    """Finds an announcement by its title and returns the record or None."""
    if not airtable_handler.airtable:
        return "Error: Airtable connection is not available."
    
    all_announcements = airtable_handler.get_all_announcements()
    if isinstance(all_announcements, str) and all_announcements.startswith("Error:"):
        return all_announcements
    
    for announcement in all_announcements:
        if announcement.get("Title", "").lower() == title.lower():
            return announcement
    
    return f"Error: Could not find an announcement with title '{title}'."

def analyze_document_wrapper(pdf_path: str, analysis_type: str = "summarize", custom_prompt: str = None, max_pages_to_analyze: int = 5):
    """Analyzes a PDF document. Returns analysis string or error string."""
    if not openai_analyzer.client:
        return "Error: OpenAI client is not available for document analysis."
    return openai_analyzer.analyze_document_content(pdf_path, analysis_type, custom_prompt, max_pages_to_analyze)

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
    )
]

# --- Initialize LLM and Agent ---
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=OPENAI_API_KEY)

MEMORY_KEY = "chat_history"
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant that can interact with Airtable and analyze documents. You have access to tools for these tasks. If a tool returns an error, inform the user clearly about the error. When a user asks about an attachment after mentioning a specific announcement, use the FindAnnouncementByTitle tool first to get details about that announcement, then use GetAndDownloadAnnouncementAttachment with the search_term parameter set to the announcement title. Always maintain context between conversation turns."),
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

    # Example of a potentially successful multi-turn conversation
    print("\n--- Multi-turn test (potential success) ---")
    # Assuming 'sample_test.pdf' was created by openai_analysis_tool.py's __main__ and an announcement links to it.
    # This is hard to test without a populated Airtable base that the agent can interact with live.
    # For now, let's simulate a successful download then analysis.

    # Step 1: Try to get a known attachment (if any were successfully added and downloadable)
    # This requires a known good state in Airtable, which is hard to guarantee in a script.
    # We will assume the user might ask to summarize a file they know was downloaded.

    # Let's first try to download the 'latest' attachment and see if it works.
    query1 = "Can you download the attachment from the latest announcement?"
    print(f"User: {query1}")
    langchain_hist_q1 = [HumanMessage(content=h[1]) if h[0]=='user' else AIMessage(content=h[1]) for h in raw_chat_history]
    result1 = agent_executor.invoke({"input": query1, MEMORY_KEY: langchain_hist_q1})
    output1 = result1.get('output', "Error: No output from agent.")
    print(f"Agent: {output1}")
    raw_chat_history.append(("user", query1))
    raw_chat_history.append(("assistant", output1))

    pdf_path_from_output = None
    if "Error:" not in output1 and "downloaded successfully to:" in output1.lower():
        try:
            # Extract path carefully
            path_part = output1.split("downloaded successfully to:")[-1].strip()
            # Further clean if there's trailing text, e.g. periods or agent's own commentary
            pdf_path_from_output = path_part.split()[0] # Take the first word after the phrase
            if not os.path.exists(pdf_path_from_output):
                 print(f"Warning: Agent reported download to {pdf_path_from_output}, but file not found. Path extraction might be imperfect or download failed silently.")
                 pdf_path_from_output = None # Reset if not found
            else:
                print(f"Successfully extracted path: {pdf_path_from_output}")
        except Exception as e:
            print(f"Could not reliably extract PDF path from agent output: {e}")
    
    if pdf_path_from_output:
        query2 = f"Great, now please summarize the document you just downloaded at {pdf_path_from_output}"
        print(f"User: {query2}")
        langchain_hist_q2 = [HumanMessage(content=h[1]) if h[0]=='user' else AIMessage(content=h[1]) for h in raw_chat_history]
        result2 = agent_executor.invoke({"input": query2, MEMORY_KEY: langchain_hist_q2})
        output2 = result2.get('output', "Error: No output from agent.")
        print(f"Agent: {output2}")
        raw_chat_history.append(("user", query2))
        raw_chat_history.append(("assistant", output2))
    else:
        print("Skipping follow-up analysis as previous download step might have failed, found no attachment, or path extraction failed.")


