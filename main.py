from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv
import httpx
import re
import random
from prompts.movies import create_recommendation_prompt
import asyncio
from typing import List, Optional

# Load environment variables
load_dotenv()

# Get API keys from environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

if not GROQ_API_KEY or not TMDB_API_KEY:
    raise ValueError("Missing required API keys")

# Initialize the model
model = ChatGroq(model="mixtral-8x7b-32768", api_key=GROQ_API_KEY)  # Using Mixtral model

# Define FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://filmyfim.vercel.app",
        "https://www.filmyfim.vercel.app",
        "https://filmyfim-git-main-shahinzam.vercel.app",
        "https://filmyfim-shahinzam.vercel.app",
        "https://your-production-domain.com",
        "file://"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# اضافه کردن middleware برای اطمینان از CORS
@app.middleware("http")
async def add_cors_headers(request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

# Expanded genre categories with more variety
GENRES = {
    "Action": 28,
    "Adventure": 12,
    "Animation": 16,
    "Comedy": 35,
    "Crime": 80,
    "Documentary": 99,
    "Drama": 18,
    "Family": 10751,
    "Fantasy": 14,
    "Horror": 27,
    "Musical": 10402,
    "Mystery": 9648,
    "Romance": 10749,
    "Science Fiction": 878,
    "Thriller": 53,
    "War": 10752
}

# Genre combinations that are very different from each other
DIVERSE_GENRE_SETS = [
    # Set 1: Action/Drama/Animation
    ["Action", "Drama", "Animation"],
    # Set 2: Comedy/Horror/Sci-Fi
    ["Comedy", "Horror", "Science Fiction"],
    # Set 3: Romance/Thriller/Fantasy
    ["Romance", "Thriller", "Fantasy"],
    # Set 4: Mystery/Family/War
    ["Mystery", "Family", "War"],
    # Set 5: Adventure/Crime/Musical
    ["Adventure", "Crime", "Musical"]
]

async def translate_to_persian(text: str, model: ChatGroq) -> str:
    """Translate text to natural and fluent Persian"""
    try:
        prompt = f"""به عنوان یک مترجم حرفه‌ای فیلم، این متن را به فارسی روان و ساده ترجمه کن.
        - از اصطلاحات رایج فارسی استفاده کن
        - جملات باید طبیعی و روان باشند
        - از کلمات ساده و قابل فهم استفاده کن
        - نام فیلم‌ها را به انگلیسی نگه دار
        
        متن اصلی: {text}"""
        
        response = model.invoke(prompt)
        return response.content.strip()
    except Exception as e:
        print(f"Translation error: {str(e)}")
        return text

async def get_movie_details(title: str, model: ChatGroq) -> dict:
    """Get movie details from TMDB API with Persian translation"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        cleaned_title = re.sub(r'[^\w\s]', '', title).strip()
        
        search_url = f"https://api.themoviedb.org/3/search/movie"
        params = {
            "api_key": TMDB_API_KEY,
            "query": cleaned_title,
            "language": "en-US",
            "page": 1
        }
        
        try:
            response = await client.get(search_url, params=params)
            data = response.json()
            
            if not data.get("results"):
                return {
                    "name": title,
                    "score": 0,
                    "description": await translate_to_persian("No information available", model),
                    "description_en": "No information available",
                    "image": None,
                    "imdb_id": None
                }
            
            movie = data["results"][0]
            
            # Get IMDB ID
            movie_id = movie["id"]
            details_url = f"https://api.themoviedb.org/3/movie/{movie_id}"
            details_response = await client.get(details_url, params={"api_key": TMDB_API_KEY})
            details_data = details_response.json()
            imdb_id = details_data.get("imdb_id")
            
            description_en = movie["overview"] or "No description available"
            description_fa = await translate_to_persian(description_en, model)
            
            return {
                "name": movie["title"],
                "score": round(movie["vote_average"], 1),
                "description": description_fa,
                "description_en": description_en,
                "image": f"https://image.tmdb.org/t/p/w500{movie['poster_path']}" if movie.get('poster_path') else None,
                "imdb_id": imdb_id
            }
        except Exception as e:
            print(f"Error fetching details for {title}: {str(e)}")
            return {
                "name": title,
                "score": 0,
                "description": await translate_to_persian("Error fetching movie details", model),
                "description_en": "Error fetching movie details",
                "image": None,
                "imdb_id": None
            }

async def get_top_movie_by_genre(genre_id: int, exclude_movies: list = None, model: ChatGroq = None) -> dict:
    """Get a top-rated movie from a specific genre, excluding certain movies"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        url = "https://api.themoviedb.org/3/discover/movie"
        params = {
            "api_key": TMDB_API_KEY,
            "with_genres": genre_id,
            "sort_by": "popularity.desc",
            "vote_count.gte": 1000,
            "vote_average.gte": 7.0,
            "page": random.randint(1, 3)
        }
        
        response = await client.get(url, params=params)
        data = response.json()
        
        if data.get("results"):
            available_movies = [
                movie for movie in data["results"][:10]
                if not exclude_movies or movie["title"] not in exclude_movies
            ]
            
            if available_movies:
                movie = random.choice(available_movies)
                description_en = movie["overview"]
                description_fa = await translate_to_persian(description_en, model) if model else description_en
                
                return {
                    "name": movie["title"],
                    "score": round(movie["vote_average"], 1),
                    "description": description_fa,
                    "description_en": description_en,
                    "image": f"https://image.tmdb.org/t/p/w500{movie['poster_path']}" if movie.get('poster_path') else None,
                    "genre": next(name for name, id in GENRES.items() if id == genre_id)
                }
        return None

@app.get("/featured-movies")
async def get_featured_movies():
    """Get three diverse movies from different genres"""
    try:
        genre_set = random.choice(DIVERSE_GENRE_SETS)
        movies = []
        used_movies = set()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            tasks = []
            for genre_name in genre_set:
                genre_id = GENRES[genre_name]
                tasks.append(get_top_movie_by_genre(genre_id, list(used_movies), model))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, dict) and result["name"] not in used_movies:
                    movies.append(result)
                    used_movies.add(result["name"])
        
        return {"movies": movies[:3]}
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Define a request schema
class MovieRequest(BaseModel):
    movie_title: str

@app.post("/recommend")
async def get_movie_recommendations(request: MovieRequest):
    try:
        prompt = create_recommendation_prompt(request.movie_title)
        response = model.invoke(prompt)
        
        lines = response.content.strip().split('\n')
        movie_titles = []
        
        for line in lines:
            clean_line = re.sub(r'^\d+[\.\)\-]\s*', '', line.strip())
            clean_line = re.sub(r'^[-•*]\s*', '', clean_line)
            clean_line = re.sub(r'\([^)]*\)', '', clean_line)
            clean_line = clean_line.strip()
            if clean_line and not clean_line.lower().startswith(('similar', 'recommended')):
                movie_titles.append(clean_line)
        
        movie_titles = movie_titles[:6]
        
        movies_with_details = []
        for title in movie_titles:
            details = await get_movie_details(title, model)
            if details:
                movies_with_details.append(details)
        
        while len(movies_with_details) < 6:
            original_movie = await get_movie_details(request.movie_title, model)
            if original_movie:
                genre_id = random.choice(list(GENRES.values()))
                additional_movie = await get_top_movie_by_genre(genre_id, [m['name'] for m in movies_with_details], model)
                if additional_movie:
                    movies_with_details.append(additional_movie)
        
        return {
            "recommendations": movies_with_details
        }
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        print(f"Raw AI response: {response.content if 'response' in locals() else 'No response'}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"status": "ok", "message": "Server is running"}
