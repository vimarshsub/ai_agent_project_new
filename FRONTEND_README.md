# AI Agent Frontend Integration Guide

This guide explains how to connect your frontend application to the AI Agent server and effectively manage conversation sessions.

## API Endpoints

The server provides the following RESTful endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat` | POST | Send a message to the AI agent |
| `/api/chat/{session_id}` | DELETE | Clear conversation history for a specific session |
| `/health` | GET | Check server health status |

## Session Management

The server handles conversation history using session IDs:

1. On first request, server generates a new session ID
2. Client should store and reuse this session ID for continued conversations
3. Session ID is passed via the `X-Session-ID` HTTP header
4. To start a new conversation, omit the session ID or use a different one

## API Response Format

The `/api/chat` endpoint returns responses in the following JSON format:

```json
{
  "session_id": "uuid-string-here",
  "response": "The agent's response text",
  "additional_data": null
}
```

- `session_id`: Unique identifier for the conversation session
- `response`: The AI agent's text response to the user's message
- `additional_data`: Optional field that may contain additional structured data (currently null)

## Making Requests

### Basic Chat Request

```javascript
async function sendMessage(message) {
  try {
    const response = await fetch('http://localhost:8000/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ message })
    });
    
    const result = await response.json();
    
    // Store the session ID for future requests
    const sessionId = result.session_id;
    
    // Display the agent's response
    console.log(result.response);
    
    return { sessionId, response: result.response };
  } catch (error) {
    console.error('Error sending message:', error);
  }
}
```

### Continuing a Conversation

```javascript
async function continueConversation(message, sessionId) {
  try {
    const response = await fetch('http://localhost:8000/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Session-ID': sessionId
      },
      body: JSON.stringify({ message })
    });
    
    const result = await response.json();
    
    // Display the agent's response
    console.log(result.response);
    
    return { sessionId: result.session_id, response: result.response };
  } catch (error) {
    console.error('Error sending message:', error);
  }
}
```

### Clearing Conversation History

```javascript
async function clearConversation(sessionId) {
  try {
    const response = await fetch(`http://localhost:8000/api/chat/${sessionId}`, {
      method: 'DELETE'
    });
    
    const result = await response.json();
    console.log(result.message);
    
    return result;
  } catch (error) {
    console.error('Error clearing conversation:', error);
  }
}
```

## Complete React Example

Here's a simple React component that integrates with the AI Agent:

```jsx
import { useState, useEffect } from 'react';

function ChatInterface() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [loading, setLoading] = useState(false);

  // Send a message to the AI agent
  const handleSendMessage = async () => {
    if (!input.trim()) return;
    
    // Add user message to the UI
    const userMessage = { sender: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);
    
    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(sessionId && { 'X-Session-ID': sessionId })
        },
        body: JSON.stringify({ message: input })
      });
      
      const result = await response.json();
      
      // Store the session ID
      setSessionId(result.session_id);
      
      // Add agent response to the UI
      setMessages(prev => [...prev, { 
        sender: 'agent', 
        content: result.response 
      }]);
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => [...prev, { 
        sender: 'error', 
        content: 'Failed to communicate with the agent.' 
      }]);
    } finally {
      setLoading(false);
    }
  };

  // Clear conversation history
  const handleClearConversation = async () => {
    if (!sessionId) return;
    
    try {
      await fetch(`http://localhost:8000/api/chat/${sessionId}`, {
        method: 'DELETE'
      });
      
      setMessages([]);
      setSessionId(null);
    } catch (error) {
      console.error('Error clearing conversation:', error);
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-messages">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.sender}`}>
            {msg.content}
          </div>
        ))}
        {loading && <div className="loading">Agent is thinking...</div>}
      </div>
      
      <div className="chat-input">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
          placeholder="Type your message..."
          disabled={loading}
        />
        <button onClick={handleSendMessage} disabled={loading}>
          Send
        </button>
        <button onClick={handleClearConversation}>
          Clear Conversation
        </button>
      </div>
      
      {sessionId && (
        <div className="session-info">
          Session ID: {sessionId}
        </div>
      )}
    </div>
  );
}

export default ChatInterface;
```

## Best Practices

1. **Persist the Session ID**: Store the session ID in localStorage or cookies to maintain conversations across page refreshes.

   ```javascript
   // Example of persisting session ID in localStorage
   
   // Save session ID
   function saveSessionId(sessionId) {
     localStorage.setItem('aiAgentSessionId', sessionId);
   }
   
   // Retrieve session ID
   function getSessionId() {
     return localStorage.getItem('aiAgentSessionId');
   }
   
   // Usage in a React component
   const [sessionId, setSessionId] = useState(() => {
     // Try to get existing session ID on component mount
     return getSessionId() || null;
   });
   
   // When you receive a session ID from the server
   const handleResponse = (result) => {
     // Update state
     setSessionId(result.session_id);
     
     // Persist to localStorage
     saveSessionId(result.session_id);
   };
   ```

2. **Error Handling**: Implement robust error handling for network issues or server problems.

3. **Loading States**: Show loading indicators while waiting for responses.

4. **Session Timeout**: Consider implementing session timeout logic to start fresh conversations after periods of inactivity.

5. **Message History**: Cache message history on the client side for immediate display, even though the server maintains the conversation context.

## Common Issues

- **CORS Issues**: If encountering CORS errors, ensure your frontend application's domain is allowed in the server's CORS configuration.

- **Network Problems**: Implement retry logic for failed requests due to network issues.

- **Large Responses**: Be prepared to handle potentially large responses from the AI agent, especially for complex queries.

- **Rate Limiting**: Implement client-side throttling to prevent overwhelming the server with too many requests.

## Testing with cURL

You can test the API directly using cURL before implementing in your frontend:

### Send Initial Message

```bash
curl -X POST \
  http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, how can you help me today?"}'
```

### Continue Conversation with Session ID

```bash
# Replace your-session-id-here with the session_id from the previous response
curl -X POST \
  http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: your-session-id-here" \
  -d '{"message": "Tell me more about that"}'
```

### Clear Conversation History

```bash
# Replace your-session-id-here with the session_id you want to clear
curl -X DELETE \
  http://localhost:8000/api/chat/your-session-id-here
```

### Check Server Health

```bash
curl http://localhost:8000/health
``` 