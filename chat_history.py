from typing import Dict, List, Tuple
from langchain_core.messages import HumanMessage, AIMessage

class ChatHistoryManager:
    def __init__(self):
        # Dictionary to store chat history by session_id
        self._history: Dict[str, List[Tuple[str, str]]] = {}
    
    def add_message(self, session_id: str, role: str, content: str) -> None:
        """Add a message to the chat history for a specific session"""
        if session_id not in self._history:
            self._history[session_id] = []
        
        self._history[session_id].append((role, content))
    
    def get_history(self, session_id: str) -> List[Tuple[str, str]]:
        """Get the raw chat history for a specific session"""
        return self._history.get(session_id, [])
    
    def get_langchain_history(self, session_id: str) -> List:
        """Get the chat history formatted for LangChain"""
        raw_history = self.get_history(session_id)
        langchain_history = []
        
        for role, content in raw_history:
            if role == "user":
                langchain_history.append(HumanMessage(content=content))
            elif role == "assistant":
                langchain_history.append(AIMessage(content=content))
        
        return langchain_history
    
    def clear_history(self, session_id: str) -> None:
        """Clear the chat history for a specific session"""
        if session_id in self._history:
            del self._history[session_id]

# Create a singleton instance
chat_history_manager = ChatHistoryManager() 