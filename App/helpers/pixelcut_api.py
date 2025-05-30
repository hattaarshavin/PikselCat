import requests
import json
import time
from PySide6.QtCore import QObject, Signal, QThread, QMutex, QTimer

class PixelcutApiWorker(QThread):
    """Worker thread for Pixelcut API calls with rate limiting"""
    credits_received = Signal(dict)  # Emit credit data
    error_occurred = Signal(str)     # Emit error message
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        
    def run(self):
        """Fetch credits from Pixelcut API with rate limiting"""
        try:
            # Get API config from config manager
            api_config = self.config_manager.get("api_endpoints", {})
            headers_config = self.config_manager.get("api_headers", {})
            
            credits_url = api_config.get("credits")
            if not credits_url:
                self.error_occurred.emit("Credits API URL not configured")
                return
            
            # Make API request with timeout
            response = requests.get(credits_url, headers=headers_config, timeout=12)
            
            if response.status_code == 200:
                credit_data = response.json()
                
                # Update config cache
                self.config_manager.set("pixelcut_credits", credit_data)
                self.config_manager.save_config()
                
                self.credits_received.emit(credit_data)
            else:
                error_msg = f"API request failed: {response.status_code}"
                if response.status_code == 429:
                    error_msg = "Rate limit exceeded. Please wait before trying again."
                elif response.status_code == 401:
                    error_msg = "Invalid API key"
                elif response.status_code == 403:
                    error_msg = "API access forbidden"
                
                self.error_occurred.emit(error_msg)
                
        except requests.exceptions.Timeout:
            error_msg = "Request timeout - Check connection"
            self.error_occurred.emit(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error: {str(e)}"
            self.error_occurred.emit(error_msg)
        except json.JSONDecodeError as e:
            error_msg = f"Invalid API response: {str(e)}"
            self.error_occurred.emit(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.error_occurred.emit(error_msg)

class PixelcutApiHelper(QObject):
    """Helper class for Pixelcut API operations with comprehensive safety measures"""
    credits_updated = Signal(int)    # Emit remaining credits
    credits_error = Signal(str)      # Emit error message
    validation_completed = Signal(bool, str, int)  # success, message, credits
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.current_credits = 0
        self.api_worker = None
        
        # SAFETY MEASURES - Much more conservative timing
        self.last_fetch_time = 0
        self.min_fetch_interval = 30000  # INCREASED: 30 seconds between fetches
        self.is_fetching = False
        self.fetch_mutex = QMutex()
        
        # Validation cache with longer duration - LOAD FROM CONFIG
        self.cache_duration = 300000  # INCREASED: 5 minutes cache
        self.min_validation_interval = 10000  # INCREASED: 10 seconds between validations
        
        # Load cache and daily tracking from config
        self._load_cache_from_config()
        self._load_daily_tracking_from_config()
        
        # Initialize from cached data
        self._load_cached_credits()
        
        # Setup daily reset timer
        self._setup_daily_reset_timer()
    
    def _load_cached_credits(self):
        """Load credits from cache on startup"""
        try:
            cached_credits = self.config_manager.get("pixelcut_credits", {}).get("creditsRemaining", 0)
            if cached_credits == 0:
                # Fallback to alternative key
                cached_credits = self.config_manager.get("pixelcut_credits", {}).get("credits_remaining", 0)
            
            self.current_credits = cached_credits
            # print(f"Loaded cached credits: {cached_credits}")
        except Exception as e:
            print(f"Error loading cached credits: {e}")
            self.current_credits = 0
    
    def _setup_daily_reset_timer(self):
        """Setup timer to reset daily API call counter"""
        try:
            self.daily_reset_timer = QTimer()
            self.daily_reset_timer.timeout.connect(self._reset_daily_counter)
            # Check every hour for date change
            self.daily_reset_timer.start(3600000)  # 1 hour = 3600000 ms
            # print("Daily reset timer initialized")
        except Exception as e:
            print(f"Error setting up daily reset timer: {e}")

    def _load_cache_from_config(self):
        """Load validation cache from config"""
        try:
            cache_data = self.config_manager.get("api_validation_cache", {})
            
            # Load validation cache
            self.validation_cache = cache_data.get("validation_cache", {})
            self.last_validation_time = cache_data.get("last_validation_time", 0)
            
            # Clean old cache entries
            current_time = int(time.time() * 1000)
            cache_to_remove = []
            for key, entry in self.validation_cache.items():
                if current_time - entry.get('timestamp', 0) > self.cache_duration * 2:  # Remove entries older than 10 minutes
                    cache_to_remove.append(key)
            
            for key in cache_to_remove:
                del self.validation_cache[key]
            
            # print(f"Loaded validation cache with {len(self.validation_cache)} entries")
        except Exception as e:
            print(f"Error loading cache from config: {e}")
            self.validation_cache = {}
            self.last_validation_time = 0
    
    def _save_cache_to_config(self):
        """Save validation cache to config"""
        try:
            cache_data = {
                "validation_cache": self.validation_cache,
                "last_validation_time": self.last_validation_time,
                "last_updated": int(time.time() * 1000)
            }
            
            self.config_manager.set("api_validation_cache", cache_data)
            # Don't save immediately to avoid too frequent writes
        except Exception as e:
            print(f"Error saving cache to config: {e}")
    
    def _load_daily_tracking_from_config(self):
        """Load daily API call tracking from config"""
        try:
            daily_data = self.config_manager.get("api_daily_tracking", {})
            
            self.last_reset_date = daily_data.get("last_reset_date", time.strftime('%Y-%m-%d'))
            self.daily_api_calls = daily_data.get("daily_api_calls", 0)
            self.max_daily_calls = 100  # Maximum 100 API calls per day
            self.last_fetch_time = daily_data.get("last_fetch_time", 0)
            
            # Check if we need to reset for new day
            current_date = time.strftime('%Y-%m-%d')
            if current_date != self.last_reset_date:
                # print(f"New day detected, resetting API counter from {self.daily_api_calls} to 0")
                self.daily_api_calls = 0
                self.last_reset_date = current_date
                self._save_daily_tracking_to_config()
            
            # print(f"Loaded daily tracking: {self.daily_api_calls}/{self.max_daily_calls} calls for {self.last_reset_date}")
        except Exception as e:
            print(f"Error loading daily tracking from config: {e}")
            self.last_reset_date = time.strftime('%Y-%m-%d')
            self.daily_api_calls = 0
            self.max_daily_calls = 100
            self.last_fetch_time = 0
    
    def _save_daily_tracking_to_config(self):
        """Save daily API call tracking to config"""
        try:
            daily_data = {
                "last_reset_date": self.last_reset_date,
                "daily_api_calls": self.daily_api_calls,
                "last_fetch_time": self.last_fetch_time,
                "last_updated": int(time.time() * 1000)
            }
            
            self.config_manager.set("api_daily_tracking", daily_data)
            # Save immediately for tracking data
            self.config_manager.save_config()
        except Exception as e:
            print(f"Error saving daily tracking to config: {e}")

    def _reset_daily_counter(self):
        """Reset daily API call counter if date has changed"""
        try:
            current_date = time.strftime('%Y-%m-%d')
            if current_date != self.last_reset_date:
                # print(f"Resetting daily API counter for new date: {current_date}")
                self.daily_api_calls = 0
                self.last_reset_date = current_date
                self._save_daily_tracking_to_config()
        except Exception as e:
            print(f"Error resetting daily counter: {e}")

    def _can_make_api_call(self):
        """Check if we can make an API call based on all safety measures"""
        try:
            current_time = int(time.time() * 1000)
            
            # Check daily limit
            if self.daily_api_calls >= self.max_daily_calls:
                # print(f"Daily API limit reached: {self.daily_api_calls}/{self.max_daily_calls}")
                return False, "Daily API limit reached"
            
            # Check if already fetching
            if self.is_fetching or (self.api_worker and self.api_worker.isRunning()):
                # print("API call already in progress")
                return False, "API call in progress"
            
            # Check minimum interval
            time_since_last = current_time - self.last_fetch_time
            if time_since_last < self.min_fetch_interval:
                # print(f"Rate limiting: {time_since_last}ms since last, minimum is {self.min_fetch_interval}ms")
                return False, f"Rate limited - wait {(self.min_fetch_interval - time_since_last)//1000} seconds"
            
            return True, "OK"
        except Exception as e:
            print(f"Error checking API call conditions: {e}")
            return False, f"Error: {e}"

    def fetch_credits(self):
        """Fetch current credits from API with comprehensive safety checks"""
        # SAFETY CHECK: Can we make API call?
        can_call, reason = self._can_make_api_call()
        if not can_call:
            # print(f"Skipping API call: {reason}")
            # Use cached data
            cached_credits = self.config_manager.get("pixelcut_credits", {}).get("creditsRemaining", 0)
            if cached_credits > 0:
                self.current_credits = cached_credits
                self.credits_updated.emit(cached_credits)
                # print(f"Using cached credits: {cached_credits}")
            else:
                self.credits_error.emit(reason)
            return
        
        # Acquire mutex to prevent concurrent fetches
        if not self.fetch_mutex.tryLock():
            # print("Credits fetch mutex locked, skipping")
            return
        
        try:
            self.is_fetching = True
            self.last_fetch_time = int(time.time() * 1000)
            self.daily_api_calls += 1
            
            # Save tracking data immediately
            self._save_daily_tracking_to_config()
            
            # print(f"Starting credits fetch from API (Daily calls: {self.daily_api_calls}/{self.max_daily_calls})")
            
            self.api_worker = PixelcutApiWorker(self.config_manager)
            self.api_worker.credits_received.connect(self.on_credits_received)
            self.api_worker.error_occurred.connect(self.on_credits_error)
            self.api_worker.finished.connect(self.on_worker_finished)
            self.api_worker.start()
            
        finally:
            self.fetch_mutex.unlock()

    def validate_api_key(self, api_key):
        """Validate API key with aggressive rate limiting and caching"""
        current_time = int(time.time() * 1000)
        
        # Check cache first - USE FULL API KEY for cache key, not just first 16 chars
        cache_key = api_key.strip() if api_key else ""  # Use full API key as cache key
        if cache_key and cache_key in self.validation_cache:
            cache_entry = self.validation_cache[cache_key]
            if current_time - cache_entry['timestamp'] < self.cache_duration:
                # print(f"Using cached validation result (age: {(current_time - cache_entry['timestamp'])//1000}s)")
                success = cache_entry['valid']
                message = cache_entry['message']
                credits = cache_entry['credits']
                self.validation_completed.emit(success, message, credits)
                return
        
        # SAFETY CHECK: Daily limit
        if self.daily_api_calls >= self.max_daily_calls:
            # print(f"Daily API limit reached for validation: {self.daily_api_calls}/{self.max_daily_calls}")
            # Use cached config data
            cached_credits = self.config_manager.get("pixelcut_credits", {}).get("creditsRemaining", 0)
            if cached_credits > 0:
                self.validation_completed.emit(True, f"Using cached validation ({cached_credits} credits)", cached_credits)
            else:
                self.validation_completed.emit(False, "Daily API limit reached", 0)
            return
        
        # Rate limiting check - VERY conservative
        time_since_last = current_time - self.last_validation_time
        if time_since_last < self.min_validation_interval:
            # print(f"Rate limiting validation: {time_since_last}ms since last, minimum is {self.min_validation_interval}ms")
            # ONLY use cache if exact API key exists in cache
            if cache_key and cache_key in self.validation_cache:
                cache_entry = self.validation_cache[cache_key]
                success = cache_entry['valid']
                message = cache_entry['message']
                credits = cache_entry['credits']
                self.validation_completed.emit(success, message, credits)
            else:
                self.validation_completed.emit(False, "Rate limited - enter complete API key", 0)
            return
        
        self.last_validation_time = current_time
        self.daily_api_calls += 1
        
        if not api_key or not api_key.strip():
            self.validation_completed.emit(False, "API key is empty", 0)
            return
        
        try:
            # print(f"Starting API key validation (Daily calls: {self.daily_api_calls}/{self.max_daily_calls})")
            url = "https://api.developer.pixelcut.ai/v1/credits"
            headers = {
                'Accept': 'application/json',
                'X-API-KEY': api_key.strip()
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            # print(f"Validation API response: {response.status_code}")
            
            if response.status_code == 200:
                credit_data = response.json()
                credits_remaining = credit_data.get("creditsRemaining", 0)
                
                # SAVE COMPLETE API RESPONSE TO CONFIG
                self.config_manager.set("pixelcut_credits", credit_data)
                self.config_manager.save_config()
                
                if credits_remaining > 0:
                    # Cache successful result with FULL API key
                    if cache_key:
                        self.validation_cache[cache_key] = {
                            'valid': True,
                            'message': f"Ready ({credits_remaining} credits available)",
                            'credits': credits_remaining,
                            'timestamp': current_time
                        }
                        # SAVE CACHE TO CONFIG
                        self._save_cache_to_config()
                    
                    self.validation_completed.emit(True, f"Ready ({credits_remaining} credits available)", credits_remaining)
                else:
                    # Cache insufficient credits result
                    if cache_key:
                        self.validation_cache[cache_key] = {
                            'valid': False,
                            'message': "Insufficient credits",
                            'credits': 0,
                            'timestamp': current_time
                        }
                        # SAVE CACHE TO CONFIG
                        self._save_cache_to_config()
                    
                    self.validation_completed.emit(False, "Insufficient credits", 0)
            else:
                error_msg = f"Invalid API key (Error {response.status_code})"
                if response.status_code == 429:
                    error_msg = "Rate limit exceeded. Please wait."
                    # Don't count rate limited calls against daily limit
                    self.daily_api_calls -= 1
                elif response.status_code == 401:
                    error_msg = "Invalid API key"
                elif response.status_code == 403:
                    error_msg = "API access forbidden"
                
                # Cache negative result for shorter time
                if cache_key:
                    self.validation_cache[cache_key] = {
                        'valid': False,
                        'message': error_msg,
                        'credits': 0,
                        'timestamp': current_time
                    }
                    # SAVE CACHE TO CONFIG
                    self._save_cache_to_config()
                
                self.validation_completed.emit(False, error_msg, 0)
                
        except requests.exceptions.RequestException as e:
            error_msg = "Network error - Check connection"
            print(f"Validation network error: {e}")
            self.validation_completed.emit(False, error_msg, 0)
        except Exception as e:
            error_msg = "Validation error"
            print(f"Validation unexpected error: {e}")
            self.validation_completed.emit(False, error_msg, 0)

    def quick_validate_api_key(self, api_key):
        """Quick validation - PREFERS cache over API calls but uses FULL API key"""
        current_time = int(time.time() * 1000)
        
        # ALWAYS check cache first and prefer it - USE FULL API KEY
        cache_key = api_key.strip() if api_key else ""  # Use full API key as cache key
        if cache_key and cache_key in self.validation_cache:
            cache_entry = self.validation_cache[cache_key]
            # Use cache even if older - only make API call if cache is very old
            if current_time - cache_entry['timestamp'] < (self.cache_duration * 3):  # Even longer cache for quick validation
                return cache_entry['valid'] and cache_entry['credits'] > 0
        
        # For quick validation, be very conservative about API calls
        # If no recent cache, assume invalid and require full validation
        if not cache_key:
            return False
        
        # Check if we have any recent cached credits in config
        cached_credits = self.config_manager.get("pixelcut_credits", {}).get("creditsRemaining", 0)
        if cached_credits > 0:
            # We have some cached credits, likely valid
            # Cache this assumption
            if cache_key:
                self.validation_cache[cache_key] = {
                    'valid': True,
                    'message': f"Assumed valid ({cached_credits} cached credits)",
                    'credits': cached_credits,
                    'timestamp': current_time
                }
            return True
        
        # No cache, no credits - assume invalid for quick check
        return False

    def _save_cache_to_config(self):
        """Save validation cache to config with cleanup"""
        try:
            # Clean cache before saving - remove old entries and limit size
            current_time = int(time.time() * 1000)
            cache_to_remove = []
            
            # Remove entries older than cache duration
            for key, entry in self.validation_cache.items():
                if current_time - entry.get('timestamp', 0) > self.cache_duration * 2:
                    cache_to_remove.append(key)
            
            for key in cache_to_remove:
                del self.validation_cache[key]
            
            # Limit cache size to prevent config file from growing too large
            if len(self.validation_cache) > 50:  # Keep only 50 most recent entries
                # Sort by timestamp and keep newest 50
                sorted_cache = sorted(
                    self.validation_cache.items(), 
                    key=lambda x: x[1].get('timestamp', 0), 
                    reverse=True
                )
                self.validation_cache = dict(sorted_cache[:50])
            
            cache_data = {
                "validation_cache": self.validation_cache,
                "last_validation_time": self.last_validation_time,
                "last_updated": current_time
            }
            
            self.config_manager.set("api_validation_cache", cache_data)
            # print(f"Saved validation cache with {len(self.validation_cache)} entries")
        except Exception as e:
            print(f"Error saving cache to config: {e}")

    def on_credits_received(self, credit_data):
        """Handle successful credit data reception"""
        try:
            # Extract credits from API response
            credits_remaining = credit_data.get("creditsRemaining", 0)
            if credits_remaining == 0:
                credits_remaining = credit_data.get("credits_remaining", 0)
            
            self.current_credits = credits_remaining
            # print(f"Credits updated: {credits_remaining}")
            self.credits_updated.emit(credits_remaining)
        except Exception as e:
            print(f"Error processing credits data: {e}")
            self.on_credits_error(f"Error processing credits: {e}")
    
    def on_credits_error(self, error_message):
        """Handle credit fetch error"""
        try:
            print(f"Credits fetch error: {error_message}")
            # Fall back to cached value from config
            cached_credits = self.config_manager.get("pixelcut_credits", {}).get("creditsRemaining", 0)
            self.current_credits = cached_credits
            # print(f"Using cached credits after error: {cached_credits}")
            self.credits_error.emit(error_message)
        except Exception as e:
            print(f"Error handling credits error: {e}")
    
    def on_worker_finished(self):
        """Clean up worker thread"""
        try:
            # print("Credits fetch worker finished")
            self.is_fetching = False
            if self.api_worker:
                self.api_worker.deleteLater()
                self.api_worker = None
        except Exception as e:
            print(f"Error cleaning up worker: {e}")

    def get_current_credits(self):
        """Get current credits count"""
        return self.current_credits
    
    def has_sufficient_credits(self, required_credits):
        """Check if current credits are sufficient for operation"""
        return self.current_credits >= required_credits
