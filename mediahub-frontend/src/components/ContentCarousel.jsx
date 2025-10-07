import React, { useState, useRef } from 'react';
import { ChevronLeft, ChevronRight, Play, Plus, ThumbsUp, ChevronDown } from 'lucide-react';

const ContentCarousel = ({ title, items = [] }) => {
  const [scrollPosition, setScrollPosition] = useState(0);
  const [hoveredItem, setHoveredItem] = useState(null);
  const carouselRef = useRef(null);

  // Sample content if no items provided
  const sampleItems = items.length > 0 ? items : [
    {
      id: 1,
      title: 'Stranger Things',
      poster: 'https://image.tmdb.org/t/p/w500/49WJfeN0moxb9IPfGn8AIqMGskD.jpg',
      rating: '8.7',
      year: '2016',
      maturity: '16+',
      seasons: '4 Seasons',
      genres: ['Sci-Fi', 'Horror', 'Drama']
    },
    {
      id: 2,
      title: 'The Witcher',
      poster: 'https://image.tmdb.org/t/p/w500/7vjaCdMw15FEbXyLQTVa04URsPm.jpg',
      rating: '8.2',
      year: '2019',
      maturity: '18+',
      seasons: '3 Seasons',
      genres: ['Fantasy', 'Action', 'Adventure']
    },
    {
      id: 3,
      title: 'The Crown',
      poster: 'https://image.tmdb.org/t/p/w500/1M876KPjulVwppEpldhdc8V4o68.jpg',
      rating: '8.6',
      year: '2016',
      maturity: '16+',
      seasons: '6 Seasons',
      genres: ['Drama', 'History']
    },
    {
      id: 4,
      title: 'Ozark',
      poster: 'https://image.tmdb.org/t/p/w500/m73QW8uVR0OhWkXYZdNFmJBRz8g.jpg',
      rating: '8.5',
      year: '2017',
      maturity: '18+',
      seasons: '4 Seasons',
      genres: ['Crime', 'Drama', 'Thriller']
    },
    {
      id: 5,
      title: 'Dark',
      poster: 'https://image.tmdb.org/t/p/w500/56v2KjBlU4XaOv9rVYEQypROD7P.jpg',
      rating: '8.8',
      year: '2017',
      maturity: '16+',
      seasons: '3 Seasons',
      genres: ['Sci-Fi', 'Mystery', 'Drama']
    },
    {
      id: 6,
      title: 'Money Heist',
      poster: 'https://image.tmdb.org/t/p/w500/reEMJA1uzscCbkpeRJeTT2bjqUp.jpg',
      rating: '8.2',
      year: '2017',
      maturity: '16+',
      seasons: '5 Seasons',
      genres: ['Crime', 'Drama', 'Mystery']
    }
  ];

  const displayItems = items.length > 0 ? items : sampleItems;

  const scroll = (direction) => {
    const container = carouselRef.current;
    if (!container) return;

    const scrollAmount = container.offsetWidth * 0.8;
    const newPosition = direction === 'left'
      ? Math.max(0, scrollPosition - scrollAmount)
      : Math.min(container.scrollWidth - container.offsetWidth, scrollPosition + scrollAmount);

    container.scrollTo({
      left: newPosition,
      behavior: 'smooth'
    });
    setScrollPosition(newPosition);
  };

  return (
    <div className="relative group mb-12">
      {/* Title */}
      <h2 className="text-2xl font-bold text-white mb-4 px-8">{title}</h2>

      {/* Carousel Container */}
      <div className="relative px-8">
        {/* Left Arrow */}
        {scrollPosition > 0 && (
          <button
            onClick={() => scroll('left')}
            className="absolute left-0 top-0 bottom-0 z-20 w-12 bg-gradient-to-r from-black/80 to-transparent flex items-center justify-start pl-2 opacity-0 group-hover:opacity-100 transition-opacity"
            aria-label="Scroll left"
          >
            <div className="bg-black/60 hover:bg-black/80 rounded-full p-2">
              <ChevronLeft className="w-8 h-8 text-white" />
            </div>
          </button>
        )}

        {/* Content */}
        <div
          ref={carouselRef}
          className="flex gap-2 overflow-x-hidden scroll-smooth"
          onScroll={(e) => setScrollPosition(e.target.scrollLeft)}
        >
          {displayItems.map((item) => (
            <div
              key={item.id}
              className="relative flex-shrink-0 w-[200px] transition-transform duration-300 hover:scale-110 hover:z-10"
              onMouseEnter={() => setHoveredItem(item.id)}
              onMouseLeave={() => setHoveredItem(null)}
            >
              {/* Poster */}
              <div className="relative aspect-[2/3] rounded-md overflow-hidden">
                <img
                  src={item.poster}
                  alt={item.title}
                  className="w-full h-full object-cover"
                />
                
                {/* Hover Overlay */}
                {hoveredItem === item.id && (
                  <div className="absolute inset-0 bg-gradient-to-t from-black via-black/50 to-transparent flex flex-col justify-end p-3 animate-in fade-in duration-200">
                    {/* Quick Actions */}
                    <div className="flex gap-2 mb-2">
                      <button className="bg-white text-black rounded-full p-2 hover:bg-white/90 transition-colors">
                        <Play className="w-4 h-4 fill-current" />
                      </button>
                      <button className="bg-gray-800/80 text-white rounded-full p-2 hover:bg-gray-700/80 transition-colors">
                        <Plus className="w-4 h-4" />
                      </button>
                      <button className="bg-gray-800/80 text-white rounded-full p-2 hover:bg-gray-700/80 transition-colors">
                        <ThumbsUp className="w-4 h-4" />
                      </button>
                      <button className="bg-gray-800/80 text-white rounded-full p-2 hover:bg-gray-700/80 transition-colors ml-auto">
                        <ChevronDown className="w-4 h-4" />
                      </button>
                    </div>

                    {/* Info */}
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 text-xs text-white/90">
                        <span className="text-green-400 font-semibold">{item.rating}</span>
                        <span>{item.year}</span>
                        <span className="border border-white/40 px-1">{item.maturity}</span>
                      </div>
                      <div className="text-xs text-white/80">
                        {item.seasons}
                      </div>
                      <div className="flex gap-1 flex-wrap">
                        {item.genres.slice(0, 3).map((genre, index) => (
                          <span key={index} className="text-xs text-white/70">
                            {genre}
                            {index < Math.min(item.genres.length, 3) - 1 && ' •'}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Title (always visible) */}
              <div className="mt-2 px-1">
                <h3 className="text-sm font-medium text-white line-clamp-1">
                  {item.title}
                </h3>
              </div>
            </div>
          ))}
        </div>

        {/* Right Arrow */}
        {scrollPosition < (carouselRef.current?.scrollWidth - carouselRef.current?.offsetWidth - 10) && (
          <button
            onClick={() => scroll('right')}
            className="absolute right-0 top-0 bottom-0 z-20 w-12 bg-gradient-to-l from-black/80 to-transparent flex items-center justify-end pr-2 opacity-0 group-hover:opacity-100 transition-opacity"
            aria-label="Scroll right"
          >
            <div className="bg-black/60 hover:bg-black/80 rounded-full p-2">
              <ChevronRight className="w-8 h-8 text-white" />
            </div>
          </button>
        )}
      </div>
    </div>
  );
};

export default ContentCarousel;
