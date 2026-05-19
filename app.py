import streamlit as st
import json
import os
import requests
import httpx
import random
import time
import hashlib
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

    /* Similar titles section */
    .similar-section-header {
        font-size: 1.05rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 0.75rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid rgba(255,255,255,0.1);
    }
    .sim-card {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 10px;
        padding: 0.6rem 0.9rem;
        margin-bottom: 0.45rem;
        transition: background 0.2s ease, border 0.2s ease, transform 0.15s ease;
    }
    .sim-card:hover {
        background: rgba(255,255,255,0.08);
        border-color: rgba(255,255,255,0.2);
        transform: translateX(4px);
    }
    .sim-card-left {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        flex: 1;
        min-width: 0;
    }
    .sim-card-title {
        font-size: 0.95rem;
        font-weight: 600;
        color: #e8e8e8;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .sim-card-right {
        display: flex;
        align-items: center;
        gap: 0.4rem;
        flex-shrink: 0;
    }
    .sim-score-slot {
        width: 42px;
        text-align: center;
    }
    .sim-watched-slot {
        width: 80px;
        text-align: center;
    }
    .sim-match-pill {
        font-size: 0.72rem;
        font-weight: 600;
        padding: 0.15rem 0.5rem;
        border-radius: 20px;
        white-space: nowrap;
        display: inline-block;
    }
    .sim-match-high { background: rgba(46,204,113,0.15); color: #2ecc71; border: 1px solid rgba(46,204,113,0.3); }
    .sim-match-med  { background: rgba(241,196,15,0.15); color: #f1c40f; border: 1px solid rgba(241,196,15,0.3); }
    .sim-match-low  { background: rgba(231,76,60,0.15);  color: #e74c3c; border: 1px solid rgba(231,76,60,0.3); }
    .sim-watched-tag {
        font-size: 0.7rem;
        font-weight: 600;
        padding: 0.12rem 0.45rem;
        border-radius: 20px;
        background: rgba(46,204,113,0.12);
        color: #2ecc71;
        border: 1px solid rgba(46,204,113,0.25);
        white-space: nowrap;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

st.title("🎬 AI Personalized Watch Recommendations")
st.markdown("Upload your Trakt `watch_history.json` and ratings files, and let Gemini orchestrate your next binge!")

# Sidebar for API Keys and File Upload
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key_gemini = st.text_input("Google Gemini API Key", value=GEMINI_API_KEY if GEMINI_API_KEY else "", type="password")
    api_key_tmdb = st.text_input("TMDB API Key", value=TMDB_API_KEY if TMDB_API_KEY else "", type="password")
    
    AVAILABLE_MODELS = [
        "gemini-3.1-pro-preview",
        "gemini-3-pro-preview",
        "gemini-2.5-pro",
        "gemma-4-31b-it",
        "gemma-4-26b-a4b-it",
        "gemma-3-27b-it",
        "gemini-3-flash-preview",
        "gemini-2.5-flash"
    ]
    selected_model = st.selectbox("🤖 Select AI Model", AVAILABLE_MODELS, index=0)
    
    st.header("📁 Upload History Data")
    uploaded_files = st.file_uploader("Upload Trakt watch_history.json", type=["json"], accept_multiple_files=True)
    
    st.header("⭐ Upload Ratings Data")
    ratings_files = st.file_uploader("Upload Trakt ratings JSON files (ratings-shows.json, etc.)", type=["json"], accept_multiple_files=True)

def parse_watch_history(data):
    """Parses the Trakt history JSON and extracts unique movie/show titles."""
    watched_titles = set()
    for item in data:
        if item.get("type") == "episode" and "show" in item:
            watched_titles.add(item["show"]["title"])
        elif item.get("type") == "movie" and "movie" in item:
            watched_titles.add(item["movie"]["title"])
    return list(watched_titles)

def parse_ratings(data):
    """Parses Trakt ratings JSON and extracts titles and their scores."""
    ratings = {}
    for item in data:
        if "rating" in item:
            title = None
            if item.get("type") == "episode" and "show" in item:
                title = item["show"]["title"]
            elif item.get("type") == "show" and "show" in item:
                title = item["show"]["title"]
            elif item.get("type") == "movie" and "movie" in item:
                title = item["movie"]["title"]
            if title:
                ratings[title] = item["rating"]
    return ratings

def build_context_list(watched_list, ratings_dict, limit=500):
    """Builds a string of watched titles, prioritizing rated ones and appending scores."""
    rated_titles = []
    for title, rating in ratings_dict.items():
        if title in watched_list:
            rated_titles.append(f"{title} ({rating}/10)")
        else:
            # If they rated it but it's not in watch history for some reason, still include it
            rated_titles.append(f"{title} ({rating}/10)")
            
    remaining_slots = limit - len(rated_titles)
    unrated_titles = [t for t in watched_list if t not in ratings_dict]
    
    if remaining_slots > 0:
        sampled_unrated = random.sample(unrated_titles, min(len(unrated_titles), remaining_slots))
        context_list = rated_titles + sampled_unrated
    else:
        context_list = rated_titles
        
    random.shuffle(context_list) # Shuffle to avoid bias based on ordering
    return ", ".join(context_list)

# A small cache/mapping of TMDB Genre IDs to Names
TMDB_GENRES = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy", 80: "Crime", 
    99: "Documentary", 18: "Drama", 10751: "Family", 14: "Fantasy", 36: "History", 
    27: "Horror", 10402: "Music", 9648: "Mystery", 10749: "Romance", 878: "Science Fiction", 
    10770: "TV Movie", 53: "Thriller", 10752: "War", 37: "Western",
    10759: "Action & Adventure", 10762: "Kids", 10763: "News", 10764: "Reality", 
    10765: "Sci-Fi & Fantasy", 10766: "Soap", 10767: "Talk", 10768: "War & Politics"
}

def get_top_genres(watched_list, tmdb_key, st_status_obj=None, sample_size=200, top_n=5):
    """Fetches genre IDs concurrently from TMDB and returns the top N genres."""
    sampled_list = random.sample(watched_list, min(len(watched_list), sample_size))
    genre_counts = Counter()

    def fetch_genre_for_title(title):
        url = f"https://api.themoviedb.org/3/search/multi?api_key={tmdb_key}&query={title}"
        for attempt in range(3):
            try:
                res = requests.get(url, timeout=5)
                if res.status_code == 429:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                if res.status_code == 200:
                    data = res.json()
                    if "results" in data and len(data["results"]) > 0:
                        for item in data["results"]:
                            if item.get("media_type") in ["movie", "tv"] and "genre_ids" in item:
                                return item["genre_ids"]
                break
            except Exception:
                time.sleep(1)
        return []

    results = []
    if st_status_obj:
        progress_bar = st_status_obj.progress(0, text="Fetching genres from TMDB...")
        completed_count = 0
        total_count = len(sampled_list)

    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        future_to_title = {executor.submit(fetch_genre_for_title, title): title for title in sampled_list}
        for future in concurrent.futures.as_completed(future_to_title):
            title = future_to_title[future]
            try:
                ids = future.result()
                results.append(ids)
            except Exception:
                pass
            finally:
                if st_status_obj:
                    completed_count += 1
                    progress_text = f"Analyzed {completed_count}/{total_count} titles... (Just checked: {title})"
                    progress_bar.progress(completed_count / total_count, text=progress_text)
                    
    if st_status_obj:
        progress_bar.empty()

    for ids in results:
        if ids:
            for genre_id in ids:
                if genre_id in TMDB_GENRES:
                    genre_counts[TMDB_GENRES[genre_id]] += 1

    return [genre for genre, count in genre_counts.most_common(top_n)]
    

def get_recommendations(watched_list, ratings_dict, top_genres, user_preferences, gemini_key, model_name):
    client = genai.Client(api_key=gemini_key)
    
    watched_str = build_context_list(watched_list, ratings_dict, limit=500)
    genres_str = ", ".join(top_genres) if top_genres else "Unknown"
    pref_instruction = f"\nUSER SPECIFIC PREFERENCE: The user has requested: '{user_preferences}'. You MUST heavily bias your recommendations to fit this specific preference above all else.\n" if user_preferences else ""
    
    prompt = f"""You are an expert movie and TV show recommender.
Here is a list of movies and TV shows the user has watched, along with their personal ratings out of 10.

[WATCHED LIST START]
{watched_str}
[WATCHED LIST END]

USER TASTE PROFILE (Based on history):
Their most frequently watched genres are: {genres_str}.
{pref_instruction}
TASK:
1. Analyze this viewing history, ratings, and genre preference to understand their taste.
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
    "reason": "3-4 sentence detailed explanation of why this fits their specific taste profile perfectly.",
    "confidence": 92,
    "verdict": "A must-watch for you!" or "Watch it if you're in the mood." or "You might want to skip this one."
  }}
]
"""
    try:
        response = client.models.generate_content(model=model_name, contents=prompt)
        text = response.text.strip()
        if text.startswith("```json"): text = text[7:]
        if text.startswith("```"): text = text[3:]
        if text.endswith("```"): text = text[:-3]
        return json.loads(text.strip()), prompt
    except Exception as e:
        st.error(f"Error communicating with Gemini: {e}")
        try: st.error(f"Raw response was: {response.text}")
        except: pass
        return None, prompt

def check_title_match(title, watched_list, ratings_dict, top_genres, gemini_key, model_name):
    client = genai.Client(api_key=gemini_key)
    
    watched_str = build_context_list(watched_list, ratings_dict, limit=500)
    genres_str = ", ".join(top_genres) if top_genres else "Unknown"
    
    prompt = f"""You are an expert movie and TV show recommender.
The user wants to know if the title "{title}" matches their taste.

Here is a list of movies and TV shows the user has already watched, along with their ratings out of 10.
[WATCHED LIST START]
{watched_str}
[WATCHED LIST END]

USER TASTE PROFILE:
Their most frequently watched genres are: {genres_str}.

TASK:
1. Analyze if "{title}" fits this taste profile based on their watch history and genre preferences.
2. Provide a match score (0-100) and a 9-10 sentence reason.
3. Determine if it's a Movie or TV Show.
4. Suggest exactly 5 shows or movies that are highly similar to "{title}".

FORMAT REQUIREMENT:
Provide your response in valid JSON format ONLY. Ensure the JSON is properly escaped.
It must follow this exact structure:
{{
  "title": "{title}",
  "type": "Movie" or "TV Show",
  "reason": "9-10 sentence detailed explanation of why this fits or doesn't fit their taste profile.",
  "confidence": 85,
  "verdict": "You should definitely watch this!" or "You should probably skip this one.",
  "similar_titles": [
    {{"title": "Similar Title 1", "match_score": 88}},
    {{"title": "Similar Title 2", "match_score": 75}},
    {{"title": "Similar Title 3", "match_score": 92}},
    {{"title": "Similar Title 4", "match_score": 65}},
    {{"title": "Similar Title 5", "match_score": 80}}
  ]
}}
"""
    try:
        response = client.models.generate_content(model=model_name, contents=prompt)
        text = response.text.strip()
        if text.startswith("```json"): text = text[7:]
        if text.startswith("```"): text = text[3:]
        if text.endswith("```"): text = text[:-3]
        return json.loads(text.strip()), prompt
    except Exception as e:
        st.error(f"Error communicating with Gemini: {e}")
        return None, prompt

def fetch_tmdb_metadata(title, tmdb_key):
    url = f"https://api.themoviedb.org/3/search/multi?api_key={tmdb_key}&query={title}"
    for attempt in range(3):
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 429:
                time.sleep(1 * (attempt + 1))
                continue
            if res.status_code == 200:
                data = res.json()
                if "results" in data and len(data["results"]) > 0:
                    for item in data["results"]:
                        if item.get("media_type") in ["movie", "tv"]:
                            poster_path = item.get("poster_path")
                            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
                            release_date = item.get("release_date") or item.get("first_air_date", "Unknown")
                            overview = item.get("overview", "No plot available.")
                            return {"poster": poster_url, "release_date": release_date, "overview": overview}
            break
        except Exception:
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
            watched_list = list(set(watched_list))
            
            ratings_dict = {}
            if ratings_files:
                for r_file in ratings_files:
                    # Seek to 0 in case file pointer is at EOF from a previous read
                    r_file.seek(0)
                    data = json.load(r_file)
                    ratings_dict.update(parse_ratings(data))
                    
            st.success(f"✅ Extracted {len(watched_list)} watched titles and {len(ratings_dict)} ratings!")
            
            # Compute Content Hash
            content_hash_str = "".join(sorted(watched_list)) + "".join([f"{k}{v}" for k,v in sorted(ratings_dict.items())])
            current_hash = hashlib.md5(content_hash_str.encode()).hexdigest()
            cache_file = ".taste_cache.json"
            
            # Smart Caching Check
            if st.session_state.get('current_hash') != current_hash:
                if os.path.exists(cache_file):
                    with open(cache_file, "r") as f:
                        cache_data = json.load(f)
                        if cache_data.get("hash") == current_hash:
                            st.session_state.top_genres = cache_data.get("top_genres", [])
                            st.session_state.watched_list = watched_list
                            st.session_state.ratings_dict = ratings_dict
                            st.session_state.current_hash = current_hash
                            st.session_state.taste_analyzed = True
                            st.toast("Loaded Taste Profile from local cache!", icon="⚡")
            
            btn_label = "🔄 Re-Analyze My Taste (Ignore Cache)" if st.session_state.get('taste_analyzed') else "🧠 Analyze My Taste"
            
            if st.button(btn_label, type="primary"):
                with st.status("🤖 Analyzing history and fetching top genres from TMDB...", expanded=True) as status:
                    top_genres = get_top_genres(watched_list, api_key_tmdb, st_status_obj=status)
                    st.session_state.top_genres = top_genres
                    st.session_state.watched_list = watched_list
                    st.session_state.ratings_dict = ratings_dict
                    st.session_state.current_hash = current_hash
                    st.session_state.taste_analyzed = True
                    
                    # Save to cache
                    with open(cache_file, "w") as f:
                        json.dump({
                            "hash": current_hash,
                            "top_genres": top_genres
                        }, f)
                    
                    status.update(label="✅ Taste Analysis Complete & Cached!", state="complete", expanded=False)
                st.rerun()
            
            if st.session_state.get('taste_analyzed'):
                top_genres = st.session_state.top_genres
                if top_genres:
                    st.info(f"🎭 **Identified Top Genres:** {', '.join(top_genres)}")
                else:
                    st.info("🎭 Could not identify specific top genres. Proceeding with raw history...")
                    
                tab1, tab2 = st.tabs(["🎯 Check a Specific Title", "🔮 Get Recommendations"])
                
                with tab1:
                    st.header("Check Title Match")
                    st.markdown("Enter a movie or TV show to see how well it matches your taste!")
                    
                    search_title = st.text_input("Title", placeholder="e.g., Inception, Breaking Bad")
                    if st.button("Check Match"):
                        if search_title:
                            with st.spinner(f"Evaluating '{search_title}'... (Estimated time: ~5-10 seconds)"):
                                match_result, raw_prompt = check_title_match(search_title, watched_list, ratings_dict, top_genres, api_key_gemini, selected_model)
                                if match_result:
                                    meta = fetch_tmdb_metadata(search_title, api_key_tmdb)
                                    
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
                                        st.markdown(f'<div class="rec-title">{match_result.get("title", search_title)}{year_str}</div>', unsafe_allow_html=True)
                                        
                                        conf_score = match_result.get("confidence")
                                        conf_badge = ""
                                        if conf_score is not None:
                                            conf_class = "conf-high" if conf_score >= 85 else "conf-med" if conf_score >= 70 else "conf-low"
                                            conf_badge = f'<span class="confidence-badge {conf_class}">{conf_score}% Match</span>'
                                        
                                        st.markdown(f'**{match_result.get("type", "Media").upper()}** {conf_badge}', unsafe_allow_html=True)
                                        
                                        verdict_text = match_result.get("verdict", "")
                                        if verdict_text:
                                            verdict_emoji = "🟢" if conf_score and conf_score >= 85 else "🟡" if conf_score and conf_score >= 70 else "🔴"
                                            st.markdown(f"{verdict_emoji} **{verdict_text}**")
                                        
                                        st.markdown(f'<div class="rec-reason">{match_result.get("reason", "")}</div>', unsafe_allow_html=True)
                                        
                                        with st.expander("Show Plot Summary"):
                                            st.write(meta["overview"])
                                            
                                        if "similar_titles" in match_result and match_result["similar_titles"]:
                                            st.markdown("---")
                                            st.markdown('<div class="similar-section-header">🍿 If you like this, you might also like:</div>', unsafe_allow_html=True)
                                            watched_lower = {title.lower() for title in watched_list}
                                            sim_cards_html = ""
                                            for sim_item in match_result["similar_titles"]:
                                                sim_title = sim_item.get("title") if isinstance(sim_item, dict) else sim_item
                                                match_score = sim_item.get("match_score") if isinstance(sim_item, dict) else None
                                                is_watched = sim_title.lower() in watched_lower
                                                pill_html = ""
                                                if match_score:
                                                    pill_class = "sim-match-high" if match_score >= 85 else "sim-match-med" if match_score >= 70 else "sim-match-low"
                                                    pill_html = f'<span class="sim-match-pill {pill_class}">{match_score}%</span>'
                                                watched_html = '<span class="sim-watched-tag">✅ Watched</span>' if is_watched else ""
                                                sim_cards_html += f'<div class="sim-card"><div class="sim-card-left"><span class="sim-card-title">{sim_title}</span></div><div class="sim-card-right"><div class="sim-score-slot">{pill_html}</div><div class="sim-watched-slot">{watched_html}</div></div></div>'
                                            st.markdown(sim_cards_html, unsafe_allow_html=True)
                                                
                                    st.markdown('</div>', unsafe_allow_html=True)
                                    
                                    # Provide the raw prompt for Check Title Match
                                    if raw_prompt:
                                        st.markdown("---")
                                        with st.expander("View Raw Gemini Prompt"):
                                            st.markdown("Here is the exact prompt sent to the Gemini API behind the scenes.")
                                            st.code(raw_prompt, language="markdown")
                        else:
                            st.warning("Please enter a title to check.")
                
                with tab2:
                    st.header("Get Recommendations")
                    st.markdown("##### ✨ Preferences (Optional)")
                    user_prefs = st.text_input("Any specific mood or genre today?", placeholder="e.g., Anime, Rom Com, 90s action")
                    
                    if st.button("🔮 Generate Recommendations", type="primary", use_container_width=True):
                        with st.status("🤖 Processing Recommendations... (Estimated time: ~20-35 seconds)", expanded=True) as status:
                            status.write("Sending data to Gemini to analyze Taste Profile...")
                            recommendations, raw_prompt = get_recommendations(watched_list, ratings_dict, top_genres, user_prefs, api_key_gemini, selected_model)
                            
                            if recommendations:
                                filtered_recs = [rec for rec in recommendations if rec["title"] not in watched_list]
                                filtered_recs.sort(key=lambda x: x.get("confidence", 0), reverse=True)
                                status.write(f"Successfully received and filtered {len(filtered_recs)} recommendations!")
                                status.write("Fetching metadata & posters from TMDB for each recommendation...")
                                
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
                            
                            cols_per_row = 2
                            for i in range(0, len(filtered_recs), cols_per_row):
                                cols = st.columns(cols_per_row)
                                for j in range(cols_per_row):
                                    if i + j < len(filtered_recs):
                                        item = filtered_recs[i + j]
                                        col = cols[j]
                                        meta = item['_meta']
                                        
                                        with col:
                                            card_container = st.container()
                                            with card_container:
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
                                                    
                                                    conf_score = item.get("confidence")
                                                    conf_badge = ""
                                                    if conf_score is not None:
                                                        conf_class = "conf-high" if conf_score >= 85 else "conf-med" if conf_score >= 70 else "conf-low"
                                                        conf_badge = f'<span class="confidence-badge {conf_class}">{conf_score}% Match</span>'
                                                    
                                                    st.markdown(f'**{item.get("type", "Media").upper()}** {conf_badge}', unsafe_allow_html=True)
                                                    
                                                    verdict_text = item.get("verdict", "")
                                                    if verdict_text:
                                                        verdict_emoji = "🟢" if conf_score and conf_score >= 85 else "🟡" if conf_score and conf_score >= 70 else "🔴"
                                                        st.markdown(f"{verdict_emoji} **{verdict_text}**")
                                                    
                                                    st.markdown(f'<div class="rec-reason">{item["reason"]}</div>', unsafe_allow_html=True)
                                                    
                                                    with st.expander("Show Plot Summary"):
                                                        st.write(meta["overview"])
                                                        
                                                st.markdown('</div>', unsafe_allow_html=True)
                                                
                            if raw_prompt:
                                st.markdown("---")
                                with st.expander("View Raw Gemini Prompt"):
                                    st.markdown("Here is the exact prompt sent to the Gemini API behind the scenes. You can copy it using the icon ranking in the top right of the block.")
                                    st.code(raw_prompt, language="markdown")
        except Exception as e:
            st.error(f"Failed to process file: {e}")
else:
    st.info("⬆️ Upload your Trakt JSON export in the sidebar to get started.")
