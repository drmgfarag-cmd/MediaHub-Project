import React, { useState, useEffect } from 'react';
import { Play, Info, ChevronLeft, ChevronRight, Volume2, VolumeX } from 'lucide-react';
import { Button } from './ui/button';

const HeroSection = () => {
  const [currentHero, setCurrentHero] = useState(0);
  const [isMuted, setIsMuted] = useState(true);
  const [isPlaying, setIsPlaying] = useState(false);

  // Sample hero content - in production, this would come from API
  const heroContent = [
    {
      id: 1,
      title: 'The Last Kingdom',
      description: 'As Alfred the Great defends his kingdom from Norse invaders, Uhtred - born a Saxon but raised by Vikings - seeks to claim his ancestral birthright.',
      backdrop: 'https://image.tmdb.org/t/p/original/qsxhnirlp7y4Ae9bd11oYA4Yxfq.jpg',
      logo: null,
      rating: '8.5',
      year: '2015',
      seasons: '5 Seasons',
      genres: ['Drama', 'Action', 'History'],
      trailerUrl: null
    },
    {
      id: 2,
      title: 'Dune',
      description: 'Paul Atreides, a brilliant and gifted young man born into a great destiny beyond his understanding, must travel to the most dangerous planet in the universe to ensure the future of his family and his people.',
      backdrop: 'https://image.tmdb.org/t/p/original/s16H6tpK2utvwDtzZ8Qy4qm5Emw.jpg',
      logo: null,
      rating: '8.0',
      year: '2021',
      runtime: '2h 35m',
      genres: ['Science Fiction', 'Adventure'],
      trailerUrl: null
    },
    {
      id: 3,
      title: 'Breaking Bad',
      description: 'When Walter White, a New Mexico chemistry teacher, is diagnosed with Stage III cancer and given a prognosis of only two years left to live, he becomes filled with a sense of fearlessness and an unrelenting desire to secure his family\'s financial future.',
      backdrop: 'https://image.tmdb.org/t/p/original/9faGSFi5jam6pDWGNd0p8JcJgXQ.jpg',
      logo: null,
      rating: '9.5',
      year: '2008',
      seasons: '5 Seasons',
      genres: ['Drama', 'Crime', 'Thriller'],
      trailerUrl: null
    }
  ];

  const currentItem = heroContent[currentHero];

  // Auto-rotate hero content
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentHero((prev) => (prev + 1) % heroContent.length);
    }, 8000);

    return () => clearInterval(interval);
  }, [heroContent.length]);

  const handlePrevious = () => {
    setCurrentHero((prev) => (prev - 1 + heroContent.length) % heroContent.length);
  };

  const handleNext = () => {
    setCurrentHero((prev) => (prev + 1) % heroContent.length);
  };

  const handlePlayTrailer = () => {
    setIsPlaying(true);
    // In production, this would trigger video playback
  };

  return (
    <div className="relative h-[85vh] w-full overflow-hidden">
      {/* Background Image with Gradient Overlay */}
      <div className="absolute inset-0 transition-opacity duration-1000">
        <img
          src={currentItem.backdrop}
          alt={currentItem.title}
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-r from-black via-black/70 to-transparent" />
        <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent" />
      </div>

      {/* Content */}
      <div className="relative z-10 h-full flex items-center">
        <div className="container mx-auto px-8 max-w-7xl">
          <div className="max-w-2xl space-y-6">
            {/* Title */}
            {currentItem.logo ? (
              <img
                src={currentItem.logo}
                alt={currentItem.title}
                className="h-32 w-auto object-contain"
              />
            ) : (
              <h1 className="text-6xl font-bold text-white drop-shadow-2xl">
                {currentItem.title}
              </h1>
            )}

            {/* Metadata */}
            <div className="flex items-center gap-4 text-white/90">
              <span className="flex items-center gap-1 text-green-400 font-semibold">
                <svg className="w-5 h-5 fill-current" viewBox="0 0 24 24">
                  <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z" />
                </svg>
                {currentItem.rating}
              </span>
              <span className="font-medium">{currentItem.year}</span>
              <span>{currentItem.seasons || currentItem.runtime}</span>
              <span className="px-2 py-0.5 border border-white/40 text-xs font-semibold rounded">
                HD
              </span>
            </div>

            {/* Genres */}
            <div className="flex gap-2">
              {currentItem.genres.map((genre, index) => (
                <span
                  key={index}
                  className="text-white/80 text-sm"
                >
                  {genre}
                  {index < currentItem.genres.length - 1 && ' •'}
                </span>
              ))}
            </div>

            {/* Description */}
            <p className="text-white/90 text-lg leading-relaxed line-clamp-3">
              {currentItem.description}
            </p>

            {/* Action Buttons */}
            <div className="flex gap-4 pt-2">
              <Button
                size="lg"
                className="bg-white text-black hover:bg-white/90 gap-2 px-8 py-6 text-lg font-semibold"
                onClick={handlePlayTrailer}
              >
                <Play className="w-6 h-6 fill-current" />
                Play
              </Button>
              <Button
                size="lg"
                variant="outline"
                className="bg-gray-500/30 text-white border-white/40 hover:bg-gray-500/50 gap-2 px-8 py-6 text-lg font-semibold backdrop-blur-sm"
              >
                <Info className="w-6 h-6" />
                More Info
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Arrows */}
      <button
        onClick={handlePrevious}
        className="absolute left-4 top-1/2 -translate-y-1/2 z-20 bg-black/50 hover:bg-black/70 text-white p-3 rounded-full backdrop-blur-sm transition-all"
        aria-label="Previous"
      >
        <ChevronLeft className="w-8 h-8" />
      </button>
      <button
        onClick={handleNext}
        className="absolute right-4 top-1/2 -translate-y-1/2 z-20 bg-black/50 hover:bg-black/70 text-white p-3 rounded-full backdrop-blur-sm transition-all"
        aria-label="Next"
      >
        <ChevronRight className="w-8 h-8" />
      </button>

      {/* Mute Button */}
      <button
        onClick={() => setIsMuted(!isMuted)}
        className="absolute right-8 bottom-32 z-20 bg-black/50 hover:bg-black/70 text-white p-3 rounded-full backdrop-blur-sm transition-all"
        aria-label={isMuted ? 'Unmute' : 'Mute'}
      >
        {isMuted ? <VolumeX className="w-6 h-6" /> : <Volume2 className="w-6 h-6" />}
      </button>

      {/* Pagination Dots */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-20 flex gap-2">
        {heroContent.map((_, index) => (
          <button
            key={index}
            onClick={() => setCurrentHero(index)}
            className={`h-1 rounded-full transition-all ${
              index === currentHero
                ? 'w-8 bg-white'
                : 'w-1 bg-white/50 hover:bg-white/70'
            }`}
            aria-label={`Go to slide ${index + 1}`}
          />
        ))}
      </div>
    </div>
  );
};

export default HeroSection;
