# AI Personalized Watch Recommendations 🎬

An intelligent, visually stunning movie and TV show recommendation web application built with Python and Streamlit. By analyzing your Trakt.tv watch history and leveraging the power of Google Gemini and the TMDB API, this app curates a highly personalized list of 20 *new* things to watch that you haven't seen before.

https://github.com/kuzhagan143/AI_Personalized_Watch_Recommendations/blob/main/Screenshot/Screenshot%20%20(1).png?raw=true
https://github.com/kuzhagan143/AI_Personalized_Watch_Recommendations/blob/main/Screenshot/Screenshot%20%20(2).png?raw=true

## ✨ Features

- **Trakt.tv Integration:** Upload your `history-1.json` straight from Trakt to analyze your viewing habits.
- **Smart Taste Profiling:** Automatically identifies your most frequently watched genres using TMDB.
- **AI-Powered Discovery:** Uses Google Gemini (`gemini-3-flash-preview`) to generate 20 highly relevant recommendations based on your unique taste profile.
- **Strictly No Duplicates:** The AI is strictly instructed to ensure *no* title from your watch history is ever recommended to you.
- **Custom Preferences:** Feeling like a specific genre today? Enter custom prompts like "Anime", "Rom Com", or "90s action" to heavily bias your recommendations.
- **Rich Metadata:** Fetches movie/show posters, release dates, and plot summaries directly from TMDB.
- **Modern UI:** Features a sleek, responsive, glassmorphic dark theme with gradient animated backgrounds and dynamic hover effects.

## 🛠️ Tech Stack

- **Frontend / Framework:** [Streamlit](https://streamlit.io/)
- **AI / LLM API:** [Google GenAI (Gemini)](https://ai.google.dev/)
- **Metadata API:** [TMDB API (The Movie Database)](https://www.themoviedb.org/documentation/api)
- **Environment Management:** `python-dotenv`
- **HTTP Requests:** `requests`

## 🚀 Getting Started

### Prerequisites

You will need Python 3 installed, active API keys for both Google Gemini and TMDB, and your Trakt.tv watch history.

1.  **Get a TMDB API Key:** Register at [The Movie Database](https://www.themoviedb.org/) and request an API key from your account settings.
2.  **Get a Gemini API Key:** Obtain an API key from [Google AI Studio](https://aistudio.google.com/).
3.  **Export Trakt History:** Export your viewing history from [Trakt.tv](https://trakt.tv/) as a JSON file and have `history-1.json, history-2.json,..` ready.

### Installation

1.  **Clone the repository** (or download the source code).
    ```bash
    git clone https://github.com/kuzhagan143/AI_Personalized_Watch_Recommendations.git
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
    Create a `.env` file in the root directory (you can use `.env.example` as a template if one exists) and add your API keys:
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

1. **Upload History:** Export your viewing history from Trakt.tv in JSON format (`history-1.json, history-2.json,..`) and upload it securely via the app's sidebar.
2. **API Keys (Fallback):** If you skipped setting up the `.env` file, you can enter your TMDB and Gemini API keys directly into the provided sidebar inputs.
3. **Set Preferences:** (Optional) Add any specific mood or genre in the preferences input box before generating suggestions.
4. **Generate:** Click **"🔮 Generate Recommendations"** and wait for the AI to curate your personalized watchlist!
5. **Explore:** Browse the recommended titles. You can view AI confidence scores, read personalized reasons for the recommendation, and expand plot summaries.

## 🤝 Contributing

Contributions, issues, and feature requests are always welcome! Feel free to open an issue or submit a Pull Request.
