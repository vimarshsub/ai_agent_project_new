import requests
import json
from datetime import datetime, timedelta

class GoogleCalendarTool:
    def __init__(self):
        # API endpoints
        self.get_url = "https://agentichome.app.n8n.cloud/webhook/3c4e4c24-635b-4776-aec6-afb141cfab5c"
        self.post_url = "https://agentichome.app.n8n.cloud/webhook/615f7ae5-4d59-4555-aa7c-228feef7d013"
        
    def search_events(self, query=None, start_date=None, end_date=None, max_results=10):
        """
        Search for events in Google Calendar.
        
        Args:
            query (str, optional): Search term to find events
            start_date (str, optional): Start date in 'YYYY-MM-DD' format
            end_date (str, optional): End date in 'YYYY-MM-DD' format
            max_results (int, optional): Maximum number of results to return
            
        Returns:
            dict: Dictionary containing the search results or error message
        """
        try:
            # Prepare request data
            params = {
                "action": "search_events",
                "max_results": max_results
            }
            
            if query:
                params["query"] = query
            
            if start_date:
                params["start_date"] = start_date
                
            if end_date:
                params["end_date"] = end_date
            
            # Send GET request
            response = requests.get(self.get_url, params=params)
            
            # Check if request was successful
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "error": f"Failed to search events. Status code: {response.status_code}",
                    "message": response.text
                }
                
        except Exception as e:
            return {
                "error": "Failed to search events",
                "message": str(e)
            }
    
    def create_event(self, title, start_datetime, end_datetime=None, description=None, location=None, attendees=None, reminder_minutes=None):
        """
        Create a new event in Google Calendar.
        
        Args:
            title (str): Title of the event
            start_datetime (str): Start date and time in ISO format (YYYY-MM-DDTHH:MM:SS)
            end_datetime (str, optional): End date and time in ISO format
            description (str, optional): Description of the event
            location (str, optional): Location of the event
            attendees (list, optional): List of email addresses of attendees
            reminder_minutes (int, optional): Reminder time in minutes before the event
            
        Returns:
            dict: Dictionary containing the created event or error message
        """
        try:
            # Set end time to 1 hour after start time if not provided
            if not end_datetime:
                start_dt = datetime.fromisoformat(start_datetime.replace('Z', '+00:00'))
                end_dt = start_dt + timedelta(hours=1)
                end_datetime = end_dt.isoformat().replace('+00:00', 'Z')
            
            # Prepare request data
            data = {
                "action": "create_event",
                "title": title,
                "start_datetime": start_datetime,
                "end_datetime": end_datetime
            }
            
            if description:
                data["description"] = description
                
            if location:
                data["location"] = location
                
            if attendees:
                data["attendees"] = attendees
                
            if reminder_minutes:
                data["reminder_minutes"] = reminder_minutes
            
            # Send POST request
            headers = {"Content-Type": "application/json"}
            response = requests.post(self.post_url, json=data, headers=headers)
            
            # Check if request was successful
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "error": f"Failed to create event. Status code: {response.status_code}",
                    "message": response.text
                }
                
        except Exception as e:
            return {
                "error": "Failed to create event",
                "message": str(e)
            }
    
    def create_reminder(self, title, due_date, description=None):
        """
        Create a new reminder in Google Calendar.
        
        Args:
            title (str): Title of the reminder
            due_date (str): Due date and time in ISO format (YYYY-MM-DDTHH:MM:SS)
            description (str, optional): Description of the reminder
            
        Returns:
            dict: Dictionary containing the created reminder or error message
        """
        try:
            # Prepare request data
            data = {
                "action": "create_reminder",
                "title": title,
                "due_date": due_date
            }
            
            if description:
                data["description"] = description
            
            # Send POST request
            headers = {"Content-Type": "application/json"}
            response = requests.post(self.post_url, json=data, headers=headers)
            
            # Check if request was successful
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "error": f"Failed to create reminder. Status code: {response.status_code}",
                    "message": response.text
                }
                
        except Exception as e:
            return {
                "error": "Failed to create reminder",
                "message": str(e)
            }

    def delete_event(self, event_id):
        """
        Delete an event from Google Calendar.
        
        Args:
            event_id (str): ID of the event to delete
            
        Returns:
            dict: Dictionary containing the result of the deletion or error message
        """
        try:
            # Prepare request data
            data = {
                "action": "delete_event",
                "event_id": event_id
            }
            
            # Send POST request
            headers = {"Content-Type": "application/json"}
            response = requests.post(self.post_url, json=data, headers=headers)
            
            # Check if request was successful
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "error": f"Failed to delete event. Status code: {response.status_code}",
                    "message": response.text
                }
                
        except Exception as e:
            return {
                "error": "Failed to delete event",
                "message": str(e)
            }

# Example usage
if __name__ == "__main__":
    calendar_tool = GoogleCalendarTool()
    
    # Example: Search for events
    print("Searching for events...")
    search_results = calendar_tool.search_events(query="Meeting", max_results=5)
    print(json.dumps(search_results, indent=2))
    
    # Example: Create an event
    print("\nCreating a new event...")
    tomorrow = (datetime.now() + timedelta(days=1)).replace(hour=10, minute=0, second=0).isoformat() + 'Z'
    tomorrow_end = (datetime.now() + timedelta(days=1)).replace(hour=11, minute=0, second=0).isoformat() + 'Z'
    
    event_result = calendar_tool.create_event(
        title="Team Meeting",
        start_datetime=tomorrow,
        end_datetime=tomorrow_end,
        description="Discuss project progress",
        location="Conference Room A",
        attendees=["example@email.com"],
        reminder_minutes=30
    )
    print(json.dumps(event_result, indent=2)) 