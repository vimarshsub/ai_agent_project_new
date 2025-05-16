# AI Agent for Airtable and OpenAI Document Analysis

## 1. Project Overview

This project implements a conversational AI agent capable of interacting with an Airtable base to manage announcements and analyzing PDF document attachments using OpenAI's GPT-4o vision capabilities. The agent can fetch all announcements, search for specific announcements, retrieve attachments, convert PDF attachments to images, and then perform analysis tasks like summarization, action item extraction, and sentiment analysis on the document content.

## 2. Project Structure

The project is organized into the following key Python files within the `/home/ubuntu/ai_agent_project/` directory:

-   `main.py`: This script provides a command-line chat interface to interact with the AI agent. It handles user input and displays the agent's responses.
-   `agent_logic.py`: This file contains the core logic for the LangChain agent. It defines the tools, initializes the language model (LLM), sets up the agent executor, and manages the conversational flow and tool routing.
-   `airtable_tool.py`: This module implements the `AirtableTool` class, which provides functionalities to connect to an Airtable base, fetch all records, search records based on text, retrieve attachment URLs, and download attachments.
-   `openai_analysis_tool.py`: This module contains the `OpenAIDocumentAnalysisTool` class. It is responsible for converting PDF document pages into images (base64 encoded) and then using the OpenAI API (GPT-4o) to analyze the content of these images based on specified analysis types (e.g., summarize, extract action items, sentiment).
-   `venv/`: This directory contains the Python virtual environment with all the necessary dependencies.

## 3. Setup Instructions

### 3.1. Prerequisites

-   Python 3.11
-   `poppler-utils`: This system dependency is required by the `pdf2image` library for PDF processing. It was installed during the environment setup. If running elsewhere, ensure it's installed (e.g., `sudo apt-get install poppler-utils` on Debian/Ubuntu).

### 3.2. Environment Setup

1.  **Navigate to the project directory**:
    ```bash
    cd /home/ubuntu/ai_agent_project
    ```

2.  **Activate the virtual environment**:
    The virtual environment `venv` should already be set up in the project directory. To activate it:
    ```bash
    source venv/bin/activate
    ```

3.  **Install Dependencies**:
    All required Python packages are listed in `requirements.txt` (which will be created in the next step). If setting up manually or if `requirements.txt` is not used, the core packages were installed during the initial setup. You can ensure they are present by running:
    ```bash
    pip install langchain langchain-openai airtable-python-wrapper requests Pillow pdf2image openai fpdf2 python-dotenv
    ```

### 3.3. API Keys

As per your request, the following API keys have been **hardcoded** directly into the respective Python files:

-   **Airtable API Key, Base ID, and Table Name**: Located at the beginning of `airtable_tool.py`.
    -   `AIRTABLE_API_KEY`
    -   `AIRTABLE_BASE_ID`
    -   `AIRTABLE_TABLE_NAME` (set to "Announcements")
-   **OpenAI API Key**: Located at the beginning of `openai_analysis_tool.py` and also set as an environment variable within `agent_logic.py` for LangChain's `ChatOpenAI`.
    -   `OPENAI_API_KEY`

**Security Note**: While hardcoding keys was done as requested for this development context, for production environments or shared code, it is strongly recommended to use environment variables (e.g., via a `.env` file and the `python-dotenv` library, or system environment variables) to manage sensitive credentials. This prevents accidental exposure.

## 4. Running the Agent

To start interacting with the AI agent:

1.  Ensure you are in the project directory (`/home/ubuntu/ai_agent_project/`).
2.  Ensure the virtual environment is activated (`source venv/bin/activate`).
3.  Run the `main.py` script:
    ```bash
    python main.py
    ```
This will launch the command-line chat interface. You can then type your queries, such as:
-   "Show all announcements"
-   "Search announcements for Q2 report"
-   "Summarize the latest announcement attachment"
-   "What are the action items in the attachment of the announcement titled 'Project Phoenix Update'?"

Type `quit` or `exit` to terminate the chat interface.

## 5. Functionality Details

### 5.1. Chat Interface (`main.py`)
-   Accepts user queries via the command line.
-   Maintains a chat history for conversational context.
-   Passes queries and history to the `agent_executor` from `agent_logic.py`.
-   Displays the agent's final response or any errors encountered.

