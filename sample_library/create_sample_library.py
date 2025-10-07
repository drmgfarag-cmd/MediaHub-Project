#!/usr/bin/env python3
"""
Sample Media Library Structure Creator for MediaHub Phase 1C
Creates realistic directory structures and placeholder files for testing
"""

import os
import json
import random
from pathlib import Path

class SampleLibraryCreator:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        
    def create_placeholder_file(self, file_path, size_mb=1):
        """Create a placeholder file with specified size"""
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create placeholder content
        placeholder_content = f"# PLACEHOLDER FILE\n# Original Size: {size_mb}MB\n# Path: {file_path}\n# Created for MediaHub Phase 1C Testing\n"
        placeholder_content += "\n" + "*" * 100 + "\n"
        placeholder_content += "This is a placeholder file for testing MediaHub's media organization capabilities.\n"
        placeholder_content += "In a real implementation, this would contain actual media content.\n"
        placeholder_content += "*" * 100 + "\n"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(placeholder_content)
            
    def create_nfo_file(self, video_path, metadata):
        """Create NFO metadata file"""
        nfo_path = video_path.with_suffix('.nfo')
        nfo_content = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<movie>
    <title>{metadata['title']}</title>
    <year>{metadata['year']}</year>
    <rating>{metadata['rating']}</rating>
    <plot>{metadata['plot']}</plot>
    <genre>{metadata['genre']}</genre>
    <director>{metadata['director']}</director>
    <runtime>{metadata['runtime']}</runtime>
    <mpaa>{metadata['mpaa']}</mpaa>
</movie>
"""
        with open(nfo_path, 'w', encoding='utf-8') as f:
            f.write(nfo_content)
            
    def create_subtitle_file(self, video_path, language, content_type="normal"):
        """Create subtitle file"""
        suffix = ".forced" if content_type == "forced" else ""
        suffix += ".hi" if content_type == "hearing_impaired" else ""
        
        srt_path = video_path.with_suffix(f'.{language}{suffix}.srt')
        
        srt_content = """1
00:00:01,000 --> 00:00:04,000
This is a sample subtitle file

2
00:00:05,000 --> 00:00:08,000
Created for MediaHub Phase 1C testing

