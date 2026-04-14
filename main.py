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

class FunApp(App):
    def build(self):
        # Initialize with loading state
        self.events = []
        self.current_event_index = 0
        
        # Layout
        self.layout = BoxLayout(orientation='vertical')
        
        # Event title label
        self.event_title = Label(
            text="Loading today's events...",
            font_size=28,
            bold=True,
            halign='center',
            valign='middle',
            size_hint=(1, 0.15)
        )
        self.event_title.bind(size=self.event_title.setter('text_size'))
        
        # Image widget
        self.image = Image(
            size_hint=(1, 0.55)
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
            text="Next Event / Quote",
            font_size=20,
            size_hint=(1, 0.1)
        )
        self.button.bind(on_press=self.show_next_event)
        
        self.layout.add_widget(self.event_title)
        self.layout.add_widget(self.image)
        self.layout.add_widget(self.quote_label)
        self.layout.add_widget(self.button)
        
        # Start loading events in background
        self.load_today_events()
        
        return self.layout
    
    def load_today_events(self):
        """Load today's events from Wikipedia 'On this day'"""
        def fetch_events():
            try:
                now = datetime.now()
                month = now.strftime('%B').lower()
                day = now.day
                
                # Wikipedia "On this day" API
                url = f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/{month}/{day}"
                
                headers = {
                    'User-Agent': 'DailyEventsApp/1.0 (learning@project.com)'
                }
                
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=10) as response:
                    data = json.loads(response.read())
                    
                    events = []
                    for event in data.get('events', [])[:5]:  # Limit to 5 events
                        year = event.get('year', 'Unknown')
                        text = event.get('text', '')
                        
                        # Extract event name from text
                        event_name = text.split('.')[0] if '.' in text else text[:50]
                        if len(event_name) > 50:
                            event_name = event_name[:47] + "..."
                        
                        # Create keyword from event text
                        keyword = self.extract_keyword(text)
                        
                        # Generate quotes for this event
                        quotes = self.generate_quotes_for_event(event_name, year)
                        
                        events.append({
                            "name": f"{year}: {event_name}",
                            "keyword": keyword,
                            "quotes": quotes
                        })
                    
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
                print(f"Error fetching events: {e}")
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
        # Simple keyword extraction
        words = text.lower().split()
        keywords = []
        
        # Common event-related words
        event_words = ['war', 'battle', 'born', 'died', 'discovered', 'invented', 
                      'founded', 'launched', 'signed', 'peace', 'revolution']
        
        for word in words:
            if word in event_words or len(word) > 4:
                keywords.append(word)
        
        if keywords:
            return ' '.join(keywords[:3])  # Take first 3 keywords
        else:
            return 'historical event'
    
    def generate_quotes_for_event(self, event_name, year):
        """Generate positive quotes related to the event"""
        base_quotes = [
            f"Celebrate the legacy of {event_name}!",
            f"Remember the impact of events from {year}!",
            f"History teaches us through moments like {event_name}!",
            f"Every historical event shapes our future!",
            f"Learn from the past, live in the present!"
        ]
        
        # Return 3 random quotes
        return random.sample(base_quotes, 3)
    
    @mainthread
    def update_event_ui(self, index):
        """Update UI with event data"""
        if index < len(self.events):
            event = self.events[index]
            self.event_title.text = event["name"]
            self.quote_label.text = random.choice(event["quotes"])
            self.load_event_image(index)
    
    def load_event_image(self, index):
        """Load and display image for the current event"""
        def download_image():
            if index >= len(self.events):
                return
                
            event = self.events[index]
            keyword = event["keyword"]
            
            # For demo purposes, use reliable static images based on keywords
            image_sources = {
                "celebration happiness joy": "https://images.pexels.com/photos/1108099/pexels-photo-1108099.jpeg?w=400&h=200&fit=crop",
                "history learning wisdom": "https://images.pexels.com/photos/159866/books-book-pages-read-literature-159866.jpeg?w=400&h=200&fit=crop",
                "cute pets animals": "https://images.pexels.com/photos/1108099/pexels-photo-1108099.jpeg?w=400&h=200&fit=crop",
                "siblings family love": "https://images.pexels.com/photos/1181690/pexels-photo-1181690.jpeg?w=400&h=200&fit=crop",
                "Parkinson's awareness health": "https://images.pexels.com/photos/3807517/pexels-photo-3807517.jpeg?w=400&h=200&fit=crop",
                "Christmas celebration holiday": "https://images.pexels.com/photos/4240471/pexels-photo-4240471.jpeg?w=400&h=200&fit=crop",
                "New Year celebration fireworks": "https://images.pexels.com/photos/2331697/pexels-photo-2331697.jpeg?w=400&h=200&fit=crop",
                "Valentine's Day love romance": "https://images.pexels.com/photos/3585365/pexels-photo-3585365.jpeg?w=400&h=200&fit=crop",
                "Halloween pumpkin spooky": "https://images.pexels.com/photos/3652392/pexels-photo-3652392.jpeg?w=400&h=200&fit=crop"
            }
            
            try:
                # Get image URL for the keyword
                image_url = image_sources.get(keyword)
                
                if image_url:
                    # Download the image
                    output_path = "dataset"
                    if not os.path.exists(output_path):
                        os.makedirs(output_path)
                    
                    headers = {
                        'User-Agent': 'DailyEventsApp/1.0'
                    }
                    
                    req = urllib.request.Request(image_url, headers=headers)
                    with urllib.request.urlopen(req, timeout=10) as response:
                        image_data = response.read()
                        
                        # Save image
                        image_path = os.path.join(output_path, f"event_{index}.jpg")
                        with open(image_path, 'wb') as f:
                            f.write(image_data)
                        
                        # Update UI
                        self.update_image_ui(image_path)
                        return
                
                # Fallback
                self.update_image_ui(None)
                            
            except Exception as e:
                print(f"Error downloading image for '{keyword}': {e}")
                self.update_image_ui(None)
        
        # Run download in background thread
        thread = threading.Thread(target=download_image, daemon=True)
        thread.start()
    
    @mainthread
    def update_image_ui(self, image_path):
        """Update the image widget"""
        if image_path and os.path.exists(image_path):
            self.image.source = image_path
            self.image.reload()
        else:
            # Fallback to a working static image
            self.image.source = 'https://images.pexels.com/photos/1108099/pexels-photo-1108099.jpeg?w=400&h=200&fit=crop'
    
    def show_next_event(self, instance):
        """Cycle to next event or next quote"""
        if not self.events:
            return
            
        # First, show all quotes for current event
        if self.current_event_index < len(self.events):
            event = self.events[self.current_event_index]
            current_quote = self.quote_label.text
            quotes = event["quotes"]
            
            # Find next quote
            try:
                current_index = quotes.index(current_quote)
                next_index = (current_index + 1) % len(quotes)
            except:
                next_index = 0
            
            if next_index == 0 and current_index == len(quotes) - 1:
                # Move to next event
                self.current_event_index = (self.current_event_index + 1) % len(self.events)
                event = self.events[self.current_event_index]
                self.event_title.text = event["name"]
                self.quote_label.text = random.choice(event["quotes"])
                self.load_event_image(self.current_event_index)
            else:
                # Just change quote in current event
                self.quote_label.text = quotes[next_index]
    
    def show_next_event(self, instance):
        """Cycle to next event or next quote"""
        if not self.events:
            return
            
        # First, show all quotes for current event
        if self.current_event_index < len(self.events):
            event = self.events[self.current_event_index]
            current_quote = self.quote_label.text
            quotes = event["quotes"]
            
            # Find next quote
            try:
                current_index = quotes.index(current_quote)
                next_index = (current_index + 1) % len(quotes)
            except:
                next_index = 0
            
            if next_index == 0 and current_index == len(quotes) - 1:
                # Move to next event
                self.current_event_index = (self.current_event_index + 1) % len(self.events)
                event = self.events[self.current_event_index]
                self.event_title.text = event["name"]
                self.quote_label.text = random.choice(event["quotes"])
                self.load_event_image(self.current_event_index)
            else:
                # Just change quote in current event
                self.quote_label.text = quotes[next_index]

if __name__ == '__main__':
    FunApp().run()