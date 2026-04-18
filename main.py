from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.core.window import Window
from kivy.utils import platform
from datetime import datetime
import os
import glob
import random
from kivy.clock import mainthread, Clock
import threading
import urllib.request
import urllib.error
import json
import re
import time
import shutil
import ssl

# Build SSL context — use certifi bundle if available (required on Android)
try:
    import certifi
    _SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _SSL_CONTEXT = ssl.create_default_context()


# Curated fallback images indexed by keyword fragment
_FALLBACK_IMAGES = {
    "celebration": "https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=1200&h=800&fit=crop",
    "christmas":   "https://images.unsplash.com/photo-1543269865-cbdf26effbad?w=1200&h=800&fit=crop",
    "new year":    "https://images.unsplash.com/photo-1504434318773-77635a50b0f1?w=1200&h=800&fit=crop",
    "valentine":   "https://images.unsplash.com/photo-1518895949257-7621c3c786d7?w=1200&h=800&fit=crop",
    "love":        "https://images.unsplash.com/photo-1518231557733-0c6f47ad1b44?w=1200&h=800&fit=crop",
    "holiday":     "https://images.unsplash.com/photo-1511632765486-a01980e01a18?w=1200&h=800&fit=crop",
    "halloween":   "https://images.unsplash.com/photo-1506259926900-3f6a79b04de0?w=1200&h=800&fit=crop",
    "pumpkin":     "https://images.unsplash.com/photo-1506259926900-3f6a79b04de0?w=1200&h=800&fit=crop",
    "fireworks":   "https://images.unsplash.com/photo-1504382216647-33e28496e0cd?w=1200&h=800&fit=crop",
    "nature":      "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=1200&h=800&fit=crop",
    "earth":       "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=1200&h=800&fit=crop",
    "history":     "https://images.unsplash.com/photo-1519452575417-564c1401ecc0?w=1200&h=800&fit=crop",
    "book":        "https://images.unsplash.com/photo-1507842217343-583f20270319?w=1200&h=800&fit=crop",
    "women":       "https://images.unsplash.com/photo-1524503033411-c9566986fc8f?w=1200&h=800&fit=crop",
    "workers":     "https://images.unsplash.com/photo-1504376830547-506dedfe681a?w=1200&h=800&fit=crop",
    "america":     "https://images.unsplash.com/photo-1501466044931-62695aada8e9?w=1200&h=800&fit=crop",
    "irish":       "https://images.unsplash.com/photo-1615478503562-ec2d8aa0e24e?w=1200&h=800&fit=crop",
}
_DEFAULT_IMAGE = "https://images.unsplash.com/photo-1519452575417-564c1401ecc0?w=1200&h=800&fit=crop"