### 5.2. Airtable Tool (`airtable_tool.py`)
-   **Connects to Airtable**: Uses the hardcoded API Key, Base ID (`appLu7BlsSJ0MzwXt`), and Table Name (`Announcements`).
-   **Fetch All Announcements**: Retrieves all records from the specified table.
-   **Search Announcements**: Filters announcements based on a search term in the `Title` or `Description` fields (case-insensitive local filtering after fetching all records).
-   **Get Attachment**: 
    -   Can find an announcement by its ID, a search term, or by requesting the latest (based on `SentTime` field, assuming it exists and is sortable).
    -   Retrieves the URL and filename of the *first* attachment found in the `Attachments` field of the target announcement.
    -   Downloads the attachment to a local directory (`/tmp/agent_downloads/`).
-   **Airtable Columns**: The tool expects your "Announcements" table to have at least the following columns for full functionality:
    -   `Title` (Text)
    -   `Description` (Text)
    -   `Attachments` (Attachment type, for PDF files)
    -   `SentTime` (Date/Time, used for 'latest' functionality)
    -   `AnnouncementId` (Formula or Auto-number, if you want to refer to it directly, though the tool primarily uses Airtable's internal record IDs)
    -   `DocumentsCount` (Number, this was mentioned but not directly used by the current tool logic, but good to be aware of).

### 5.3. OpenAI Document Analysis Tool (`openai_analysis_tool.py`)
-   **PDF to Image Conversion**: 
    -   Takes a local PDF file path as input.
    -   Uses `pdf2image` (which relies on `poppler-utils`) to convert each page of the PDF (up to a specified maximum, default 5 pages) into a PNG image.
    -   Encodes these images into base64 strings.
-   **OpenAI Analysis (GPT-4o)**:
    -   Sends the base64 encoded images along with a text prompt to the OpenAI GPT-4o model.
    -   Supports analysis types:
        -   `summarize`: Provides a summary of the document content.
        -   `extract_action_items`: Identifies action items, deadlines, and responsible parties.
        -   `sentiment`: Analyzes the overall sentiment of the document.
        -   `custom`: Allows for a user-defined prompt for analysis.
    -   Returns the textual analysis from OpenAI.

### 5.4. Agent Logic (`agent_logic.py`)
-   **LangChain Framework**: Utilizes LangChain for agent creation and tool management.
-   **Tool Definition**: Wraps the functionalities of `AirtableTool` and `OpenAIDocumentAnalysisTool` into LangChain `Tool` or `StructuredTool` objects, making them available to the agent.
-   **LLM**: Uses `ChatOpenAI` with the `gpt-4o` model.
-   **Prompt Engineering**: Employs a system prompt and message placeholders to guide the agent's behavior and maintain conversational history.
-   **Agent Executor**: Manages the interaction between the user input, the LLM, and the available tools. It decides which tool to use (if any) based on the user's intent.
-   **Error Handling**: The tools and agent logic include error handling to manage issues like failed API calls, missing files, or incorrect inputs, and aim to provide informative messages to the user.

## 6. Key Dependencies

-   `langchain`: Framework for building LLM applications.
-   `langchain-openai`: OpenAI integration for LangChain.
-   `airtable-python-wrapper`: For interacting with the Airtable API.
-   `openai`: Official OpenAI Python client library.
-   `requests`: For making HTTP requests (used by Airtable tool for downloads).
-   `Pillow`: Python Imaging Library, used by `pdf2image`.
-   `pdf2image`: For converting PDF files to images.
-   `fpdf2`: Used in test scripts to generate sample PDF files.
-   `python-dotenv`: Used in test scripts (though not for loading main app keys as they are hardcoded).

## 7. Testing

-   The `openai_analysis_tool.py` script contains a `if __name__ == "__main__":` block that tests PDF conversion and analysis. It creates a `sample_test.pdf` if one doesn't exist.
-   The `agent_logic.py` script also contains a `if __name__ == "__main__":` block with various test queries to check the agent's responses to different scenarios, including error conditions.

This documentation should provide a good starting point for understanding and using the AI agent. Let me know if you have further questions after reviewing the code and this guide.

