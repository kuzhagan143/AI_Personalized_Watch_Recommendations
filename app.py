import streamlit as st
import json
import os
import requests
import httpx
import random
import time
from collections import Counter
import concurrent.futures
from google import genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure APIs globally if available in .env
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

st.set_page_config(page_title="Personalized Recommender", page_icon="🎬", layout="wide")

# Custom CSS for dark theme and styling referencing modern, aesthetic UI
st.markdown("""
<style>
    /* Gradient animated background */
    .stApp {
        background: linear-gradient(-45deg, #0f0c29, #302b63, #24243e);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
        color: #e0e0e0;
    }
    
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    .poster-img {
        border-radius: 12px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.6);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .poster-img:hover {
        transform: scale(1.05);
        box-shadow: 0 12px 24px rgba(0,0,0,0.8);
    }
    
    /* Sleek card container */
    div[data-testid="stVerticalBlock"] > div > div > div.rec-card-container {
        background-color: rgba(30, 30, 30, 0.6);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        padding: 1.5rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: transform 0.2s ease, border 0.2s ease;
    }
    
    div[data-testid="stVerticalBlock"] > div > div > div.rec-card-container:hover {
        transform: translateY(-5px);
        border: 1px solid rgba(255, 255, 255, 0.3);
    }
    
    .rec-title {
        color: #ffffff;
        font-weight: 800;
        font-size: 1.4rem;
        margin-bottom: 0.5rem;
        font-family: 'Inter', sans-serif;
    }
    
    .rec-reason {
        color: #bbbbbb;
        font-size: 1rem;
        margin-bottom: 1rem;
        line-height: 1.5;
    }
    
    .confidence-badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-left: 0.5rem;
        vertical-align: middle;
    }
    .conf-high { background-color: rgba(46, 204, 113, 0.2); color: #2ecc71; border: 1px solid rgba(46, 204, 113, 0.4); }
    .conf-med { background-color: rgba(241, 196, 15, 0.2); color: #f1c40f; border: 1px solid rgba(241, 196, 15, 0.4); }
    .conf-low { background-color: rgba(231, 76, 60, 0.2); color: #e74c3c; border: 1px solid rgba(231, 76, 60, 0.4); }
</style>
""", unsafe_allow_html=True)

st.title("🎬 AI Personalized Watch Recommendations")
st.markdown("Upload your Trakt `watch_history.json` and let Gemini orchestrate your next binge, ensuring you never get a duplicate recommendation!")

# Sidebar for API Keys and File Upload
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key_gemini = st.text_input("Google Gemini API Key", value=GEMINI_API_KEY if GEMINI_API_KEY else "", type="password")
    api_key_tmdb = st.text_input("TMDB API Key", value=TMDB_API_KEY if TMDB_API_KEY else "", type="password")
    
    st.header("📁 Upload Data")
    uploaded_files = st.file_uploader("Upload Trakt watch_history.json files", type=["json"], accept_multiple_files=True)
    
    st.header("✨ Preferences (Optional)")
    user_prefs = st.text_input("Any specific mood or genre today?", placeholder="e.g., Anime, Rom Com, 90s action")

def parse_watch_history(data):
    """
    Parses the Trakt history JSON and extracts unique movie/show titles.
    """
    watched_titles = set()
    for item in data:
        if item.get("type") == "episode" and "show" in item:
            watched_titles.add(item["show"]["title"])
        elif item.get("type") == "movie" and "movie" in item:
            watched_titles.add(item["movie"]["title"])
    return list(watched_titles)


# A small cache/mapping of TMDB Genre IDs to Names
# It's better to fetch this from TMDB once, but a hardcoded dict is fast and reliable for movies & TV
TMDB_GENRES = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy", 80: "Crime", 
    99: "Documentary", 18: "Drama", 10751: "Family", 14: "Fantasy", 36: "History", 
    27: "Horror", 10402: "Music", 9648: "Mystery", 10749: "Romance", 878: "Science Fiction", 
    10770: "TV Movie", 53: "Thriller", 10752: "War", 37: "Western",
    10759: "Action & Adventure", 10762: "Kids", 10763: "News", 10764: "Reality", 
    10765: "Sci-Fi & Fantasy", 10766: "Soap", 10767: "Talk", 10768: "War & Politics"
}

