# AI Personalized Watch Recommendations 🎬

An intelligent, visually stunning movie and TV show recommendation web application built with Python and Streamlit. By analyzing your Trakt.tv watch history and leveraging the power of Google Gemini (and Gemma!) alongside the TMDB API, this app curates highly personalized recommendations and evaluates your specific title interests.

## ✨ Features

- **Smart Taste Profiling Engine:** Upload your `watch_history.json` straight from Trakt. The app intelligently samples your history and uses concurrent TMDB API calls to build an accurate "Taste Profile" of your most frequently watched genres.
- **Dual-Tab Interface:**
  - **🎯 Check a Specific Title:** Wondering if you'll like a specific movie or show? Enter the title and get an AI-generated **Match Score (0-100%)** along with a personalized reason based on your taste profile. 
  - **🔮 Get Recommendations:** Generate a curated list of 20 *new* things to watch that fit your taste perfectly. The AI is strictly instructed to ensure *no* title from your watch history is ever recommended.
- **Smart Model Selector:** Dynamically switch between the best Google Gemini and Gemma AI models directly from the sidebar. Evaluate recommendations using `gemini-3.1-pro-preview`, `gemma-4-31b-it`, and more.
- **"If you like this..." (Similar Titles):** When checking a specific title, the AI also suggests 5 highly similar shows or movies complete with their own Match Percentages.
- **Smart "Watched" Indicator:** The app cross-references generated similar titles against your uploaded Trakt history. If you've already seen a suggested similar title, a `✅ (Watched)` indicator automatically appears next to it!
- **Rich Metadata & Modern UI:** Fetches movie/show posters, release dates, and plot summaries directly from TMDB. Features a sleek, responsive, glassmorphic dark theme with gradient animated backgrounds and dynamic confidence badges (`conf-high`, `conf-med`, `conf-low`).

## 🛠️ Tech Stack

- **Frontend / Framework:** [Streamlit](https://streamlit.io/)
- **AI / LLM SDK:** [Google GenAI Python SDK](https://github.com/google/generative-ai-python)
- **Metadata API:** [TMDB API (The Movie Database)](https://www.themoviedb.org/documentation/api)
- **Environment Management:** `python-dotenv`
- **Concurrency:** `concurrent.futures.ThreadPoolExecutor`

## 🚀 Getting Started

### Prerequisites

You will need Python 3 installed, active API keys for both Google Gemini and TMDB, and your Trakt.tv watch history.

1.  **Get a TMDB API Key:** Register at [The Movie Database](https://www.themoviedb.org/) and request an API key from your account settings.
2.  **Get a Gemini API Key:** Obtain an API key from [Google AI Studio](https://aistudio.google.com/).
3.  **Export Trakt History:** Export your viewing history from [Trakt.tv](https://trakt.tv/) as a JSON file and have `watch_history.json` ready.

### Installation

1.  **Clone the repository** (or download the source code).
    ```bash
    git clone <your-repo-url>
    cd <your-repo-directory>
    ```

2.  **Create a virtual environment (optional but highly recommended)**
    ```bash
    python -m venv venv
    # On Windows:
    venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate
    ```

3.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables**
    Create a `.env` file in the root directory and add your API keys:
    ```env
    TMDB_API_KEY=your_tmdb_api_key_here
    GEMINI_API_KEY=your_gemini_api_key_here
    ```

### Running the Application

Run the Streamlit application using the following command:

```bash
streamlit run app.py
```

The application will open automatically in your default web browser (usually at `http://localhost:8501`).

## 📖 How to Use

1. **Upload History:** Export your viewing history from Trakt.tv in JSON format (`watch_history.json`) and upload it securely via the app's sidebar.
2. **Select AI Model:** Choose your preferred AI model from the sidebar dropdown (e.g., `gemini-3.1-pro-preview` or `gemma-4-31b-it`).
3. **Analyze Taste:** Click the **🧠 Analyze My Taste** button to let the app securely process your history against TMDB and build your profile.
4. **Choose a Feature Tab:**
   - **Tab 1:** Enter a specific title to get a match score and see 5 similar titles.
   - **Tab 2:** Add any optional preferences (like "Anime" or "90s Thriller") and click **🔮 Generate Recommendations** for a fresh batch of 20 personalized shows/movies.

## 🤝 Contributing

Contributions, issues, and feature requests are always welcome! Feel free to open an issue or submit a Pull Request.

## 📄 License

This project is open-source and available under the terms of the [MIT License](LICENSE).
