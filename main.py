
from agent_logic import agent_executor, MEMORY_KEY
from langchain_core.messages import HumanMessage, AIMessage

def run_chat_interface():
    """Runs a command-line chat interface for the AI agent."""
    print("AI Agent Chat Interface Initialized.")
    print("Type your queries to interact with the agent. Type 'quit' or 'exit' to end.")
    
    chat_history = []

    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ["quit", "exit"]:
            print("Exiting chat interface. Goodbye!")
            break

        if not user_input.strip():
            continue

        print("Agent is thinking...")
        try:
            # Prepare chat history for the agent
            # The agent_executor.invoke expects chat_history in a specific format if MessagesPlaceholder is used
            # For create_openai_functions_agent, it expects a list of BaseMessage objects (HumanMessage, AIMessage)
            
            langchain_chat_history = []
            for utype, message in chat_history:
                if utype == "user":
                    langchain_chat_history.append(HumanMessage(content=message))
                elif utype == "assistant":
                    langchain_chat_history.append(AIMessage(content=message))

            result = agent_executor.invoke({
                "input": user_input,
                MEMORY_KEY: langchain_chat_history # Pass the formatted chat history
            })
            
            agent_response = result.get("output", "Sorry, I didn't get a clear response.")
            print(f"Agent: {agent_response}")

            # Update chat history with the current interaction
            chat_history.append(("user", user_input))
            chat_history.append(("assistant", agent_response))

        except Exception as e:
            error_message = f"An error occurred: {e}"
            print(f"Agent: {error_message}")
            # Optionally, add error to history or handle differently
            chat_history.append(("user", user_input))
            chat_history.append(("assistant", error_message))

if __name__ == "__main__":
    run_chat_interface()