def get_top_genres(watched_list, tmdb_key, st_status_obj=None, sample_size=200, top_n=5):
    """
    Randomly samples up to `sample_size` titles from the watched list,
    fetches their genre IDs concurrently from TMDB, and returns the top N genres.
    """
    sampled_list = random.sample(watched_list, min(len(watched_list), sample_size))
    genre_counts = Counter()

    def fetch_genre_for_title(title):
        url = f"https://api.themoviedb.org/3/search/multi?api_key={tmdb_key}&query={title}"
        
        # Simple retry logic for the concurrent requests
        for attempt in range(3):
            try:
                res = requests.get(url, timeout=5)
                # If rate limited, sleep briefly and retry
                if res.status_code == 429:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                    
                if res.status_code == 200:
                    data = res.json()
                    if "results" in data and len(data["results"]) > 0:
                        for item in data["results"]:
                            if item.get("media_type") in ["movie", "tv"] and "genre_ids" in item:
                                return item["genre_ids"]
                break # Break if successful or standard error
            except Exception:
                # On timeout or connection error, wait and retry
                time.sleep(1)
        return []

    results = []
    
    # Optional stream output for Streamlit
    if st_status_obj:
        progress_bar = st_status_obj.progress(0, text="Fetching genres from TMDB...")
        completed_count = 0
        total_count = len(sampled_list)

    # Use ThreadPoolExecutor to make concurrent API calls
    # Max workers set to 15 to be respectful of the 50 req/sec rate limit
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        # Submit all tasks
        future_to_title = {executor.submit(fetch_genre_for_title, title): title for title in sampled_list}
        
        for future in concurrent.futures.as_completed(future_to_title):
            title = future_to_title[future]
            try:
                ids = future.result()
                results.append(ids)
            except Exception as e:
                pass
            finally:
                if st_status_obj:
                    completed_count += 1
                    # Update progress bar
                    progress_text = f"Analyzed {completed_count}/{total_count} titles... (Just checked: {title})"
                    progress_bar.progress(completed_count / total_count, text=progress_text)
                    
    if st_status_obj:
        progress_bar.empty() # Remove the progress bar when done

    # Flatten the list of lists of ids and count them
    for ids in results:
        if ids:
            for genre_id in ids:
                if genre_id in TMDB_GENRES:
                    genre_counts[TMDB_GENRES[genre_id]] += 1

    # Get the top N genres
    top_genres = [genre for genre, count in genre_counts.most_common(top_n)]
    return top_genres
    

def get_recommendations(watched_list, top_genres, user_preferences, gemini_key):
    """
    Constructs prompt, sends it to Gemini, constraints to exclude watched_list,
    and parses the result back as JSON.
    """
    # Initialize the new genai client properly assigning the key
    client = genai.Client(api_key=gemini_key)
    
    # Optional limit if the string is exceedingly huge
    sampled_list = watched_list[:1500] if len(watched_list) > 1500 else watched_list
    watched_str = ", ".join(sampled_list)
    
    genres_str = ", ".join(top_genres) if top_genres else "Unknown"
    pref_instruction = f"\nUSER SPECIFIC PREFERENCE: The user has requested: '{user_preferences}'. You MUST heavily bias your recommendations to fit this specific preference above all else.\n" if user_preferences else ""
    
    prompt = f"""You are an expert movie and TV show recommender.
Here is a list of movies and TV shows the user has already watched.

[WATCHED LIST START]
{watched_str}
[WATCHED LIST END]

USER TASTE PROFILE (Based on history):
Their most frequently watched genres are: {genres_str}.
{pref_instruction}
TASK:
1. Analyze this viewing history and genre preference to understand their taste.
2. Suggest exactly 20 NEW titles (a healthy mix of movies and TV shows) that they will love.

CRUCIAL CONSTRAINT: 
You must strictly EXCLUDE any title that is already in the Watched List above. You are forbidden from recommending anything they have already seen.

FORMAT REQUIREMENT:
Provide your recommendations in valid JSON format ONLY. Ensure the JSON is properly escaped.
It must follow this exact structure:
[
  {{
    "title": "Exact Title of Movie or Show",
    "type": "Movie" or "TV Show",
    "reason": "1-2 sentence explanation of why this fits their specific taste profile perfectly.",
    "confidence": 92
  }}
]
"""
    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview", 
            contents=prompt
        )
        text = response.text.strip()
        # Clean up markdown output if model wraps the JSON
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
            
        return json.loads(text.strip()), prompt
    except Exception as e:
        st.error(f"Error communicating with Gemini: {e}")
        # Show what Gemini actually replied with to help debug
        try:
             st.error(f"Raw response was: {response.text}")
        except:
             pass
        return None, prompt

def fetch_tmdb_metadata(title, tmdb_key):
    """
    Fetches the poster, release date, and plot summary from TMDB using a search query with retries.
    """
    url = f"https://api.themoviedb.org/3/search/multi?api_key={tmdb_key}&query={title}"
    
    for attempt in range(3):
        try:
            res = requests.get(url, timeout=10)
            
            # Identify rate limiting
            if res.status_code == 429:
                time.sleep(1 * (attempt + 1))
                continue
                
            if res.status_code == 200:
                data = res.json()
                if "results" in data and len(data["results"]) > 0:
                    # We'll take the first relevant structured result (movie or tv)
                    for item in data["results"]:
                        if item.get("media_type") in ["movie", "tv"]:
                            poster_path = item.get("poster_path")
                            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
                            release_date = item.get("release_date") or item.get("first_air_date", "Unknown")
                            overview = item.get("overview", "No plot available.")
                            return {"poster": poster_url, "release_date": release_date, "overview": overview}
            
            # If nothing returned or a non-429 error happened, act as not found
            break
        except Exception as e:
            # Sleep on network timeouts
            time.sleep(1)
            
    return {"poster": None, "release_date": "Unknown", "overview": "No detailed metadata found."}

