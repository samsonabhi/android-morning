from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from datetime import datetime
import os
import random
from kivy.clock import mainthread
import threading
import urllib.request
import urllib.error
import json
import urllib.parse
import re
import time
import shutil


# Holiday and special events database
SPECIAL_EVENTS = {
    (1, 1): {"name": "New Year's Day", "keywords": ["new year", "celebration", "fireworks", "party"]},
    (2, 14): {"name": "Valentine's Day", "keywords": ["love", "romance", "hearts", "flowers"]},
    (3, 8): {"name": "International Women's Day", "keywords": ["women", "celebration", "empowerment"]},
    (3, 17): {"name": "St. Patrick's Day", "keywords": ["celebration", "green", "irish"]},
    (4, 22): {"name": "Earth Day", "keywords": ["nature", "earth", "green", "environment"]},
    (5, 1): {"name": "International Labor Day", "keywords": ["workers", "celebration", "unity"]},
    (7, 4): {"name": "Independence Day", "keywords": ["celebration", "fireworks", "america"]},
    (10, 31): {"name": "Halloween", "keywords": ["pumpkin", "spooky", "costume"]},
    (12, 25): {"name": "Christmas", "keywords": ["christmas", "celebration", "holiday", "festive"]},
}

class FunApp(App):
    def build(self):
        # Initialize with loading state
        self.events = []
        self.current_event_index = 0
        self._quotes_cache = []

        # Clean dataset folder on startup
        self._clean_dataset()

        # Layout
        self.layout = BoxLayout(orientation='vertical')
        
        # Event title label
        self.event_title = Label(
            text="Loading today's events...",
            font_size=20,
            bold=True,
            halign='center',
            valign='middle',
            size_hint=(1, 0.20)
        )
        self.event_title.bind(size=self.event_title.setter('text_size'))
        
        # Image widget
        self.image = Image(
            size_hint=(1, 0.50)
        )
        
        # Quote label
        self.quote_label = Label(
            text="Fetching inspiring quotes...",
            font_size=18,
            halign='center',
            valign='middle',
            size_hint=(1, 0.2)
        )
        self.quote_label.bind(size=self.quote_label.setter('text_size'))
        
        # Button
        self.button = Button(
            text="Next  ▶  Event / Quote",
            font_size=20,
            bold=True,
            size_hint=(1, 0.1),
            background_normal='',
            background_color=(0.18, 0.53, 0.93, 1),
            color=(1, 1, 1, 1),
        )
        self.button.bind(on_press=self.show_next_event)
        
        self.layout.add_widget(self.event_title)
        self.layout.add_widget(self.image)
        self.layout.add_widget(self.quote_label)
        self.layout.add_widget(self.button)
        
        # Start loading events in background
        self.load_today_events()
        
        return self.layout

    def on_stop(self):
        self._clean_dataset()

    def _clean_dataset(self):
        """Remove all files from the dataset folder"""
        dataset_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dataset')
        if os.path.exists(dataset_dir):
            shutil.rmtree(dataset_dir)
        os.makedirs(dataset_dir)
    
    def load_today_events(self):
        """Load today's events from Wikipedia 'On this day' and special events"""
        def fetch_events():
            try:
                now = datetime.now()
                month = now.month
                day = now.day
                
                events = []
                
                # Check for special holidays/events today
                if (month, day) in SPECIAL_EVENTS:
                    special_event = SPECIAL_EVENTS[(month, day)]
                    quotes = self.fetch_multiple_quotes(3)
                    events.append({
                        "name": special_event["name"],
                        "keyword": random.choice(special_event["keywords"]),
                        "quotes": quotes
                    })
                
                # Try to fetch Wikipedia events
                try:
                    month_str = now.strftime('%m')
                    day_str = now.strftime('%d')
                    url = f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/{month_str}/{day_str}"
                    
                    headers = {
                        'User-Agent': 'DailyEventsApp/1.0 (learning@project.com)'
                    }
                    
                    req = urllib.request.Request(url, headers=headers)
                    with urllib.request.urlopen(req, timeout=10) as response:
                        data = json.loads(response.read())
                        
                        for event in data.get('events', [])[:5]:  # Limit to 5 events
                            year = event.get('year', 'Unknown')
                            text = event.get('text', '')
                            
                            # Extract event name from the first sentence
                            event_name = text.split('.')[0] if '.' in text else text
                            if len(event_name) > 100:
                                event_name = event_name[:97] + "..."
                            
                            # Create keyword from event text
                            keyword = self.extract_keyword(text)
                            
                            # Fetch real quotes for this event
                            quotes = self.fetch_multiple_quotes(3)
                            
                            events.append({
                                "name": f"{year}: {event_name}",
                                "keyword": keyword,
                                "quotes": quotes
                            })
                except Exception as wiki_error:
                    pass
                
                if not events:
                    # Fallback events
                    events = [{
                        "name": f"April {day}, {now.year}",
                        "keyword": "celebration happiness",
                        "quotes": [
                            "Every day is a new opportunity!",
                            "Make today amazing!",
                            "Celebrate the gift of life!"
                        ]
                    }]
                
                self.events = events
                self.current_event_index = 0
                
                # Update UI with first event
                self.update_event_ui(0)
                
            except Exception as e:
                # Fallback events
                now = datetime.now()
                self.events = [
                    {
                        "name": f"April {now.day}, {now.year}",
                        "keyword": "celebration happiness joy",
                        "quotes": [
                            "Every day brings new possibilities!",
                            "Make today count!",
                            "Celebrate the gift of life!"
                        ]
                    },
                    {
                        "name": "Historical Moment",
                        "keyword": "history learning wisdom",
                        "quotes": [
                            "History teaches us valuable lessons!",
                            "Learn from the past to shape the future!",
                            "Every day has historical significance!"
                        ]
                    }
                ]
                self.current_event_index = 0
                self.update_event_ui(0)
        
        # Run in background thread
        thread = threading.Thread(target=fetch_events, daemon=True)
        thread.start()
    
    def extract_keyword(self, text):
        """Extract relevant keywords from event text"""
        # Simple keyword extraction - filter for meaningful words
        words = text.lower().split()
        keywords = []
        
        # Common event-related words to prioritize
        event_words = ['war', 'battle', 'born', 'died', 'discovered', 'invented', 
                      'founded', 'launched', 'signed', 'peace', 'revolution', 'election',
                      'treaty', 'assassination', 'disaster']
        
        for word in words:
            # Remove punctuation
            word = word.strip('.,!?;:')
            if (word in event_words or len(word) > 4) and word not in ['from', 'that', 'with', 'were', 'been']:
                keywords.append(word)
        
        if keywords:
            return ' '.join(keywords[:3])  # Take first 3 keywords
        else:
            return 'historical event'

    def fetch_multiple_quotes(self, count=3):
        """Fetch multiple quotes using ZenQuotes API, cached for the session"""
        fallback_quotes = [
            "Every day is a chance for greatness!",
            "Embrace the present moment!",
            "Life is a beautiful journey!",
            "Make today count!",
            "Celebrate the gift of existence!"
        ]

        try:
            if not self._quotes_cache:
                url = "https://zenquotes.io/api/quotes"
                headers = {'User-Agent': 'DailyEventsApp/1.0'}
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=8) as response:
                    data = json.loads(response.read())
                    self._quotes_cache = [
                        f'"{item["q"]}" - {item.get("a", "Unknown")}'
                        for item in data if item.get("q")
                    ]

            if self._quotes_cache:
                return random.sample(self._quotes_cache, min(count, len(self._quotes_cache)))
        except Exception:
            pass

        return random.sample(fallback_quotes, min(count, len(fallback_quotes)))
    
    @mainthread
    def update_event_ui(self, index):
        """Update UI with event data"""
        if index < len(self.events):
            event = self.events[index]
            self.event_title.text = event["name"]
            self.quote_label.text = random.choice(event["quotes"])
            self.load_event_image(index)
    
    def get_cached_image_path(self):
        """Return the single reused image path (keeps dataset folder to one file)"""
        dataset_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dataset')
        if not os.path.exists(dataset_dir):
            os.makedirs(dataset_dir)
        return os.path.join(dataset_dir, 'current.jpg')
    
    def get_high_quality_image_url(self, keyword):
        """Get high quality image URL using Google Image search or fallback sources"""
        search_keywords = urllib.parse.quote_plus(keyword or "celebration")
        try:
            # Use Google Images search page to find a relevant image URL
            url = f"https://www.google.com/search?tbm=isch&q={search_keywords}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9'
            }
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read().decode('utf-8', errors='ignore')
                matches = re.findall(r'https://[^\"\']+?\.(?:jpg|jpeg|png|webp|gif)', html)
                if matches:
                    image_url = matches[0]
                    return image_url
        except Exception as e:
            pass

        # Fallback: Use curated high-quality image sources
        high_quality_sources = {
            "celebration": "https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=1200&h=800&fit=crop",
            "christmas": "https://images.unsplash.com/photo-1543269865-cbdf26effbad?w=1200&h=800&fit=crop",
            "new year": "https://images.unsplash.com/photo-1504434318773-77635a50b0f1?w=1200&h=800&fit=crop",
            "valentine": "https://images.unsplash.com/photo-1518895949257-7621c3c786d7?w=1200&h=800&fit=crop",
            "love": "https://images.unsplash.com/photo-1518231557733-0c6f47ad1b44?w=1200&h=800&fit=crop",
            "holiday": "https://images.unsplash.com/photo-1511632765486-a01980e01a18?w=1200&h=800&fit=crop",
            "pumpkin": "https://images.unsplash.com/photo-1506259926900-3f6a79b04de0?w=1200&h=800&fit=crop",
            "halloween": "https://images.unsplash.com/photo-1506259926900-3f6a79b04de0?w=1200&h=800&fit=crop",
            "sparkle": "https://images.unsplash.com/photo-1442512595331-e89e6f47dba6?w=1200&h=800&fit=crop",
            "fireworks": "https://images.unsplash.com/photo-1504382216647-33e28496e0cd?w=1200&h=800&fit=crop",
            "history": "https://images.unsplash.com/photo-1519452575417-564c1401ecc0?w=1200&h=800&fit=crop",
            "book": "https://images.unsplash.com/photo-1507842217343-583f20270319?w=1200&h=800&fit=crop",
            "learning": "https://images.unsplash.com/photo-1524534694827-239e0b79be1d?w=1200&h=800&fit=crop",
            "nature": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=1200&h=800&fit=crop",
            "earth": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=1200&h=800&fit=crop"
        }
        for key, url in high_quality_sources.items():
            if key in keyword.lower():
                return url

        return "https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=1200&h=800&fit=crop"
    
    @mainthread
    def _set_button_loading(self):
        self.button.disabled = True
        self.button.text = "Loading image…"
        self.button.background_color = (0.45, 0.45, 0.45, 1)
        self.image.source = ''

    @mainthread
    def _set_button_ready(self):
        self.button.disabled = False
        self.button.text = "Next  ▶  Event / Quote"
        self.button.background_color = (0.18, 0.53, 0.93, 1)

    def load_event_image(self, index):
        """Load and display image for the current event with forced fresh download"""
        self._set_button_loading()

        def download_image():
            if index >= len(self.events):
                self._set_button_ready()
                return

            event = self.events[index]
            keyword = event["keyword"]

            cache_path = self.get_cached_image_path()
            if os.path.exists(cache_path):
                try:
                    os.remove(cache_path)
                except Exception:
                    pass
            
            try:
                # Get high quality image
                image_url = self.get_high_quality_image_url(keyword)
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                # Retry logic
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        req = urllib.request.Request(image_url, headers=headers)
                        with urllib.request.urlopen(req, timeout=10) as response:
                            image_data = response.read()

                            # Save to cache for the current session
                            with open(cache_path, 'wb') as f:
                                f.write(image_data)

                            self.update_image_ui(cache_path)
                            return
                    except Exception as retry_error:
                        if attempt < max_retries - 1:
                            time.sleep(1)
                
                # All retries failed
                self.update_image_ui(None)

            except Exception as e:
                self.update_image_ui(None)
        
        # Run download in background thread
        thread = threading.Thread(target=download_image, daemon=True)
        thread.start()
    
    @mainthread
    def update_image_ui(self, image_path):
        """Update the image widget"""
        if image_path and os.path.exists(image_path):
            self.image.source = ''
            self.image.source = image_path
            self.image.reload()
        else:
            fallback_url = "https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=800&h=600&fit=crop"
            self.image.source = fallback_url
        self._set_button_ready()
    
    def show_next_event(self, instance):
        """Cycle to next event or next quote, always fetching a fresh image"""
        if not self.events:
            return

        if self.current_event_index < len(self.events):
            event = self.events[self.current_event_index]
            current_quote = self.quote_label.text
            quotes = event["quotes"]

            # Find next quote
            try:
                current_index = quotes.index(current_quote)
                next_index = (current_index + 1) % len(quotes)
            except ValueError:
                current_index = -1
                next_index = 0

            if next_index == 0 and current_index == len(quotes) - 1:
                # Advance to next event
                self.current_event_index = (self.current_event_index + 1) % len(self.events)
                event = self.events[self.current_event_index]
                self.event_title.text = event["name"]
                self.quote_label.text = random.choice(event["quotes"])
            else:
                # Stay on current event, advance quote
                self.quote_label.text = quotes[next_index]

            # Always fetch a fresh image for the now-current event
            self.load_event_image(self.current_event_index)

if __name__ == '__main__':
    FunApp().run()