3
00:00:09,000 --> 00:00:12,000
Demonstrates subtitle organization capabilities
"""
        
        with open(srt_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)
            
    def create_sample_movies(self):
        """Create sample movie library"""
        movies_base = self.base_path / "Movies"
        
        # Action Movies
        action_movies = [
            {"title": "Fast.Action.2024", "year": 2024, "size": 8500, "quality": "2160p", "codec": "x265", "group": "YIFY"},
            {"title": "Mission.Impossible.Dead.Reckoning", "year": 2023, "size": 6200, "quality": "1080p", "codec": "x264", "group": "RARBG"},
            {"title": "John.Wick.Chapter.4", "year": 2023, "size": 4800, "quality": "1080p", "codec": "x265", "group": "FGT"},
            {"title": "Top.Gun.Maverick", "year": 2022, "size": 7200, "quality": "2160p", "codec": "AV1", "group": "SCENE"},
            {"title": "The.Matrix.Resurrections", "year": 2021, "size": 5600, "quality": "1080p", "codec": "x264", "group": "YTS"}
        ]
        
        for movie in action_movies:
            filename = f"{movie['title']}.{movie['year']}.{movie['quality']}.BluRay.{movie['codec']}-{movie['group']}.mkv"
            movie_path = movies_base / "Action" / filename
            self.create_placeholder_file(movie_path, movie['size'])
            
            # Create metadata
            metadata = {
                "title": movie['title'].replace('.', ' '),
                "year": movie['year'],
                "rating": round(random.uniform(6.5, 9.2), 1),
                "plot": f"High-octane action thriller from {movie['year']}",
                "genre": "Action / Thriller",
                "director": "Sample Director",
                "runtime": f"{random.randint(110, 150)} min",
                "mpaa": "PG-13"
            }
            self.create_nfo_file(movie_path, metadata)
            
            # Create subtitles
            for lang in ['en', 'es', 'fr', 'de']:
                self.create_subtitle_file(movie_path, lang)
            self.create_subtitle_file(movie_path, 'en', 'forced')
            
        # Comedy Movies
        comedy_movies = [
            {"title": "Funny.Business.2024", "year": 2024, "size": 3200, "quality": "1080p", "codec": "x264", "group": "YIFY"},
            {"title": "The.Comedy.Special", "year": 2023, "size": 2800, "quality": "720p", "codec": "x265", "group": "RARBG"},
            {"title": "Laugh.Out.Loud", "year": 2023, "size": 4100, "quality": "1080p", "codec": "x264", "group": "FGT"}
        ]
        
        for movie in comedy_movies:
            filename = f"{movie['title']}.{movie['year']}.{movie['quality']}.WEB-DL.{movie['codec']}-{movie['group']}.mp4"
            movie_path = movies_base / "Comedy" / filename
            self.create_placeholder_file(movie_path, movie['size'])
            
            metadata = {
                "title": movie['title'].replace('.', ' '),
                "year": movie['year'],
                "rating": round(random.uniform(7.0, 8.5), 1),
                "plot": f"Hilarious comedy from {movie['year']}",
                "genre": "Comedy",
                "director": "Comedy Director",
                "runtime": f"{random.randint(90, 120)} min",
                "mpaa": "R"
            }
            self.create_nfo_file(movie_path, metadata)
            
            for lang in ['en', 'es']:
                self.create_subtitle_file(movie_path, lang)
                
    def create_sample_tv_shows(self):
        """Create sample TV show library"""
        tv_base = self.base_path / "TV Shows"
        
        tv_shows = [
            {
                "name": "Breaking.Bad",
                "seasons": 5,
                "episodes_per_season": [7, 13, 13, 13, 16],
                "year_start": 2008,
                "quality": "1080p",
                "codec": "x264",
                "group": "SCENE"
            },
            {
                "name": "The.Office.US",
                "seasons": 9,
                "episodes_per_season": [6, 22, 25, 19, 28, 26, 26, 24, 25],
                "year_start": 2005,
                "quality": "720p",
                "codec": "x265",
                "group": "YIFY"
            },
            {
                "name": "Stranger.Things",
                "seasons": 4,
                "episodes_per_season": [8, 9, 8, 9],
                "year_start": 2016,
                "quality": "2160p",
                "codec": "x265",
                "group": "NETFLIX"
            }
        ]
        
        for show in tv_shows:
            show_dir = tv_base / show['name']
            
            for season in range(1, show['seasons'] + 1):
                season_dir = show_dir / f"Season {season:02d}"
                episodes = show['episodes_per_season'][season - 1]
                
                for episode in range(1, episodes + 1):
                    filename = f"{show['name']}.S{season:02d}E{episode:02d}.Episode.Title.{show['quality']}.WEB-DL.{show['codec']}-{show['group']}.mkv"
                    episode_path = season_dir / filename
                    self.create_placeholder_file(episode_path, random.randint(800, 1500))
                    
                    # Create subtitles for some episodes
                    if random.random() > 0.3:
                        for lang in ['en', 'es']:
                            self.create_subtitle_file(episode_path, lang)
                            
    def create_sample_documentaries(self):
        """Create sample documentary library"""
        doc_base = self.base_path / "Documentaries"
        
        documentaries = [
            {"title": "Planet.Earth.III", "year": 2023, "episodes": 8, "quality": "2160p", "codec": "x265", "group": "BBC"},
            {"title": "Our.Universe", "year": 2022, "episodes": 6, "quality": "1080p", "codec": "x264", "group": "NETFLIX"},
            {"title": "The.Last.Dance", "year": 2020, "episodes": 10, "quality": "1080p", "codec": "x265", "group": "SCENE"}
        ]
        
        for doc in documentaries:
            doc_dir = doc_base / doc['title']
            
            for episode in range(1, doc['episodes'] + 1):
                filename = f"{doc['title']}.E{episode:02d}.{doc['quality']}.WEB-DL.{doc['codec']}-{doc['group']}.mkv"
                episode_path = doc_dir / filename
                self.create_placeholder_file(episode_path, random.randint(2000, 4000))
                
                for lang in ['en', 'es', 'fr']:
                    self.create_subtitle_file(episode_path, lang)
                    
    def create_sample_music_videos(self):
        """Create sample music video library"""
        music_base = self.base_path / "Music Videos"
        
        artists = [
            {"name": "Taylor.Swift", "videos": ["Anti-Hero", "Lavender.Haze", "Karma"], "year": 2022},
            {"name": "The.Weeknd", "videos": ["Blinding.Lights", "Save.Your.Tears", "Gasoline"], "year": 2021},
            {"name": "Billie.Eilish", "videos": ["bad.guy", "everything.i.wanted", "Happier.Than.Ever"], "year": 2021}
        ]
        
        for artist in artists:
            artist_dir = music_base / artist['name']
            
            for video in artist['videos']:
                filename = f"{artist['name']}.-.{video}.{artist['year']}.1080p.WEB-DL.x264-MUSIC.mp4"
                video_path = artist_dir / filename
                self.create_placeholder_file(video_path, random.randint(200, 500))
                
    def create_sample_audiobooks(self):
        """Create sample audiobook library"""
        audio_base = self.base_path / "Audiobooks"
        
        audiobooks = [
            {"title": "Harry.Potter.and.the.Sorcerers.Stone", "author": "J.K.Rowling", "narrator": "Jim.Dale", "chapters": 17},
            {"title": "The.Hobbit", "author": "J.R.R.Tolkien", "narrator": "Rob.Inglis", "chapters": 19},
            {"title": "1984", "author": "George.Orwell", "narrator": "Simon.Prebble", "chapters": 23}
        ]
        
        for book in audiobooks:
            book_dir = audio_base / f"{book['author']}" / book['title']
            
            for chapter in range(1, book['chapters'] + 1):
                filename = f"Chapter.{chapter:02d}.mp3"
                chapter_path = book_dir / filename
                self.create_placeholder_file(chapter_path, random.randint(50, 150))
                
    def create_edge_cases(self):
        """Create edge cases and test scenarios"""
        edge_base = self.base_path / "Test Cases"
        
        # Duplicate files with different qualities
        duplicates_dir = edge_base / "Duplicates"
        base_movie = "The.Matrix.1999"
        
        qualities = ["480p", "720p", "1080p", "2160p"]
        codecs = ["x264", "x265", "AV1"]
        groups = ["YIFY", "RARBG", "FGT", "SCENE"]
        
        for quality in qualities:
            for codec in codecs[:2]:  # Limit combinations
                for group in groups[:2]:
                    filename = f"{base_movie}.{quality}.BluRay.{codec}-{group}.mkv"
                    file_path = duplicates_dir / filename
                    self.create_placeholder_file(file_path, random.randint(1000, 8000))
                    
        # Files with missing metadata
        missing_meta_dir = edge_base / "Missing Metadata"
        problematic_files = [
            "Unknown.Movie.mkv",
            "No.Year.x264.mp4",
            "BadNaming-file.avi",
            "movie_with_underscores.2023.mkv"
        ]
        
        for filename in problematic_files:
            file_path = missing_meta_dir / filename
            self.create_placeholder_file(file_path, random.randint(1000, 3000))
            
        # International titles
        international_dir = edge_base / "International"
        international_movies = [
            "Parasite.2019.1080p.BluRay.x264-[Korean].mkv",
            "Amélie.2001.720p.x265-[French].mkv",
            "Seven.Samurai.1954.1080p.x264-[Japanese].mkv",
            "La.Dolce.Vita.1960.720p.x264-[Italian].mkv"
        ]
        
        for filename in international_movies:
            file_path = international_dir / filename
            self.create_placeholder_file(file_path, random.randint(2000, 6000))
            
            # Create multiple subtitle languages
            for lang in ['en', 'es', 'fr', 'de', 'it', 'ja', 'ko']:
                self.create_subtitle_file(file_path, lang)
                
    def create_library_manifest(self):
        """Create a manifest file describing the sample library"""
        manifest = {
            "library_info": {
                "name": "MediaHub Phase 1C Sample Library",
                "version": "1.0",
                "created": "2025-10-06",
                "total_simulated_size_gb": 2.1,
                "purpose": "Testing and demonstration of MediaHub organization capabilities"
            },
            "structure": {
                "Movies": {
                    "Action": "High-quality action movies with full metadata",
                    "Comedy": "Comedy collection with subtitles",
                    "Drama": "Dramatic films",
                    "Sci-Fi": "Science fiction collection",
                    "Horror": "Horror movie collection"
                },
                "TV Shows": {
                    "description": "Complete TV series with season/episode organization",
                    "examples": ["Breaking Bad", "The Office", "Stranger Things"]
                },
                "Documentaries": {
                    "description": "Documentary series and films",
                    "examples": ["Planet Earth III", "Our Universe"]
                },
                "Music Videos": {
                    "description": "Music video collections by artist",
                    "examples": ["Taylor Swift", "The Weeknd", "Billie Eilish"]
                },
                "Audiobooks": {
                    "description": "Audiobook collections with chapter organization",
                    "examples": ["Harry Potter", "The Hobbit", "1984"]
                },
                "Test Cases": {
                    "Duplicates": "Files with same content but different qualities",
                    "Missing Metadata": "Files with incomplete or missing information",
                    "International": "Foreign language content with multiple subtitles"
                }
            },
            "features_demonstrated": [
                "Proper naming conventions",
                "Multi-language subtitle support",
                "NFO metadata files",
                "Quality and codec variations",
                "Release group patterns",
                "Franchise organization",
                "Duplicate detection scenarios",
                "International content handling"
            ]
        }
        
        manifest_path = self.base_path / "library_manifest.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
            
    def create_complete_library(self):
        """Create the complete sample library"""
        print("Creating sample movie library...")
        self.create_sample_movies()
        
        print("Creating sample TV shows...")
        self.create_sample_tv_shows()
        
        print("Creating sample documentaries...")
        self.create_sample_documentaries()
        
        print("Creating sample music videos...")
        self.create_sample_music_videos()
        
        print("Creating sample audiobooks...")
        self.create_sample_audiobooks()
        
        print("Creating edge cases and test scenarios...")
        self.create_edge_cases()
        
        print("Creating library manifest...")
        self.create_library_manifest()
        
        print("Sample library creation complete!")

if __name__ == "__main__":
    # Create the sample library
    creator = SampleLibraryCreator("/workspace/MediaHub_Phase_1C_Complete/sample_library")
    creator.create_complete_library()