if uploaded_files:
    if not api_key_gemini or not api_key_tmdb:
        st.warning("⚠️ Please provide both Google Gemini and TMDB API keys in the sidebar to proceed.")
    else:
        try:
            watched_list = []
            for uploaded_file in uploaded_files:
                data = json.load(uploaded_file)
                watched_list.extend(parse_watch_history(data))
            
            # Remove duplicates across multiple files
            watched_list = list(set(watched_list))
            st.success(f"✅ Successfully extracted {len(watched_list)} unique watched titles from your history!")
            
            if st.button("🔮 Generate Recommendations", type="primary", use_container_width=True):
                with st.status("🤖 Processing Recommendations...", expanded=True) as status:
                    status.write("Analyzing history and fetching top genres from TMDB...")
                    top_genres = get_top_genres(watched_list, api_key_tmdb, st_status_obj=status)
                    
                    if top_genres:
                        status.write(f"Identified Top Genres: **{', '.join(top_genres)}**")
                    else:
                        status.write("Could not identify specific top genres. Proceeding with raw history...")
                        
                    status.write("Sending data to Gemini to analyze Taste Profile...")
                    recommendations, raw_prompt = get_recommendations(watched_list, top_genres, user_prefs, api_key_gemini)
                    
                    if recommendations:
                        # Filter out any accidental dupes that Gemini might have included
                        filtered_recs = [rec for rec in recommendations if rec["title"] not in watched_list]
                        
                        # Sort by confidence descending
                        filtered_recs.sort(key=lambda x: x.get("confidence", 0), reverse=True)
                        
                        status.write(f"Successfully received and filtered {len(filtered_recs)} recommendations!")
                        status.write("Fetching metadata & posters from TMDB for each recommendation...")
                        
                        # Pre-fetch metadata so we can log it
                        for item in filtered_recs:
                            status.write(f"🔍 Fetching TMDB data for: **{item['title']}**...")
                            item['_meta'] = fetch_tmdb_metadata(item["title"], api_key_tmdb)
                            
                        status.update(label="✅ Generation Complete!", state="complete", expanded=False)
                    else:
                        status.update(label="❌ Failed to generate recommendations.", state="error", expanded=True)
                        filtered_recs = []
                
                if filtered_recs:
                    st.toast("Recommendations Generated!", icon="🎉")
                    st.header("Your Curated Watchlist")
                    
                    # Display results in a 2-column grid
                    cols_per_row = 2
                    
                    for i in range(0, len(filtered_recs), cols_per_row):
                        cols = st.columns(cols_per_row)
                        for j in range(cols_per_row):
                            if i + j < len(filtered_recs):
                                item = filtered_recs[i + j]
                                col = cols[j]
                                
                                # Fetch metadata for each recommendation
                                meta = item['_meta']
                                
                                with col:
                                    # Create the card wrapper using a st.container for better structural isolation
                                    card_container = st.container()
                                    with card_container:
                                        # Inject a div wrap to target via CSS
                                        st.markdown('<div class="rec-card-container">', unsafe_allow_html=True)
                                        
                                        inner_cols = st.columns([1, 2.5])
                                        with inner_cols[0]:
                                            if meta["poster"]:
                                                st.markdown(f'<img src="{meta["poster"]}" class="poster-img" width="100%">', unsafe_allow_html=True)
                                            else:
                                                st.markdown("🎥 <br> *No Poster Available*", unsafe_allow_html=True)
                                                
                                        with inner_cols[1]:
                                            year = meta["release_date"][:4] if len(meta["release_date"]) >= 4 and meta["release_date"] != "Unknown" else ""
                                            year_str = f" ({year})" if year else ""
                                            st.markdown(f'<div class="rec-title">{item["title"]}{year_str}</div>', unsafe_allow_html=True)
                                            
                                            # Confidence Badge Logic
                                            conf_score = item.get("confidence")
                                            conf_badge = ""
                                            if conf_score is not None:
                                                if conf_score >= 85:
                                                    conf_class = "conf-high"
                                                elif conf_score >= 70:
                                                    conf_class = "conf-med"
                                                else:
                                                    conf_class = "conf-low"
                                                conf_badge = f'<span class="confidence-badge {conf_class}">{conf_score}% Match</span>'
                                            
                                            st.markdown(f'**{item.get("type", "Media").upper()}** {conf_badge}', unsafe_allow_html=True)
                                            st.markdown(f'<div class="rec-reason">{item["reason"]}</div>', unsafe_allow_html=True)
                                            
                                            with st.expander("Show Plot Summary"):
                                                st.write(meta["overview"])
                                                
                                        st.markdown('</div>', unsafe_allow_html=True)
                                        
                    # Provide the raw prompt for the user to inspect and copy
                    if raw_prompt:
                        st.markdown("---")
                        with st.expander("View Raw Gemini Prompt"):
                            st.markdown("Here is the exact prompt sent to the Gemini API behind the scenes. You can copy it using the icon ranking in the top right of the block.")
                            st.code(raw_prompt, language="markdown")
        except Exception as e:
            st.error(f"Failed to process file: {e}")
else:
    st.info("⬆️ Upload your Trakt JSON export in the sidebar to get started.")
