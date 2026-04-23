from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.core.window import Window
from kivy.utils import platform
from kivy.resources import resource_find
from kivy.metrics import dp
from datetime import datetime
import os
import random
from kivy.clock import mainthread, Clock
import threading
import urllib.request
import urllib.error
import urllib.parse
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


# API Ninjas key — get a free key at https://api-ninjas.com
API_NINJAS_KEY = "4fiuXASvic9NrNqWEinAFukT6x7UNSBNgEiSQDlT"

# Pexels API key — get a free key at https://www.pexels.com/api/
PEXELS_API_KEY = "KjQ1zvKmSESzrDqdscKaY8rcU3EgFUUIGc5vVnLdviDvDD2MkkwVBtvk"

# Morning-themed search queries rotated for each image request
_MORNING_QUERIES = [
    "sunrise",
    "morning coffee",
    "good morning",
    "sunrise sky",
    "morning light",
    "morning mist",
    "dawn landscape",
    "morning breakfast",
    "golden hour morning",
    "peaceful morning",
    "morning routine",
    "coffee cup morning",
]

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

class ImageButton(ButtonBehavior, Image):
    """A pressable Image that keeps its aspect ratio."""
    pass


class FunApp(App):
    def build(self):
        # Initialize with loading state
        self.events = []
        self.current_event_index = 0
        self._quotes_cache = []
        self._last_quote = ""

        # GIF frame playback state
        self._gif_frames = []
        self._gif_frame_idx = 0
        self._gif_clock = None

        # Black background so no white flash during loads
        Window.clearcolor = (0, 0, 0, 1)

        # Clean dataset folder on startup
        self._clean_dataset()

        # Layout
        self.layout = BoxLayout(orientation='vertical')

        # Hidden labels — not added to layout, but their .text is read by
        # _composite_image() to burn title + quote onto the display image.
        self.event_title = Label(text="Loading today's events...")
        self.quote_label = Label(text="Fetching inspiring quotes...")

        # Main display image (shows the composited photo)
        self.image = Image(
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0},
            keep_ratio=True,
            allow_stretch=True,
            opacity=0,
        )

        # Spinner: plain Image whose texture we swap manually each frame
        self.spinner_gif = Image(
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0},
            keep_ratio=True,
            allow_stretch=True,
            opacity=0,
        )

        # Load GIF frames via PIL after the first frame is rendered.
        # resource_find works on Android (searches Kivy's resource dirs which
        # include the app's own directory after packaging with Buildozer).
        # Fall back to __file__-relative path for desktop.
        _script_dir = os.path.dirname(os.path.abspath(__file__))
        self._gif_path = (resource_find('meme-coffee.gif')
                          or os.path.join(_script_dir, 'meme-coffee.gif'))
        Clock.schedule_once(self._init_gif_frames, 0)

        # image_container fills the whole screen minus the bottom bar
        self.image_container = FloatLayout(size_hint=(1, 0.9))
        self.image_container.add_widget(self.image)
        self.image_container.add_widget(self.spinner_gif)
        
        # Button fills the entire bar
        self.button = Button(
            text="Refresh",
            font_size=40,
            bold=True,
            size_hint=(1, 1),
            background_normal='',
            background_color=(0.18, 0.53, 0.93, 1),
            color=(1, 1, 1, 1),
        )
        self.button.bind(on_press=self.show_next_event)

        # WhatsApp icon floated on top of the bar at the right edge
        wa_icon = resource_find('whatsapp_icon.png') or 'whatsapp_icon.png'
        self.whatsapp_btn = ImageButton(
            source=wa_icon,
            keep_ratio=True,
            allow_stretch=True,
            size_hint=(None, None),
            size=(dp(52), dp(52)),
            pos_hint={'right': 0.98, 'center_y': 0.5},
        )
        self.whatsapp_btn.bind(on_press=self.share_whatsapp)

        # Bottom bar: single FloatLayout so the WA icon overlays the button
        bottom_bar = FloatLayout(size_hint=(1, 0.1))
        bottom_bar.add_widget(self.button)
        bottom_bar.add_widget(self.whatsapp_btn)

        self.layout.add_widget(self.image_container)
        self.layout.add_widget(bottom_bar)
        
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

                # Fetch celebrity birthdays FIRST so they appear at the top
                celeb_events = self.fetch_celebrity_birthdays(month, day)
                events.extend(celeb_events)

                # Check for special holidays/events today
                if (month, day) in SPECIAL_EVENTS:
                    special_event = SPECIAL_EVENTS[(month, day)]
                    keyword = random.choice(special_event["keywords"])
                    quotes = self.fetch_multiple_quotes(3)
                    events.append({
                        "name": special_event["name"],
                        "keyword": keyword,
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
                        "keyword": "morning",
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
                        "keyword": "morning",
                        "quotes": [
                            "Every day brings new possibilities!",
                            "Make today count!",
                            "Celebrate the gift of life!"
                        ]
                    },
                    {
                        "name": "Historical Moment",
                        "keyword": "morning light",
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

    def _lookup_celebrity_api(self, name):
        """Look up a single celebrity by name via API Ninjas. Returns dict or None."""
        if not API_NINJAS_KEY or API_NINJAS_KEY == "YOUR_API_NINJAS_KEY_HERE":
            return None
        try:
            encoded = urllib.parse.quote(name)
            url = f"https://api.api-ninjas.com/v1/celebrity?name={encoded}"
            headers = {
                'X-Api-Key': API_NINJAS_KEY,
                'User-Agent': 'DailyEventsApp/1.0',
            }
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=8, context=_SSL_CONTEXT) as response:
                results = json.loads(response.read())
            return results[0] if results else None
        except Exception:
            return None

    def fetch_celebrity_birthdays(self, month, day):
        """Fetch celebrities born on today's date.
        Uses Wikipedia births endpoint for the date-based list, then enriches
        each entry with API Ninjas Celebrity API for occupation/net-worth.
        Returns a list of event dicts ready for self.events."""
        try:
            month_str = f"{month:02d}"
            day_str = f"{day:02d}"
            url = (
                f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/births/"
                f"{month_str}/{day_str}"
            )
            headers = {'User-Agent': 'DailyEventsApp/1.0 (learning@project.com)'}
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10, context=_SSL_CONTEXT) as response:
                data = json.loads(response.read())

            births = data.get('births', [])
            # Sort by most recent birth year so modern celebs come first
            births.sort(key=lambda b: b.get('year', 0), reverse=True)

            events = []
            for birth in births[:5]:
                wiki_name = birth.get('text', '').split(',')[0].strip()
                birth_year = birth.get('year', '')
                if not wiki_name:
                    continue

                # Try to get extra detail from API Ninjas
                celeb = self._lookup_celebrity_api(wiki_name)
                if celeb:
                    occupation = celeb.get('occupation', [])
                    if isinstance(occupation, list):
                        occupation = occupation[0].replace('_', ' ').title() if occupation else ''
                    if occupation:
                        label = f"On this day: {occupation} {wiki_name} was born in {birth_year}"
                    else:
                        label = f"On this day: {wiki_name} was born in {birth_year}"
                else:
                    # Extract profession from Wikipedia description ("Name, profession, ...")
                    description = birth.get('text', '')
                    parts = [p.strip() for p in description.split(',')]
                    # parts[0] is the name; parts[1] is typically nationality+profession
                    profession = parts[1] if len(parts) > 1 else ''
                    if len(profession) > 60:
                        profession = profession[:57] + '...'
                    if profession:
                        label = f"On this day: {profession} {wiki_name} was born in {birth_year}"
                    else:
                        label = f"On this day: {wiki_name} was born in {birth_year}"

                quotes = self.fetch_multiple_quotes(3)
                events.append({
                    "name": label,
                    "keyword": "celebrity birthday",
                    "quotes": quotes,
                })
            return events
        except Exception:
            return []

    def fetch_pexels_image_url(self):
        """Fetch a random morning-themed image URL from Pexels API."""
        query = random.choice(_MORNING_QUERIES)
        try:
            encoded = urllib.parse.quote(query)
            url = f"https://api.pexels.com/v1/search?query={encoded}&per_page=15&orientation=landscape"
            headers = {
                'Authorization': PEXELS_API_KEY,
                'User-Agent': 'DailyEventsApp/1.0',
            }
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10, context=_SSL_CONTEXT) as response:
                data = json.loads(response.read())
            photos = data.get('photos', [])
            if photos:
                photo = random.choice(photos)
                # Use 'large2x' for high-res, fall back to 'large'
                src = photo.get('src', {})
                return src.get('large2x') or src.get('large') or src.get('original')
        except Exception:
            pass
        return None

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
        """Return a display title. Strings already prefixed with 'On this day:' are passed through as-is."""
        if name.startswith('On this day:'):
            return name
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
            self.event_title.text = self._summarize_title(event['name'])
            self.quote_label.text = self._pick_quote(event["quotes"])
            self.load_event_image(index)
    
    def get_cached_image_path(self, index):
        """Return a per-event image path so Kivy never serves a stale cached texture"""
        dataset_dir = os.path.join(self.user_data_dir, 'dataset')
        if not os.path.exists(dataset_dir):
            os.makedirs(dataset_dir, exist_ok=True)
        return os.path.join(dataset_dir, f'event_{index}.jpg')

    def get_composite_image_path(self, index):
        """Return the path for the text-composited version of the event image."""
        dataset_dir = os.path.join(self.user_data_dir, 'dataset')
        if not os.path.exists(dataset_dir):
            os.makedirs(dataset_dir, exist_ok=True)
        return os.path.join(dataset_dir, f'event_{index}_composite.jpg')

    def _init_gif_frames(self, dt):
        """Extract every frame from the GIF into Kivy textures on the main thread."""
        try:
            from PIL import Image as PilImage
            from kivy.graphics.texture import Texture
            gif = PilImage.open(self._gif_path)
            frames = []
            try:
                while True:
                    frame = gif.copy().convert('RGBA')
                    w, h = frame.size
                    tex = Texture.create(size=(w, h), colorfmt='rgba')
                    tex.blit_buffer(frame.tobytes(), colorfmt='rgba', bufferfmt='ubyte')
                    tex.flip_vertical()
                    frames.append(tex)
                    gif.seek(gif.tell() + 1)
            except EOFError:
                pass
            self._gif_frames = frames
            print(f'[GIF] Loaded {len(frames)} frames from {self._gif_path}')
        except Exception as e:
            print(f'[GIF] Failed to load frames: {e}')

    def _advance_gif_frame(self, dt):
        if self._gif_frames:
            self.spinner_gif.texture = self._gif_frames[self._gif_frame_idx]
            self._gif_frame_idx = (self._gif_frame_idx + 1) % len(self._gif_frames)

    def _start_spinner(self):
        self.image.opacity = 0
        self.spinner_gif.opacity = 1
        if self._gif_frames and self._gif_clock is None:
            self._gif_frame_idx = 0
            self._gif_clock = Clock.schedule_interval(self._advance_gif_frame, 0.05)

    def _stop_spinner(self):
        self.spinner_gif.opacity = 0
        if self._gif_clock:
            self._gif_clock.cancel()
            self._gif_clock = None
        self.image.opacity = 1

    @mainthread
    def _set_button_loading(self):
        self.button.disabled = True
        self.button.text = "Loading image…"
        self.button.background_color = (0.45, 0.45, 0.45, 1)
        self._start_spinner()

    @mainthread
    def _set_button_ready(self):
        self.button.disabled = False
        self.button.text = "Refresh"
        self.button.background_color = (0.18, 0.53, 0.93, 1)
        self._stop_spinner()

    def load_event_image(self, index):
        """Fetch a morning-themed image from Pexels and display it."""
        self._set_button_loading()

        def download_image():
            cache_path = self.get_cached_image_path(index)
            composite_path = self.get_composite_image_path(index)

            # Use composite if it already exists for this event
            if os.path.exists(composite_path):
                self.update_image_ui(composite_path)
                return

            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

            # Get a Pexels URL for a morning-themed image
            image_url = self.fetch_pexels_image_url()

            if image_url:
                for attempt in range(3):
                    try:
                        req = urllib.request.Request(image_url, headers=headers)
                        with urllib.request.urlopen(req, timeout=15, context=_SSL_CONTEXT) as response:
                            data = response.read()
                        if data[:3] == b'\xff\xd8\xff' or data[:8] == b'\x89PNG\r\n\x1a\n':
                            with open(cache_path, 'wb') as f:
                                f.write(data)
                            self._composite_image(cache_path, composite_path)
                            self.update_image_ui(composite_path)
                            return
                        else:
                            break
                    except Exception:
                        if attempt < 2:
                            time.sleep(1)

            self.update_image_ui(None)

        threading.Thread(target=download_image, daemon=True).start()

    @mainthread
    def update_image_ui(self, composite_path):
        """Update the image widget with the composited image, bypassing Kivy's texture cache."""
        from kivy.cache import Cache
        if composite_path and os.path.exists(composite_path):
            Cache.remove('kv.image', composite_path)
            Cache.remove('kv.texture', composite_path)
            self.image.source = ''
            self.image.source = composite_path
            self.image.reload()
        else:
            self.image.source = ''
        self._set_button_ready()
    
    def show_next_event(self, instance):
        """Pick a random event and fetch a brand-new Pexels image/quote on every click"""
        if not self.events:
            return

        self.current_event_index = random.randrange(len(self.events))
        event = self.events[self.current_event_index]
        self.event_title.text = self._summarize_title(event['name'])
        self.quote_label.text = self._pick_quote(event["quotes"])

        # Delete cached images to force a fresh Pexels download and re-composite
        cache_path = self.get_cached_image_path(self.current_event_index)
        if os.path.exists(cache_path):
            os.remove(cache_path)
        composite_path = self.get_composite_image_path(self.current_event_index)
        if os.path.exists(composite_path):
            os.remove(composite_path)

        self.load_event_image(self.current_event_index)

    def share_whatsapp(self, instance):
        """Share the current event image + title + quote directly to WhatsApp."""
        if platform != 'android':
            self._share_desktop_simulation()
            return

        # Use the composite (text already burned in); fall back to raw image
        composite_path = self.get_composite_image_path(self.current_event_index)
        raw_path = self.get_cached_image_path(self.current_event_index)
        image_path = composite_path if os.path.exists(composite_path) else (
                     raw_path if os.path.exists(raw_path) else None)

        if image_path:
            Clock.schedule_once(lambda dt: self._send_whatsapp(image_path), 0.1)
        else:
            # Image not ready yet — share text only
            Clock.schedule_once(lambda dt: self._share_text_only(), 0.1)

    def _composite_image(self, image_path, out_path):
        """Render title + quote text onto the image and save to out_path.
        Returns True on success, False if Pillow is unavailable."""
        try:
            from PIL import Image as PilImage, ImageDraw, ImageFont
        except ImportError:
            shutil.copy2(image_path, out_path)
            return False

        title = self.event_title.text
        quote = self.quote_label.text

        img = PilImage.open(image_path).convert('RGB')
        w, h = img.size
        draw = ImageDraw.Draw(img)

        # Try to load a font that exists on both desktop and Android.
        # Kivy always bundles DroidSans; resource_find locates it in the
        # Kivy data directory on both platforms.
        font_size_title = max(16, h // 27)
        font_size_quote = max(12, h // 39)

        def _load_font(size, bold=False):
            candidates = []
            if bold:
                candidates += [
                    resource_find('fonts/DroidSans-Bold.ttf'),
                    resource_find('fonts/Roboto-Bold.ttf'),
                    'DejaVuSans-Bold.ttf', 'arialbd.ttf', 'arial.ttf',
                ]
            else:
                candidates += [
                    resource_find('fonts/DroidSans.ttf'),
                    resource_find('fonts/Roboto-Regular.ttf'),
                    'DejaVuSans.ttf', 'arial.ttf',
                ]
            for path in candidates:
                if not path:
                    continue
                try:
                    return ImageFont.truetype(path, size)
                except Exception:
                    pass
            return ImageFont.load_default()

        font_title = _load_font(font_size_title, bold=True)
        font_quote = _load_font(font_size_quote, bold=False)

        def wrap_text(text, font, max_width):
            words = text.split()
            lines, line = [], ''
            for word in words:
                test = (line + ' ' + word).strip()
                bbox = draw.textbbox((0, 0), test, font=font)
                if bbox[2] - bbox[0] <= max_width:
                    line = test
                else:
                    if line:
                        lines.append(line)
                    line = word
            if line:
                lines.append(line)
            return lines

        padding = w // 20
        max_text_w = w - 2 * padding

        title_lines = wrap_text(title, font_title, max_text_w)
        quote_lines = wrap_text(quote, font_quote, max_text_w)

        def line_h(font):
            bbox = draw.textbbox((0, 0), 'Ay', font=font)
            return bbox[3] - bbox[1]

        block_h = (len(title_lines) * (line_h(font_title) + 4)
                   + 12
                   + len(quote_lines) * (line_h(font_quote) + 4)
                   + padding)

        # Semi-transparent dark banner at the bottom
        overlay = PilImage.new('RGBA', img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        banner_top = h - block_h - padding
        overlay_draw.rectangle(
            [(0, banner_top), (w, h)],
            fill=(0, 0, 0, 160)
        )
        img = PilImage.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        draw = ImageDraw.Draw(img)

        y = banner_top + padding // 2
        for line in title_lines:
            draw.text((padding + 1, y + 1), line, font=font_title, fill=(0, 0, 0, 200))
            draw.text((padding, y), line, font=font_title, fill=(255, 230, 50))
            y += line_h(font_title) + 4
        y += 12
        for line in quote_lines:
            draw.text((padding + 1, y + 1), line, font=font_quote, fill=(0, 0, 0, 200))
            draw.text((padding, y), line, font=font_quote, fill=(255, 255, 255))
            y += line_h(font_quote) + 4

        img.save(out_path, 'JPEG', quality=90)
        return True

    def _share_desktop_simulation(self):
        """Desktop-only: simulate the share flow so it can be tested without Android.
        Composites title + quote onto the image exactly as the Android path does,
        then opens the result so you can inspect it."""
        import tempfile
        image_path = self.get_cached_image_path(self.current_event_index)
        share_text = self.event_title.text + '\n\n' + self.quote_label.text

        print('[Share simulation] ---- WhatsApp share preview ----')
        print(f'[Share simulation] Text:\n{share_text}')

        if os.path.exists(image_path):
            tmp_dir = tempfile.gettempdir()
            share_path = os.path.join(tmp_dir, 'share_image.jpg')
            self._composite_image(image_path, share_path)
            print(f'[Share simulation] Composited image saved to: {share_path}')
            import subprocess
            try:
                subprocess.Popen(['start', share_path], shell=True)
            except Exception as e:
                print(f'[Share simulation] Could not open image: {e}')
        else:
            print(f'[Share simulation] Image not ready at: {image_path} — would fall back to text-only')

    def _show_toast(self, context, message):
        """Show a short Toast message on Android for diagnostics."""
        try:
            from jnius import autoclass
            Toast = autoclass('android.widget.Toast')
            Toast.makeText(context, message, Toast.LENGTH_LONG).show()
        except Exception:
            pass

    def _send_whatsapp(self, image_path):
        """Fire an Android ACTION_SEND intent with the image + caption."""
        context = None
        try:
            from jnius import autoclass, cast
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Intent = autoclass('android.content.Intent')
            FileProvider = autoclass('androidx.core.content.FileProvider')
            ClipData = autoclass('android.content.ClipData')

            context = PythonActivity.mActivity

            # Composite text onto the image and write into getCacheDir() so
            # the <cache-path> entry in file_provider_paths.xml covers it.
            cache_dir = context.getCacheDir().getAbsolutePath()
            share_path = os.path.join(cache_dir, 'share_image.jpg')
            self._composite_image(image_path, share_path)

            java_file = autoclass('java.io.File')(share_path)
            authority = context.getPackageName() + '.fileprovider'
            uri = FileProvider.getUriForFile(context, authority, java_file)

            share_text = self.event_title.text + '\n\n' + self.quote_label.text

            intent = Intent(Intent.ACTION_SEND)
            intent.setType('image/jpeg')
            intent.putExtra(Intent.EXTRA_STREAM, cast('android.os.Parcelable', uri))
            intent.putExtra(Intent.EXTRA_TEXT, share_text)
            # ClipData + FLAG_GRANT_READ_URI_PERMISSION required on Android 10+
            intent.setClipData(ClipData.newRawUri('', uri))
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)

            # Explicitly grant URI read permission to WhatsApp packages.
            # FLAG_GRANT_READ_URI_PERMISSION alone is not reliably forwarded
            # by createChooser() to the individual apps on Android 10+.
            for pkg in ('com.whatsapp', 'com.whatsapp.w4b'):
                try:
                    context.grantUriPermission(pkg, uri, Intent.FLAG_GRANT_READ_URI_PERMISSION)
                except Exception:
                    pass

            chooser = Intent.createChooser(intent, 'Share')
            chooser.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            chooser.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            context.startActivity(chooser)
        except Exception as e:
            msg = str(e)[:200]
            print(f'[Share error] {msg}')
            if context:
                self._show_toast(context, msg)
            self._share_text_only()

    def _share_text_only(self):
        """Fallback: open a system share chooser with text only (no image)."""
        try:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Intent = autoclass('android.content.Intent')

            context = PythonActivity.mActivity
            share_text = self.event_title.text + '\n\n' + self.quote_label.text

            intent = Intent(Intent.ACTION_SEND)
            intent.setType('text/plain')
            intent.putExtra(Intent.EXTRA_TEXT, share_text)
            chooser = Intent.createChooser(intent, 'Share via')
            chooser.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            context.startActivity(chooser)
        except Exception as e:
            print(f'[Text share error] {e}')


if __name__ == '__main__':
    FunApp().run()