import React, { useState, useEffect } from 'react';
import ContentCarouselEnhanced from '../components/ContentCarouselEnhanced';
import HeroSection from '../components/HeroSection';
import { toast } from 'sonner';

/**
 * Library Page - Main Media Library with Full Feature Integration
 * 
 * Features:
 * - Hero section with featured content
 * - Multiple content carousels (Continue Watching, TV Shows, Movies, etc.)
 * - Context menu integration
 * - Multi-select and bulk operations
 * - Clickable metadata filtering
 * - Pinned items management
 * - Collection management
 * - Real-time updates
 */
const LibraryPage = () => {
  const [library, setLibrary] = useState({
    featured: null,
    continueWatching: [],
    tvShows: [],
    movies: [],
    recentlyAdded: [],
    trending: [],
  });
  const [pinnedItems, setPinnedItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeFilter, setActiveFilter] = useState(null);

  // API base URL
  const API_BASE = '/api';

  // Load library data
  useEffect(() => {
    loadLibraryData();
    loadPinnedItems();
  }, []);

  const loadLibraryData = async () => {
    try {
      setLoading(true);
      
      // Fetch from multiple endpoints registered in Phase 1
      const [featured, continueWatching, tvShows, movies, recent, trending] = await Promise.all([
        fetch(`${API_BASE}/discovery/featured`).then(r => r.json()).catch(() => null),
        fetch(`${API_BASE}/watch_history/continue`).then(r => r.json()).catch(() => []),
        fetch(`${API_BASE}/library/tv`).then(r => r.json()).catch(() => []),
        fetch(`${API_BASE}/library/movies`).then(r => r.json()).catch(() => []),
        fetch(`${API_BASE}/library/recent`).then(r => r.json()).catch(() => []),
        fetch(`${API_BASE}/discovery/trending`).then(r => r.json()).catch(() => []),
      ]);

      setLibrary({
        featured,
        continueWatching,
        tvShows,
        movies,
        recentlyAdded: recent,
        trending,
      });
    } catch (error) {
      console.error('Failed to load library:', error);
      toast.error('Failed to load library');
    } finally {
      setLoading(false);
    }
  };

  const loadPinnedItems = async () => {
    try {
      const response = await fetch(`${API_BASE}/home_pins`);
      const data = await response.json();
      setPinnedItems(data.items || []);
    } catch (error) {
      console.error('Failed to load pinned items:', error);
    }
  };

  // Play handler
  const handlePlay = async (item) => {
    try {
      // Start playback via mobile_streaming or player endpoint
      const response = await fetch(`${API_BASE}/player/play`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          mediaId: item.id,
          mediaType: item.type || 'video'
        }),
      });
      
      if (response.ok) {
        const playbackData = await response.json();
        // Navigate to player or open casting UI
        window.location.href = `/player?id=${item.id}`;
      }
    } catch (error) {
      console.error('Failed to start playback:', error);
      toast.error('Failed to start playback');
    }
  };

  // Pin/Unpin handlers
  const handlePin = async (item) => {
    try {
      const response = await fetch(`${API_BASE}/home_pins`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mediaId: item.id }),
      });
      
      if (response.ok) {
        setPinnedItems([...pinnedItems, item]);
        toast.success(`Pinned "${item.title}"`);
      }
    } catch (error) {
      console.error('Failed to pin item:', error);
      toast.error('Failed to pin item');
    }
  };

  const handleUnpin = async (item) => {
    try {
      const response = await fetch(`${API_BASE}/home_pins/${item.id}`, {
        method: 'DELETE',
      });
      
      if (response.ok) {
        setPinnedItems(pinnedItems.filter(p => p.id !== item.id));
        toast.success(`Unpinned "${item.title}"`);
      }
    } catch (error) {
      console.error('Failed to unpin item:', error);
      toast.error('Failed to unpin item');
    }
  };

  // Collection handlers
  const handleAddToCollection = async (item, collectionId) => {
    try {
      const response = await fetch(`${API_BASE}/collections/${collectionId || 'default'}/items`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mediaId: item.id }),
      });
      
      if (response.ok) {
        toast.success(`Added "${item.title}" to collection`);
      }
    } catch (error) {
      console.error('Failed to add to collection:', error);
      toast.error('Failed to add to collection');
    }
  };

  // Remove handler
  const handleRemove = async (item) => {
    if (!confirm(`Remove "${item.title}" from library?`)) return;
    
    try {
      const response = await fetch(`${API_BASE}/library/${item.id}`, {
        method: 'DELETE',
      });
      
      if (response.ok) {
        // Refresh library
        loadLibraryData();
        toast.success(`Removed "${item.title}"`);
      }
    } catch (error) {
      console.error('Failed to remove item:', error);
      toast.error('Failed to remove item');
    }
  };

  // Edit handler
  const handleEdit = (item) => {
    // Navigate to editor
    window.location.href = `/edit/${item.id}`;
  };

  // Download handler
  const handleDownload = async (item) => {
    try {
      const response = await fetch(`${API_BASE}/downloader/add`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          url: item.downloadUrl,
          title: item.title 
        }),
      });
      
      if (response.ok) {
        toast.success(`Added "${item.title}" to downloads`);
      }
    } catch (error) {
      console.error('Failed to add download:', error);
      toast.error('Failed to add download');
    }
  };

  // View details handler
  const handleViewDetails = (item) => {
    window.location.href = `/details/${item.id}`;
  };

  // Bulk operation handler
  const handleBulkOperation = async (operation, items) => {
    try {
      switch (operation) {
        case 'pin':
          for (const item of items) {
            await handlePin(item);
          }
          break;
        
        case 'addToCollection':
          // Show collection selector dialog
          const collectionId = prompt('Enter collection ID:');
          if (collectionId) {
            for (const item of items) {
              await handleAddToCollection(item, collectionId);
            }
          }
          break;
        
        case 'edit':
          // Batch edit
          window.location.href = `/batch-edit?ids=${items.map(i => i.id).join(',')}`;
          break;
        
        case 'remove':
          if (confirm(`Remove ${items.length} items from library?`)) {
            for (const item of items) {
              await handleRemove(item);
            }
          }
          break;
      }
    } catch (error) {
      console.error('Bulk operation failed:', error);
      toast.error('Bulk operation failed');
    }
  };

  // Metadata filter handlers (clickable directors, actors, genres, tags)
  const handleFilterByDirector = async (director) => {
    try {
      setActiveFilter({ type: 'director', value: director });
      const response = await fetch(`${API_BASE}/discovery/advanced?director=${encodeURIComponent(director)}`);
      const data = await response.json();
      
      // Update library with filtered results
      setLibrary({
        ...library,
        filtered: data.results || [],
      });
      
      toast.info(`Filtering by director

: ${director}`);
    } catch (error) {
      console.error('Filter failed:', error);
      toast.error('Filter failed');
    }
  };

  const handleFilterByActor = async (actor) => {
    try {
      setActiveFilter({ type: 'actor', value: actor });
      const response = await fetch(`${API_BASE}/discovery/advanced?actor=${encodeURIComponent(actor)}`);
      const data = await response.json();
      
      setLibrary({
        ...library,
        filtered: data.results || [],
      });
      
      toast.info(`Filtering by actor: ${actor}`);
    } catch (error) {
      console.error('Filter failed:', error);
      toast.error('Filter failed');
    }
  };

  const handleFilterByGenre = async (genre) => {
    try {
      setActiveFilter({ type: 'genre', value: genre });
      const response = await fetch(`${API_BASE}/discovery/advanced?genre=${encodeURIComponent(genre)}`);
      const data = await response.json();
      
      setLibrary({
        ...library,
        filtered: data.results || [],
      });
      
      toast.info(`Filtering by genre: ${genre}`);
    } catch (error) {
      console.error('Filter failed:', error);
      toast.error('Filter failed');
    }
  };

  const handleFilterByTag = async (tag) => {
    try:
      setActiveFilter({ type: 'tag', value: tag });
      const response = await fetch(`${API_BASE}/tags_system/search?tag=${encodeURIComponent(tag)}`);
      const data = await response.json();
      
      setLibrary({
        ...library,
        filtered: data.results || [],
      });
      
      toast.info(`Filtering by tag: ${tag}`);
    } catch (error) {
      console.error('Filter failed:', error);
      toast.error('Filter failed');
    }
  };

  const clearFilter = () => {
    setActiveFilter(null);
    loadLibraryData();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-white text-xl">Loading library...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black">
      {/* Hero Section */}
      {library.featured && (
        <HeroSection 
          content={library.featured}
          onPlay={() => handlePlay(library.featured)}
          onInfo={() => handleViewDetails(library.featured)}
        />
      )}

      {/* Active Filter Banner */}
      {activeFilter && (
        <div className="bg-blue-600 text-white px-8 py-3 flex items-center justify-between">
          <span>
            Filtering by {activeFilter.type}: <strong>{activeFilter.value}</strong>
          </span>
          <button 
            onClick={clearFilter}
            className="bg-white/20 hover:bg-white/30 px-4 py-1 rounded transition-colors"
          >
            Clear Filter
          </button>
        </div>
      )}

      {/* Filtered Results */}
      {activeFilter && library.filtered && (
        <ContentCarouselEnhanced
          title={`${activeFilter.type}: ${activeFilter.value}`}
          items={library.filtered}
          pinnedItems={pinnedItems}
          onPlay={handlePlay}
          onPin={handlePin}
          onUnpin={handleUnpin}
          onAddToCollection={handleAddToCollection}
          onRemove={handleRemove}
          onEdit={handleEdit}
          onDownload={handleDownload}
          onViewDetails={handleViewDetails}
          onBulkOperation={handleBulkOperation}
          onFilterByDirector={handleFilterByDirector}
          onFilterByActor={handleFilterByActor}
          onFilterByGenre={handleFilterByGenre}
          onFilterByTag={handleFilterByTag}
        />
      )}

      {/* Continue Watching */}
      {library.continueWatching.length > 0 && (
        <ContentCarouselEnhanced
          title="Continue Watching"
          items={library.continueWatching}
          pinnedItems={pinnedItems}
          onPlay={handlePlay}
          onPin={handlePin}
          onUnpin={handleUnpin}
          onAddToCollection={handleAddToCollection}
          onRemove={handleRemove}
          onEdit={handleEdit}
          onDownload={handleDownload}
          onViewDetails={handleViewDetails}
          onBulkOperation={handleBulkOperation}
          onFilterByDirector={handleFilterByDirector}
          onFilterByActor={handleFilterByActor}
          onFilterByGenre={handleFilterByGenre}
          onFilterByTag={handleFilterByTag}
        />
      )}

      {/* Trending */}
      {library.trending.length > 0 && (
        <ContentCarouselEnhanced
          title="Trending Now"
          items={library.trending}
          pinnedItems={pinnedItems}
          onPlay={handlePlay}
          onPin={handlePin}
          onUnpin={handleUnpin}
          onAddToCollection={handleAddToCollection}
          onRemove={handleRemove}
          onEdit={handleEdit}
          onDownload={handleDownload}
          onViewDetails={handleViewDetails}
          onBulkOperation={handleBulkOperation}
          onFilterByDirector={handleFilterByDirector}
          onFilterByActor={handleFilterByActor}
          onFilterByGenre={handleFilterByGenre}
          onFilterByTag={handleFilterByTag}
        />
      )}

      {/* TV Shows */}
      {library.tvShows.length > 0 && (
        <ContentCarouselEnhanced
          title="TV Shows"
          items={library.tvShows}
          pinnedItems={pinnedItems}
          onPlay={handlePlay}
          onPin={handlePin}
          onUnpin={handleUnpin}
          onAddToCollection={handleAddToCollection}
          onRemove={handleRemove}
          onEdit={handleEdit}
          onDownload={handleDownload}
          onViewDetails={handleViewDetails}
          onBulkOperation={handleBulkOperation}
          onFilterByDirector={handleFilterByDirector}
          onFilterByActor={handleFilterByActor}
          onFilterByGenre={handleFilterByGenre}
          onFilterByTag={handleFilterByTag}
        />
      )}

      {/* Movies */}
      {library.movies.length > 0 && (
        <ContentCarouselEnhanced
          title="Movies"
          items={library.movies}
          pinnedItems={pinnedItems}
          onPlay={handlePlay}
          onPin={handlePin}
          onUnpin={handleUnpin}
          onAddToCollection={handleAddToCollection}
          onRemove={handleRemove}
          onEdit={handleEdit}
          onDownload={handleDownload}
          onViewDetails={handleViewDetails}
          onBulkOperation={handleBulkOperation}
          onFilterByDirector={handleFilterByDirector}
          onFilterByActor={handleFilterByActor}
          onFilterByGenre={handleFilterByGenre}
          onFilterByTag={handleFilterByTag}
        />
      )}

      {/* Recently Added */}
      {library.recentlyAdded.length > 0 && (
        <ContentCarouselEnhanced
          title="Recently Added"
          items={library.recentlyAdded}
          pinnedItems={pinnedItems}
          onPlay={handlePlay}
          onPin={handlePin}
          onUnpin={handleUnpin}
          onAddToCollection={handleAddToCollection}
          onRemove={handleRemove}
          onEdit={handleEdit}
          onDownload={handleDownload}
          onViewDetails={handleViewDetails}
          onBulkOperation={handleBulkOperation}
          onFilterByDirector={handleFilterByDirector}
          onFilterByActor={handleFilterByActor}
          onFilterByGenre={handleFilterByGenre}
          onFilterByTag={handleFilterByTag}
        />
      )}

      {/* Empty State */}
      {!library.tvShows.length && !library.movies.length && !library.recentlyAdded.length && (
        <div className="px-8 py-24 text-center">
          <h2 className="text-2xl text-white/60 mb-4">Your library is empty</h2>
          <p className="text-white/40">Add some content to get started</p>
        </div>
      )}
    </div>
  );
};

export default LibraryPage;
