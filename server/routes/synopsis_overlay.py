from flask import Blueprint, jsonify, request
from .security import require_api_key
import requests
import os
from typing import Dict, List, Optional

synopsis_bp = Blueprint('synopsis', __name__)

# TMDB API configuration
TMDB_API_KEY = os.getenv('TMDB_API_KEY', 'your_tmdb_api_key_here')
TMDB_BASE_URL = 'https://api.themoviedb.org/3'
TMDB_IMAGE_BASE = 'https://image.tmdb.org/t/p'

class TMDBClient:
    """Client for TMDB API integration"""
    
    @staticmethod
    def search_movie(query: str, year: Optional[int] = None) -> Dict:
        """Search for a movie"""
        params = {
            'api_key': TMDB_API_KEY,
            'query': query,
            'language': 'en-US',
            'page': 1
        }
        if year:
            params['year'] = year
            
        response = requests.get(f'{TMDB_BASE_URL}/search/movie', params=params)
        return response.json()
    
    @staticmethod
    def search_tv(query: str, year: Optional[int] = None) -> Dict:
        """Search for a TV show"""
        params = {
            'api_key': TMDB_API_KEY,
            'query': query,
            'language': 'en-US',
            'page': 1
        }
        if year:
            params['first_air_date_year'] = year
            
        response = requests.get(f'{TMDB_BASE_URL}/search/tv', params=params)
        return response.json()
    
    @staticmethod
    def get_movie_details(movie_id: int) -> Dict:
        """Get detailed movie information"""
        params = {
            'api_key': TMDB_API_KEY,
            'language': 'en-US',
            'append_to_response': 'credits,videos,similar,keywords,release_dates'
        }
        response = requests.get(f'{TMDB_BASE_URL}/movie/{movie_id}', params=params)
        return response.json()
    
    @staticmethod
    def get_tv_details(tv_id: int) -> Dict:
        """Get detailed TV show information"""
        params = {
            'api_key': TMDB_API_KEY,
            'language': 'en-US',
            'append_to_response': 'credits,videos,similar,keywords,content_ratings'
        }
        response = requests.get(f'{TMDB_BASE_URL}/tv/{tv_id}', params=params)
        return response.json()
    
    @staticmethod
    def get_person_details(person_id: int) -> Dict:
        """Get person (actor/director) details"""
        params = {
            'api_key': TMDB_API_KEY,
            'language': 'en-US',
            'append_to_response': 'combined_credits,images'
        }
        response = requests.get(f'{TMDB_BASE_URL}/person/{person_id}', params=params)
        return response.json()

