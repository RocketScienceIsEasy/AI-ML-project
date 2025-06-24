import os
import base64
import urllib.parse
import requests
import joblib
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import pipeline

# Load environment variables
load_dotenv()
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# Initialize FastAPI app
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load models
model = joblib.load("book_genre_classifier.joblib")
hf_classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# Genre to music mood map
# (unchanged from original)
genre_music_map = {
    "Fantasy": ["epic fantasy", "medieval ambient", "cinematic"],
    "Epic Fantasy": ["epic orchestral", "battle themes", "fantasy soundtracks"],
    "Dark Fantasy": ["dark ambient", "gothic instrumental", "medieval horror"],
    "Historical Fantasy": ["period drama", "ancient scores", "folk orchestral"],
    "Political Fantasy": ["tense orchestral", "chess match soundtrack", "dark intrigue"],
    "Science Fiction": ["synthwave", "futuristic ambient", "cyberpunk"],
    "Adventure": ["cinematic adventure", "heroic scores", "quest themes"],
    "Action": ["intense instrumentals", "high tempo beats", "movie action music"],
    "Drama": ["emotional piano", "cinematic slow burn", "melancholic strings"],
    "Fiction": ["lofi chill", "acoustic", "reading music"],
    "Nonfiction": ["jazz", "classical focus", "study beats"],
    "Romance": ["love songs", "soft indie", "acoustic romance"],
    "Thriller": ["suspense", "dark ambient", "cinematic thriller"],
    "Mystery": ["noir jazz", "piano mystery", "crime soundtrack"],
    "Biography": ["soulful jazz", "instrumental", "reflective piano"],
    "Horror": ["horror scores", "creepy ambient", "dark drone"],
    "Historical": ["period drama", "folk classics", "epic orchestral"],
    "Satire": ["quirky jazz", "light piano", "playful background music"],
    "Self-Help": ["uplifting beats", "peaceful piano", "focus lo-fi"],
    "Coming of Age": ["nostalgic indie", "emotional acoustic", "teen drama soundtrack"],
    "Philosophical": ["ambient minimal", "thoughtful piano", "existential jazz"],
    "Literary Fiction": ["cinematic reading", "soulful ambient", "deep focus"],
    "Post-Apocalyptic": ["dystopian synth", "tense ambient", "moody electronica"],
    "Dystopian": ["gritty synth", "darkwave", "industrial ambient"],
    "Apocalyptic": ["desolate ambient", "survival themes", "post-industrial"],
    "Magical Realism": ["whimsical piano", "fantasy fusion", "ethereal soundscapes"],
    "Psychological Thriller": ["dark pulse", "suspense drone", "mental games soundtrack"],
    "Classic Literature": ["period chamber", "timeless strings", "vintage piano"],
    "Crime": ["detective noir", "urban jazz", "thriller beats"],
    "Comedy": ["quirky tunes", "lighthearted jazz", "playful groove"],
    "Young Adult": ["youthful pop", "soft rock", "teen anthems"],
    "General": ["lofi", "ambient", "instrumental"]
}  # KEEP ORIGINAL MAPPING HERE

candidate_labels = list(genre_music_map.keys())

# Genre Priority Mapping
genre_priority = {}

# Shared priorities
for g in ["Dark Fantasy", "Dystopian"]:
    genre_priority[g] = 3

# Remaining priorities
genre_priority.update({
    "Psychological Thriller": 1,
    "Political Fantasy": 2,
    "Philosophical": 4,
    "Post-Apocalyptic": 5,
    "Horror": 6,
    "Science Fiction": 7,
    "Mystery": 8,
    "Thriller": 9,
    "Historical": 10,
    "Fantasy": 11,
    "Adventure": 12,
    "Classic Literature": 13,
    "Fiction": 14,
    "Romance": 15,
    "Comedy": 16,
    "Self-Help": 17,
    "Nonfiction": 18,
    "Young Adult": 19
})  # KEEP ORIGINAL PRIORITY MAPPING HERE

