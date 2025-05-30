from datetime import datetime, timedelta
from PySide6.QtCore import QObject, Signal
import json

class StatisticsController(QObject):
    credits_updated = Signal(dict)
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
    
    def get_credits_info(self):
        """Get formatted credits information"""
        credits_data = self.config_manager.get("pixelcut_credits", {})
        
        # Get current period data
        periods = credits_data.get("periods", [])
        if not periods:
            return self._get_empty_credits_info()
        
        current_period = periods[0]  # Most recent period
          # Extract values
        credits_remaining = current_period.get("creditsRemaining", 0)
        total_credits = current_period.get("credits", 0)
        credits_used = current_period.get("creditsUsed", 0)
        period_start = current_period.get("periodStart", "0")
        period_end = current_period.get("periodEnd", "0")
        grace_period_end = current_period.get("gracePeriodEnd", "0")
        
        # Calculate percentage
        usage_percentage = 0
        if total_credits > 0:
            usage_percentage = int((credits_used / total_credits) * 100)
        
        remaining_percentage = 100 - usage_percentage
        
        # Calculate days until expiry
        days_until_expiry = self._calculate_days_until_expiry(period_end)
        grace_days_until_expiry = self._calculate_days_until_expiry(grace_period_end)
        
        return {
            "credits_remaining": credits_remaining,
            "total_credits": total_credits,
            "credits_used": credits_used,
            "usage_percentage": usage_percentage,
            "remaining_percentage": remaining_percentage,
            "period_start": period_start,
            "period_end": period_end,
            "grace_period_end": grace_period_end,
            "days_until_expiry": days_until_expiry,
            "grace_days_until_expiry": grace_days_until_expiry,
            "expiry_text": self._format_expiry_text(period_end, days_until_expiry),
            "period_start_text": self._format_date_simple(period_start),
            "grace_period_text": self._format_expiry_text(grace_period_end, grace_days_until_expiry)
        }
    
    def _get_empty_credits_info(self):
        """Return empty credits info when no data available"""
        return {
            "credits_remaining": 0,
            "total_credits": 0,
            "credits_used": 0,
            "usage_percentage": 0,
            "remaining_percentage": 0,
            "period_end": "0",
            "days_until_expiry": 0,
            "expiry_text": "No data available"
        }
    def _calculate_days_until_expiry(self, period_end_str):
        """Calculate days until credits expire"""
        try:
            if period_end_str == "0" or not period_end_str:
                return 0
            
            # Parse ISO format timestamp (e.g., "2026-05-29T04:46:00.926Z")
            if "T" in period_end_str and "Z" in period_end_str:
                # Remove 'Z' and parse as ISO format
                period_end_str = period_end_str.replace("Z", "+00:00")
                expiry_date = datetime.fromisoformat(period_end_str).replace(tzinfo=None)
            else:
                # Parse numeric timestamp (milliseconds or seconds)
                if len(period_end_str) > 10:
                    timestamp = int(period_end_str) / 1000
                else:
                    timestamp = int(period_end_str)
                expiry_date = datetime.fromtimestamp(timestamp)
            
            current_date = datetime.now()
            days_diff = (expiry_date - current_date).days
            return max(0, days_diff)  # Don't return negative days
        except (ValueError, TypeError) as e:
            print(f"Error parsing expiry date '{period_end_str}': {e}")
            return 0
    def _format_expiry_text(self, period_end, days_until_expiry):
        """Format expiry date with days remaining"""
        try:
            if period_end == "0" or not period_end:
                return "No expiry data"
            
            # Parse ISO format timestamp (e.g., "2026-05-29T04:46:00.926Z")
            if "T" in period_end and "Z" in period_end:
                # Remove 'Z' and parse as ISO format
                period_end_clean = period_end.replace("Z", "+00:00")
                expiry_date = datetime.fromisoformat(period_end_clean).replace(tzinfo=None)
            else:
                # Parse numeric timestamp (milliseconds or seconds)
                if len(period_end) > 10:
                    timestamp = int(period_end) / 1000
                else:
                    timestamp = int(period_end)
                expiry_date = datetime.fromtimestamp(timestamp)
            
            formatted_date = expiry_date.strftime("%Y-%m-%d")
            
            if days_until_expiry == 0:
                return f"{formatted_date} (Expired or expires today)"
            elif days_until_expiry == 1:
                return f"{formatted_date} (1 day remaining)"
            else:
                return f"{formatted_date} ({days_until_expiry} days remaining)"
        except (ValueError, TypeError) as e:
            print(f"Error formatting expiry date '{period_end}': {e}")
            return "Invalid date"    
        
    def _format_date_simple(self, date_str):
        """Format date to simple readable format with days ago"""
        try:
            if date_str == "0" or not date_str:
                return "Unknown"
            
            # Parse ISO format timestamp (e.g., "2025-05-29T04:46:00.927526Z")
            if "T" in date_str and "Z" in date_str:
                # Remove 'Z' and parse as ISO format
                date_clean = date_str.replace("Z", "+00:00")
                date_obj = datetime.fromisoformat(date_clean).replace(tzinfo=None)
            else:
                # Parse numeric timestamp (milliseconds or seconds)
                if len(date_str) > 10:
                    timestamp = int(date_str) / 1000
                else:
                    timestamp = int(date_str)
                date_obj = datetime.fromtimestamp(timestamp)
            
            # Calculate days ago
            current_date = datetime.now()
            days_diff = (current_date - date_obj).days
            formatted_date = date_obj.strftime("%Y-%m-%d")
            
            if days_diff == 0:
                return f"{formatted_date} (today)"
            elif days_diff == 1:
                return f"{formatted_date} (1 day ago)"
            else:
                return f"{formatted_date} ({days_diff} days ago)"
        except (ValueError, TypeError) as e:
            print(f"Error formatting date '{date_str}': {e}")
            return "Invalid date"
    
    def update_credits_from_config(self):
        """Update credits info and emit signal"""
        credits_info = self.get_credits_info()
        self.credits_updated.emit(credits_info)
    
    def setup_ui_connections(self, ui_widget):
        """Setup connections between controller and UI elements"""
        self.ui_widget = ui_widget
        
        # Connect signal to update method
        self.credits_updated.connect(self.update_ui_display)
        
        # Initial update
        self.update_credits_from_config()
    def update_ui_display(self, credits_info):
        """Update UI elements with credits information"""
        if not hasattr(self, 'ui_widget') or not self.ui_widget:
            return
        
        # Update credits label
        credits_remaining = credits_info["credits_remaining"]
        total_credits = credits_info["total_credits"]
        self.ui_widget.creditsLabel.setText("API Credits")
        
        # Update credits progress bar
        if total_credits > 0:
            # Set maximum and current value
            self.ui_widget.creditsProgressBar.setMaximum(total_credits)
            self.ui_widget.creditsProgressBar.setValue(credits_remaining)
            
            # Set color based on remaining percentage
            remaining_percentage = (credits_remaining / total_credits) * 100
            self._set_credits_progress_color(remaining_percentage)
            
            # Update format to show remaining/total
            self.ui_widget.creditsProgressBar.setFormat(f"{credits_remaining}/{total_credits} credits ({remaining_percentage:.0f}%)")
        else:
            self.ui_widget.creditsProgressBar.setMaximum(1)
            self.ui_widget.creditsProgressBar.setValue(0)
            self.ui_widget.creditsProgressBar.setFormat("No credits data")
          # Update credits detail label
        credits_used = credits_info["credits_used"]
        period_start_text = credits_info.get("period_start_text", "Unknown")
        self.ui_widget.creditsDetailLabel.setText(
            f"{credits_remaining} remaining, {credits_used} used of {total_credits} total\n"
            f"Period started: {period_start_text}"
        )
          # Update expiry label and progress bar
        days_until_expiry = credits_info["days_until_expiry"]
        grace_days_until_expiry = credits_info.get("grace_days_until_expiry", 0)
        self.ui_widget.expiryLabel.setText("Credits Expiry")
        max_days = 365  # Assume max 1 year
        
        self.ui_widget.expiryProgressBar.setMaximum(max_days)
        self.ui_widget.expiryProgressBar.setValue(days_until_expiry)
        
        # Set color based on days remaining
        self._set_expiry_progress_color(days_until_expiry)
        
        # Update expiry format and detail
        if days_until_expiry > 0:
            self.ui_widget.expiryProgressBar.setFormat(f"{days_until_expiry} days left")
        else:
            self.ui_widget.expiryProgressBar.setFormat("Expired")
        
        # Update expiry detail with grace period info
        expiry_text = credits_info["expiry_text"]
        grace_period_text = credits_info.get("grace_period_text", "")
        
        if grace_days_until_expiry > 0:
            self.ui_widget.expiryDetailLabel.setText(
                f"{expiry_text}\nGrace period: {grace_period_text}"
            )
        else:
            self.ui_widget.expiryDetailLabel.setText(expiry_text)
    def _set_credits_progress_color(self, percentage):
        """Set progress bar color based on percentage"""
        if percentage == 0:
            color_class = "empty"
        elif percentage >= 70:
            color_class = "high"
        elif percentage >= 30:
            color_class = "medium"
        else:
            color_class = "low"
        
        self.ui_widget.creditsProgressBar.setProperty("progressLevel", color_class)
        self.ui_widget.creditsProgressBar.style().unpolish(self.ui_widget.creditsProgressBar)
        self.ui_widget.creditsProgressBar.style().polish(self.ui_widget.creditsProgressBar)
    def _set_expiry_progress_color(self, days):
        """Set expiry progress bar color based on days remaining"""
        if days == 0:
            color_class = "expired"
        elif days >= 30:
            color_class = "safe"
        elif days >= 7:
            color_class = "warning"
        else:
            color_class = "urgent"
        
        self.ui_widget.expiryProgressBar.setProperty("expiryLevel", color_class)
        self.ui_widget.expiryProgressBar.style().unpolish(self.ui_widget.expiryProgressBar)
        self.ui_widget.expiryProgressBar.style().polish(self.ui_widget.expiryProgressBar)
