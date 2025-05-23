from datetime import datetime, timedelta
import calendar
from typing import Dict, Any, Tuple, Optional

class DateUtilsTool:
    """
    Utility class for common date operations used throughout the application.
    Provides methods for getting current date, last week, last month, next month,
    this month, and other useful date ranges.
    """
    
    def __init__(self):
        # Standard date format for ISO strings
        self.iso_format = "%Y-%m-%dT%H:%M:%SZ"
        # Standard date format for display
        self.display_format = "%Y-%m-%d"
    
    def get_current_date(self, as_string: bool = True, include_time: bool = False) -> Any:
        """
        Get the current date.
        
        Args:
            as_string (bool): Return date as string if True, datetime object if False
            include_time (bool): Include time in string output if True
            
        Returns:
            str or datetime: Current date as string or datetime object
        """
        now = datetime.now()
        if as_string:
            if include_time:
                return now.strftime(self.iso_format)
            return now.strftime(self.display_format)
        return now
    
    def get_date_range(self, period: str, as_string: bool = True) -> Dict[str, Any]:
        """
        Get start and end dates for common time periods.
        
        Args:
            period (str): Time period ('today', 'yesterday', 'this_week', 'last_week', 
                         'this_month', 'last_month', 'next_month', 'this_year', 'last_year')
            as_string (bool): Return dates as strings if True, datetime objects if False
            
        Returns:
            dict: Dictionary containing start_date and end_date
        """
        now = datetime.now()
        
        if period == "today":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        elif period == "yesterday":
            yesterday = now - timedelta(days=1)
            start_date = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        elif period == "this_week":
            # Get the start of the week (Monday)
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            # End of the week (Sunday)
            end_date = start_date + timedelta(days=6)
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        elif period == "last_week":
            # Start of last week (Monday)
            start_date = now - timedelta(days=now.weekday() + 7)
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            # End of last week (Sunday)
            end_date = start_date + timedelta(days=6)
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        elif period == "this_month":
            # Start of this month
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # End of this month
            last_day = calendar.monthrange(now.year, now.month)[1]
            end_date = now.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)
        
        elif period == "last_month":
            # First day of the current month
            first_day_current_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # Last day of previous month
            last_day_prev_month = first_day_current_month - timedelta(days=1)
            # First day of previous month
            start_date = last_day_prev_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = last_day_prev_month.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        elif period == "next_month":
            # First day of the current month
            first_day_current_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # First day of next month
            if now.month == 12:
                start_date = first_day_current_month.replace(year=now.year + 1, month=1)
            else:
                start_date = first_day_current_month.replace(month=now.month + 1)
            # Last day of next month
            last_day = calendar.monthrange(start_date.year, start_date.month)[1]
            end_date = start_date.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)
        
        elif period == "this_year":
            # Start of this year
            start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            # End of this year
            end_date = now.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
        
        elif period == "last_year":
            # Start of last year
            start_date = now.replace(year=now.year - 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            # End of last year
            end_date = now.replace(year=now.year - 1, month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
        
        else:
            # Default to today if invalid period
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        if as_string:
            return {
                "start_date": start_date.strftime(self.display_format),
                "end_date": end_date.strftime(self.display_format),
                "iso_start_date": start_date.strftime(self.iso_format),
                "iso_end_date": end_date.strftime(self.iso_format)
            }
        else:
            return {
                "start_date": start_date,
                "end_date": end_date
            }
    
    def format_date_for_display(self, date_obj: datetime) -> str:
        """
        Format a datetime object for display.
        
        Args:
            date_obj (datetime): Datetime object to format
            
        Returns:
            str: Formatted date string
        """
        return date_obj.strftime(self.display_format)
    
    def format_date_for_api(self, date_obj: datetime) -> str:
        """
        Format a datetime object for API use (ISO format).
        
        Args:
            date_obj (datetime): Datetime object to format
            
        Returns:
            str: Formatted date string in ISO format
        """
        return date_obj.strftime(self.iso_format)
    
    def parse_date_string(self, date_string: str, include_time: bool = False) -> Optional[datetime]:
        """
        Parse a date string into a datetime object.
        
        Args:
            date_string (str): Date string to parse
            include_time (bool): Whether the string includes time information
            
        Returns:
            datetime or None: Parsed datetime object or None if failed
        """
        try:
            if include_time:
                return datetime.strptime(date_string, self.iso_format)
            return datetime.strptime(date_string, self.display_format)
        except ValueError:
            # Try different common formats if the standard format doesn't work
            formats = [
                "%Y-%m-%d",
                "%Y/%m/%d",
                "%m/%d/%Y",
                "%d/%m/%Y",
                "%b %d, %Y",
                "%d %b %Y",
                "%B %d, %Y",
                "%d %B %Y"
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_string, fmt)
                except ValueError:
                    continue
            
            return None
    
    def add_days_to_date(self, date_obj: datetime, days: int) -> datetime:
        """
        Add days to a date.
        
        Args:
            date_obj (datetime): Base datetime object
            days (int): Number of days to add (can be negative)
            
        Returns:
            datetime: New datetime object
        """
        return date_obj + timedelta(days=days)
    
    def date_to_string(self, date_obj: datetime, include_time: bool = False) -> str:
        """
        Convert a datetime object to a string.
        
        Args:
            date_obj (datetime): Datetime object to convert
            include_time (bool): Include time in output string
            
        Returns:
            str: Formatted date string
        """
        if include_time:
            return date_obj.strftime(self.iso_format)
        return date_obj.strftime(self.display_format)
    
    def get_relative_date(self, reference: str = "today", offset_days: int = 0) -> Dict[str, Any]:
        """
        Get a date relative to a reference point with an offset.
        
        Args:
            reference (str): Reference point ('today', 'yesterday', 'start_of_week', etc.)
            offset_days (int): Number of days to offset (can be negative)
            
        Returns:
            dict: Dictionary containing date information
        """
        # Get the reference date
        now = datetime.now()
        
        if reference == "today":
            ref_date = now
        elif reference == "yesterday":
            ref_date = now - timedelta(days=1)
        elif reference == "start_of_week":
            # Start of the week (Monday)
            ref_date = now - timedelta(days=now.weekday())
        elif reference == "end_of_week":
            # End of the week (Sunday)
            ref_date = now + timedelta(days=6-now.weekday())
        elif reference == "start_of_month":
            # Start of the month
            ref_date = now.replace(day=1)
        elif reference == "end_of_month":
            # End of the month
            last_day = calendar.monthrange(now.year, now.month)[1]
            ref_date = now.replace(day=last_day)
        else:
            # Default to today
            ref_date = now
        
        # Apply offset
        result_date = ref_date + timedelta(days=offset_days)
        
        # Format date for response
        return {
            "date": self.date_to_string(result_date),
            "iso_date": self.date_to_string(result_date, include_time=True),
            "day_of_week": result_date.strftime("%A"),
            "month": result_date.strftime("%B"),
            "year": result_date.year
        }


# Example usage
if __name__ == "__main__":
    date_utils = DateUtilsTool()
    
    # Get current date
    print("Current date:", date_utils.get_current_date())
    
    # Get date ranges
    print("\nThis week:", date_utils.get_date_range("this_week"))
    print("\nLast week:", date_utils.get_date_range("last_week"))
    print("\nThis month:", date_utils.get_date_range("this_month"))
    print("\nLast month:", date_utils.get_date_range("last_month"))
    print("\nNext month:", date_utils.get_date_range("next_month"))
    
    # Get relative dates
    print("\nTomorrow:", date_utils.get_relative_date("today", 1))
    print("\nLast Monday:", date_utils.get_relative_date("start_of_week", -7))
    print("\nNext Friday:", date_utils.get_relative_date("today", (4 - datetime.now().weekday()) % 7 + (7 if datetime.now().weekday() > 4 else 0))) 