def _fallback_image_for(keyword):
    kw = (keyword or "").lower()
    for key, url in _FALLBACK_IMAGES.items():
        if key in kw:
            return url
    return _DEFAULT_IMAGE

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
        self._last_quote = ""

        # Clean dataset folder on startup
        self._clean_dataset()

        # Layout
        self.layout = BoxLayout(orientation='vertical')

        # Top bar with share button
        top_bar = BoxLayout(orientation='horizontal', size_hint=(1, 0.08))
        top_bar.add_widget(Label(size_hint=(0.75, 1)))  # spacer
        self.share_btn = Button(
            text='',
            size_hint=(0.25, 1),
            background_normal='share_icon.png',
            background_down='share_icon.png',
            background_color=(1, 1, 1, 1),
            border=(0, 0, 0, 0),
        )
        self.share_btn.bind(on_press=self.share_screenshot)
        top_bar.add_widget(self.share_btn)

        # Event title label
        self.event_title = Label(
            text="Loading today's events...",
            font_size=70,
            bold=True,
            halign='center',
            valign='middle',
            size_hint=(1, 0.17)
        )
        self.event_title.bind(size=self.event_title.setter('text_size'))
        
        # Image widget
        self.image = Image(
            size_hint=(1, 0.45)
        )
        
        # Quote label
        self.quote_label = Label(
            text="Fetching inspiring quotes...",
            font_size=50,
            halign='center',
            valign='middle',
            size_hint=(1, 0.2)
        )
        self.quote_label.bind(size=self.quote_label.setter('text_size'))
        
        # Button
        self.button = Button(
            text="Refresh",
            font_size=40,
            bold=True,
            size_hint=(1, 0.1),
            background_normal='',
            background_color=(0.18, 0.53, 0.93, 1),
            color=(1, 1, 1, 1),
        )
        self.button.bind(on_press=self.show_next_event)
        
        self.layout.add_widget(top_bar)
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
        dataset_dir = os.path.join(self.user_data_dir, 'dataset')
        if os.path.exists(dataset_dir):
            shutil.rmtree(dataset_dir)
        os.makedirs(dataset_dir, exist_ok=True)
    
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
                    keyword = random.choice(special_event["keywords"])
                    quotes = self.fetch_multiple_quotes(3)
                    events.append({
                        "name": special_event["name"],
                        "keyword": keyword,
                        "image_url": _fallback_image_for(keyword),
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
                    with urllib.request.urlopen(req, timeout=10, context=_SSL_CONTEXT) as response:
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

                            # Use Wikipedia page image if available — skip gifs and svgs
                            image_url = None
                            for page in event.get('pages', []):
                                # Prefer originalimage, fall back to thumbnail
                                for key in ('originalimage', 'thumbnail'):
                                    src = page.get(key, {}).get('source', '')
                                    if src and not src.lower().endswith(('.gif', '.svg', '.svg.png')):
                                        image_url = src
                                        break
                                if image_url:
                                    break
                            if not image_url:
                                image_url = _fallback_image_for(keyword)

                            # Fetch real quotes for this event
                            quotes = self.fetch_multiple_quotes(3)

                            events.append({
                                "name": f"{year}: {event_name}",
                                "keyword": keyword,
                                "image_url": image_url,
                                "quotes": quotes
                            })
                except Exception as wiki_error:
                    pass
                
                if not events:
                    # Fallback events
                    events = [{
                        "name": f"April {day}, {now.year}",
                        "keyword": "celebration happiness",
                        "image_url": _DEFAULT_IMAGE,
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
                        "image_url": _DEFAULT_IMAGE,
                        "quotes": [
                            "Every day brings new possibilities!",
                            "Make today count!",
                            "Celebrate the gift of life!"
                        ]
                    },
                    {
                        "name": "Historical Moment",
                        "keyword": "history learning wisdom",
                        "image_url": _fallback_image_for("history"),
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
                with urllib.request.urlopen(req, timeout=8, context=_SSL_CONTEXT) as response:
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
    
    def _summarize_title(self, name):
        """Return a 5-word summary of a title, skipping common stop words"""
        stop = {'a','an','the','of','in','on','at','to','for','and','or','but',
                'is','was','were','be','by','with','from','that','this','as','it',
                'its','into','after','before','during','about','over','under'}
        words = re.sub(r'[^\w\s]', '', name).split()
        key_words = [w for w in words if w.lower() not in stop]
        chosen = key_words[:5] if key_words else words[:5]
        return 'On this day: ' + ' '.join(chosen)

    def _pick_quote(self, quotes):
        """Pick a quote that is different from the last one shown"""
        if len(quotes) == 1:
            self._last_quote = quotes[0]
            return quotes[0]
        candidates = [q for q in quotes if q != self._last_quote]
        if not candidates:
            candidates = quotes
        chosen = random.choice(candidates)
        self._last_quote = chosen
        return chosen

    @mainthread
    def update_event_ui(self, index):
        """Update UI with event data"""
        if index < len(self.events):
            event = self.events[index]
            self.event_title.text = self._summarize_title(event["name"])
            self.quote_label.text = self._pick_quote(event["quotes"])
            self.load_event_image(index)
    
    def get_cached_image_path(self, index):
        """Return a per-event image path so Kivy never serves a stale cached texture"""
        dataset_dir = os.path.join(self.user_data_dir, 'dataset')
        if not os.path.exists(dataset_dir):
            os.makedirs(dataset_dir, exist_ok=True)
        return os.path.join(dataset_dir, f'event_{index}.jpg')

    @mainthread
    def _set_button_loading(self):
        self.button.disabled = True
        self.button.text = "Loading image…"
        self.button.background_color = (0.45, 0.45, 0.45, 1)
        self.image.source = ''

    @mainthread
    def _set_button_ready(self):
        self.button.disabled = False
        self.button.text = "Refresh"
        self.button.background_color = (0.18, 0.53, 0.93, 1)

    def load_event_image(self, index):
        """Download and display the image stored in the event dict"""
        self._set_button_loading()

        def download_image():
            if index >= len(self.events):
                self._set_button_ready()
                return

            image_url = self.events[index].get("image_url", _DEFAULT_IMAGE)
            cache_path = self.get_cached_image_path(index)

            # Use cached file if it already exists for this event
            if os.path.exists(cache_path):
                self.update_image_ui(cache_path)
                return

            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            for attempt in range(3):
                try:
                    req = urllib.request.Request(image_url, headers=headers)
                    with urllib.request.urlopen(req, timeout=15, context=_SSL_CONTEXT) as response:
                        data = response.read()
                    # Verify it's a valid image (JPEG/PNG magic bytes)
                    if data[:3] == b'\xff\xd8\xff' or data[:8] == b'\x89PNG\r\n\x1a\n':
                        with open(cache_path, 'wb') as f:
                            f.write(data)
                        self.update_image_ui(cache_path)
                        return
                    else:
                        # Not a valid image — fall through to fallback
                        break
                except Exception:
                    if attempt < 2:
                        time.sleep(1)

            # URL failed or returned non-image — fall back to a fresh random picsum image
            try:
                req = urllib.request.Request("https://picsum.photos/1200/800", headers=headers)
                with urllib.request.urlopen(req, timeout=10, context=_SSL_CONTEXT) as response:
                    with open(cache_path, 'wb') as f:
                        f.write(response.read())
                self.update_image_ui(cache_path)
            except Exception:
                self.update_image_ui(None)

        threading.Thread(target=download_image, daemon=True).start()

    @mainthread
    def update_image_ui(self, image_path):
        """Update the image widget, bypassing Kivy's texture cache"""
        from kivy.cache import Cache
        if image_path and os.path.exists(image_path):
            Cache.remove('kv.image', image_path)
            Cache.remove('kv.texture', image_path)
            self.image.source = ''
            self.image.source = image_path
            self.image.reload()
        else:
            # Kivy Image cannot load URLs directly — leave blank on failure
            self.image.source = ''
        self._set_button_ready()
    
    def show_next_event(self, instance):
        """Pick a random event and fetch a brand-new image/quote on every click"""
        if not self.events:
            return

        self.current_event_index = random.randrange(len(self.events))
        event = self.events[self.current_event_index]
        self.event_title.text = self._summarize_title(event["name"])
        self.quote_label.text = self._pick_quote(event["quotes"])

        # Seedless picsum URL — each request follows a redirect to a different random image
        event["image_url"] = "https://picsum.photos/1200/800"

        # Delete cached image to force a fresh download
        cache_path = self.get_cached_image_path(self.current_event_index)
        if os.path.exists(cache_path):
            os.remove(cache_path)

        self.load_event_image(self.current_event_index)

    def share_screenshot(self, instance):
        """Take a screenshot and share it via Android share sheet"""
        try:
            # Clean up old share screenshots
            for f in glob.glob(os.path.join(self.user_data_dir, 'share_*.png')):
                try:
                    os.remove(f)
                except Exception:
                    pass

            screenshot_path = os.path.join(self.user_data_dir, 'share_{:04d}.png')
            actual_path = Window.screenshot(name=screenshot_path)

            if actual_path and os.path.exists(actual_path):
                Clock.schedule_once(lambda dt: self._do_share(actual_path), 0.5)
        except Exception:
            pass

    def _do_share(self, screenshot_path):
        """Trigger platform share sheet with screenshot"""
        try:
            if not os.path.exists(screenshot_path):
                return
            if platform == 'android':
                self._share_android(screenshot_path)
            # On desktop: screenshot saved silently, no share sheet
        except Exception:
            pass

    def _share_android(self, screenshot_path):
        try:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Intent = autoclass('android.content.Intent')
            FileProvider = autoclass('androidx.core.content.FileProvider')

            context = PythonActivity.mActivity
            java_file = autoclass('java.io.File')(screenshot_path)
            authority = 'com.example.dailyquote.fileprovider'
            uri = FileProvider.getUriForFile(context, authority, java_file)

            intent = Intent(Intent.ACTION_SEND)
            intent.setType('image/png')
            intent.putExtra(Intent.EXTRA_STREAM, uri)
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)

            share_text = f"{self.event_title.text}\n\n{self.quote_label.text}"
            intent.putExtra(Intent.EXTRA_TEXT, share_text)

            chooser = Intent.createChooser(intent, 'Share via')
            PythonActivity.mActivity.startActivity(chooser)
        except Exception:
            pass


if __name__ == '__main__':
    FunApp().run()