class SynopsisFormatter:
    """Format TMDB data for synopsis overlay"""
    
    @staticmethod
    def format_movie(data: Dict) -> Dict:
        """Format movie data for frontend"""
        credits = data.get('credits', {})
        videos = data.get('videos', {}).get('results', [])
        
        # Get trailer
        trailer = next((v for v in videos if v['type'] == 'Trailer' and v['site'] == 'YouTube'), None)
        
        # Format cast
        cast = [
            {
                'id': person['id'],
                'name': person['name'],
                'character': person.get('character', ''),
                'profile_path': f"{TMDB_IMAGE_BASE}/w185{person['profile_path']}" if person.get('profile_path') else None
            }
            for person in credits.get('cast', [])[:10]  # Top 10 cast
        ]
        
        # Format crew (directors, writers)
        directors = [
            {'id': person['id'], 'name': person['name']}
            for person in credits.get('crew', [])
            if person['job'] == 'Director'
        ]
        
        writers = [
            {'id': person['id'], 'name': person['name']}
            for person in credits.get('crew', [])
            if person['job'] in ['Writer', 'Screenplay']
        ]
        
        # Format genres
        genres = [
            {'id': g['id'], 'name': g['name']}
            for g in data.get('genres', [])
        ]
        
        # Get certification
        release_dates = data.get('release_dates', {}).get('results', [])
        us_release = next((r for r in release_dates if r['iso_3166_1'] == 'US'), None)
        certification = None
        if us_release and us_release.get('release_dates'):
            certification = us_release['release_dates'][0].get('certification')
        
        return {
            'id': data['id'],
            'type': 'movie',
            'title': data['title'],
            'original_title': data.get('original_title'),
            'tagline': data.get('tagline'),
            'overview': data.get('overview'),
            'release_date': data.get('release_date'),
            'runtime': data.get('runtime'),
            'rating': data.get('vote_average'),
            'vote_count': data.get('vote_count'),
            'certification': certification,
            'genres': genres,
            'cast': cast,
            'directors': directors,
            'writers': writers,
            'poster_path': f"{TMDB_IMAGE_BASE}/w500{data['poster_path']}" if data.get('poster_path') else None,
            'backdrop_path': f"{TMDB_IMAGE_BASE}/original{data['backdrop_path']}" if data.get('backdrop_path') else None,
            'trailer': f"https://www.youtube.com/watch?v={trailer['key']}" if trailer else None,
            'similar': [
                {
                    'id': s['id'],
                    'title': s['title'],
                    'poster_path': f"{TMDB_IMAGE_BASE}/w185{s['poster_path']}" if s.get('poster_path') else None
                }
                for s in data.get('similar', {}).get('results', [])[:6]
            ],
            'keywords': [kw['name'] for kw in data.get('keywords', {}).get('keywords', [])]
        }
    
    @staticmethod
    def format_tv(data: Dict) -> Dict:
        """Format TV show data for frontend"""
        credits = data.get('credits', {})
        videos = data.get('videos', {}).get('results', [])
        
        # Get trailer
        trailer = next((v for v in videos if v['type'] == 'Trailer' and v['site'] == 'YouTube'), None)
        
        # Format cast
        cast = [
            {
                'id': person['id'],
                'name': person['name'],
                'character': person.get('character', ''),
                'profile_path': f"{TMDB_IMAGE_BASE}/w185{person['profile_path']}" if person.get('profile_path') else None
            }
            for person in credits.get('cast', [])[:10]
        ]
        
        # Format creators
        creators = [
            {'id': c['id'], 'name': c['name']}
            for c in data.get('created_by', [])
        ]
        
        # Format genres
        genres = [
            {'id': g['id'], 'name': g['name']}
            for g in data.get('genres', [])
        ]
        
        # Get content rating
        content_ratings = data.get('content_ratings', {}).get('results', [])
        us_rating = next((r for r in content_ratings if r['iso_3166_1'] == 'US'), None)
        certification = us_rating.get('rating') if us_rating else None
        
        return {
            'id': data['id'],
            'type': 'tv',
            'title': data['name'],
            'original_title': data.get('original_name'),
            'tagline': data.get('tagline'),
            'overview': data.get('overview'),
            'first_air_date': data.get('first_air_date'),
            'last_air_date': data.get('last_air_date'),
            'number_of_seasons': data.get('number_of_seasons'),
            'number_of_episodes': data.get('number_of_episodes'),
            'episode_run_time': data.get('episode_run_time', [None])[0],
            'rating': data.get('vote_average'),
            'vote_count': data.get('vote_count'),
            'certification': certification,
            'status': data.get('status'),
            'genres': genres,
            'cast': cast,
            'creators': creators,
            'poster_path': f"{TMDB_IMAGE_BASE}/w500{data['poster_path']}" if data.get('poster_path') else None,
            'backdrop_path': f"{TMDB_IMAGE_BASE}/original{data['backdrop_path']}" if data.get('backdrop_path') else None,
            'trailer': f"https://www.youtube.com/watch?v={trailer['key']}" if trailer else None,
            'similar': [
                {
                    'id': s['id'],
                    'title': s['name'],
                    'poster_path': f"{TMDB_IMAGE_BASE}/w185{s['poster_path']}" if s.get('poster_path') else None
                }
                for s in data.get('similar', {}).get('results', [])[:6]
            ],
            'keywords': [kw['name'] for kw in data.get('keywords', {}).get('results', [])]
        }
    
    @staticmethod
    def format_person(data: Dict) -> Dict:
        """Format person data for frontend"""
        combined_credits = data.get('combined_credits', {})
        
        # Sort by popularity
        cast_credits = sorted(
            combined_credits.get('cast', []),
            key=lambda x: x.get('popularity', 0),
            reverse=True
        )[:20]
        
        crew_credits = sorted(
            combined_credits.get('crew', []),
            key=lambda x: x.get('popularity', 0),
            reverse=True
        )[:20]
        
        return {
            'id': data['id'],
            'name': data['name'],
            'biography': data.get('biography'),
            'birthday': data.get('birthday'),
            'place_of_birth': data.get('place_of_birth'),
            'profile_path': f"{TMDB_IMAGE_BASE}/h632{data['profile_path']}" if data.get('profile_path') else None,
            'known_for_department': data.get('known_for_department'),
            'cast_credits': [
                {
                    'id': c['id'],
                    'title': c.get('title') or c.get('name'),
                    'character': c.get('character'),
                    'media_type': c.get('media_type'),
                    'poster_path': f"{TMDB_IMAGE_BASE}/w185{c['poster_path']}" if c.get('poster_path') else None
                }
                for c in cast_credits
            ],
            'crew_credits': [
                {
                    'id': c['id'],
                    'title': c.get('title') or c.get('name'),
                    'job': c.get('job'),
                    'media_type': c.get('media_type'),
                    'poster_path': f"{TMDB_IMAGE_BASE}/w185{c['poster_path']}" if c.get('poster_path') else None
                }
                for c in crew_credits
            ]
        }

# API Endpoints

@synopsis_bp.route("/api/synopsis/search", methods=["POST"])
@require_api_key
def search():
    """Search for movies or TV shows"""
    data = request.get_json() or {}
    query = data.get('query', '')
    media_type = data.get('type', 'movie')  # 'movie' or 'tv'
    year = data.get('year')
    
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    
    try:
        if media_type == 'movie':
            results = TMDBClient.search_movie(query, year)
        else:
            results = TMDBClient.search_tv(query, year)
        
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@synopsis_bp.route("/api/synopsis/movie/<int:movie_id>", methods=["GET"])
@require_api_key
def get_movie(movie_id):
    """Get detailed movie information"""
    try:
        data = TMDBClient.get_movie_details(movie_id)
        formatted = SynopsisFormatter.format_movie(data)
        return jsonify(formatted)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@synopsis_bp.route("/api/synopsis/tv/<int:tv_id>", methods=["GET"])
@require_api_key
def get_tv(tv_id):
    """Get detailed TV show information"""
    try:
        data = TMDBClient.get_tv_details(tv_id)
        formatted = SynopsisFormatter.format_tv(data)
        return jsonify(formatted)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@synopsis_bp.route("/api/synopsis/person/<int:person_id>", methods=["GET"])
@require_api_key
def get_person(person_id):
    """Get person details and filmography"""
    try:
        data = TMDBClient.get_person_details(person_id)
        formatted = SynopsisFormatter.format_person(data)
        return jsonify(formatted)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