def get_moods(genre: str):
    return genre_music_map.get(genre, ["lofi", "ambient"])

def fetch_book_description(title: str):
    try:
        url = f"https://www.googleapis.com/books/v1/volumes?q={urllib.parse.quote(title)}&maxResults=1"
        response = requests.get(url).json()
        if "items" not in response:
            return ""
        return response["items"][0]["volumeInfo"].get("description", "")
    except Exception:
        return ""

def get_spotify_token():
    auth_str = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
    b64_auth = base64.b64encode(auth_str.encode()).decode()
    headers = {
        "Authorization": f"Basic {b64_auth}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}

    print("🧪 Requesting Spotify token with headers and data:")
    print(headers)
    print(data)

    res = requests.post("https://accounts.spotify.com/api/token", headers=headers, data=data)
    return res.json().get("access_token")

def search_spotify_playlists(moods, book_title):
    token = get_spotify_token()
    if not token:
        return [{"name": "No token available", "url": "#"}]

    headers = {"Authorization": f"Bearer {token}"}
    playlists = []

    # Search by mood
    for mood in moods:
        print(f"🔎 Searching Spotify for playlists titled like: {mood}")
        query = urllib.parse.quote(mood)
        url = f"https://api.spotify.com/v1/search?q={query}&type=playlist&limit=2"
        try:
            res = requests.get(url, headers=headers)
            items = res.json().get("playlists", {}).get("items", [])
            for item in items:
                playlists.append({
                    "name": item["name"],
                    "url": item["external_urls"]["spotify"]
                })
        except Exception as e:
            print(f"⚠️ Spotify search error for '{mood}': {str(e)}")

    # Search by book title
    print(f"🔎 Searching Spotify for playlists titled like: Reading {book_title}")
    try:
        query = urllib.parse.quote(f"Reading {book_title}")
        url = f"https://api.spotify.com/v1/search?q={query}&type=playlist&limit=2"
        res = requests.get(url, headers=headers)
        items = res.json().get("playlists", {}).get("items", [])
        for item in items:
            playlists.append({
                "name": item["name"],
                "url": item["external_urls"]["spotify"]
            })
    except Exception as e:
        print(f"⚠️ Spotify search error for 'Reading {book_title}': {str(e)}")

    return playlists if playlists else [{"name": "No playlists found", "url": "#"}]

class TitleRequest(BaseModel):
    title: str

@app.post("/recommend")
async def recommend(req: TitleRequest):
    title = req.title.strip()
    summary = fetch_book_description(title)

    predicted_genre = model.predict([title])[0]
    zero_shot = hf_classifier(summary, candidate_labels)
    zero_shot_genre = zero_shot["labels"][0]

    final_genres = {predicted_genre, zero_shot_genre}

    def genre_rank(g):
        return genre_priority.get(g, 999)

    sorted_genres = sorted(final_genres, key=genre_rank)
    primary_genre = sorted_genres[0]

    moods = get_moods(primary_genre)
    playlists = search_spotify_playlists(moods, title)

    response = {
        "message": f"""\
📘 Enter the book title: {title}

📖 Title Match: {title}
📝 Summary: {summary[:250]}{'...' if len(summary) > 250 else ''}

🤖 Zero-shot Genre: {zero_shot_genre}
🌟 Trained Model Genre: {predicted_genre}

🌟 Final Genre(s): {final_genres}

🎵 Music moods based on genre: {primary_genre} → {', '.join(moods)}

🎷 Suggested Playlists:
""" + "\n".join([f"• {p['name']} : {p['url']}" for p in playlists]) + f"""

🔎 Searching Spotify for playlists titled like: Reading {title}
• Reading {title} : https://open.spotify.com/search/{urllib.parse.quote_plus(f'Reading {title}')}
"""
    }
    return response
