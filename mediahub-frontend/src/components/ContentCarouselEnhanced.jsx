import React, { useState, useRef } from 'react';
import { ChevronLeft, ChevronRight, CheckSquare, X, Pin, FolderPlus, Trash2, Edit } from 'lucide-react';
import MediaCard from './MediaCard';
import { Button } from './ui/button';

/**
 * Enhanced ContentCarousel with Multi-Select and Bulk Operations
 * 
 * Features:
 * - Multi-select mode
 * - Bulk operations toolbar
 * - Pinned items section
 * - Context menu integration
 * - Clickable metadata filtering
 */
const ContentCarouselEnhanced = ({ 
  title, 
  items = [],
  pinnedItems = [],
  onPlay,
  onPin,
  onUnpin,
  onAddToCollection,
  onRemove,
  onEdit,
  onDownload,
  onViewDetails,
  onBulkOperation,
  onFilterByDirector,
  onFilterByActor,
  onFilterByGenre,
  onFilterByTag,
}) => {
  const [scrollPosition, setScrollPosition] = useState(0);
  const [multiSelectMode, setMultiSelectMode] = useState(false);
  const [selectedItems, setSelectedItems] = useState(new Set());
  const carouselRef = useRef(null);

  const displayItems = items.length > 0 ? items : [];
  const hasPinnedItems = pinnedItems && pinnedItems.length > 0;

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

  const toggleMultiSelect = () => {
    setMultiSelectMode(!multiSelectMode);
    setSelectedItems(new Set());
  };

  const toggleItemSelection = (itemId) => {
    const newSelected = new Set(selectedItems);
    if (newSelected.has(itemId)) {
      newSelected.delete(itemId);
    } else {
      newSelected.add(itemId);
    }
    setSelectedItems(newSelected);
  };

  const selectAll = () => {
    const allIds = new Set(displayItems.map(item => item.id));
    setSelectedItems(allIds);
  };

  const deselectAll = () => {
    setSelectedItems(new Set());
  };

  const handleBulkOperation = (operation) => {
    const selectedItemsArray = displayItems.filter(item => selectedItems.has(item.id));
    onBulkOperation?.(operation, selectedItemsArray);
    setSelectedItems(new Set());
    setMultiSelectMode(false);
  };

  return (
    <div className="relative group mb-12">
      {/* Header with Title and Multi-Select Toggle */}
      <div className="flex items-center justify-between mb-4 px-8">
        <h2 className="text-2xl font-bold text-white">{title}</h2>
        <Button
          variant={multiSelectMode ? "default" : "outline"}
          size="sm"
          onClick={toggleMultiSelect}
          className="gap-2"
        >
          <CheckSquare className="w-4 h-4" />
          {multiSelectMode ? 'Cancel' : 'Select'}
        </Button>
      </div>

      {/* Bulk Operations Toolbar */}
      {multiSelectMode && selectedItems.size > 0 && (
        <div className="bg-blue-600 text-white px-8 py-3 mb-4 flex items-center justify-between animate-in slide-in-from-top duration-200">
          <div className="flex items-center gap-4">
            <span className="font-semibold">{selectedItems.size} selected</span>
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={selectAll}
              className="text-white hover:text-white hover:bg-blue-700"
            >
              Select All
            </Button>
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={deselectAll}
              className="text-white hover:text-white hover:bg-blue-700"
            >
              Deselect All
            </Button>
          </div>
          
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleBulkOperation('pin')}
              className="text-white hover:text-white hover:bg-blue-700 gap-2"
            >
              <Pin className="w-4 h-4" />
              Pin
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleBulkOperation('addToCollection')}
              className="text-white hover:text-white hover:bg-blue-700 gap-2"
            >
              <FolderPlus className="w-4 h-4" />
              Add to Collection
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleBulkOperation('edit')}
              className="text-white hover:text-white hover:bg-blue-700 gap-2"
            >
              <Edit className="w-4 h-4" />
              Edit
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleBulkOperation('remove')}
              className="text-white hover:text-white hover:bg-red-700 gap-2"
            >
              <Trash2 className="w-4 h-4" />
              Remove
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleMultiSelect}
              className="text-white hover:text-white hover:bg-blue-700"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>
      )}

      {/* Pinned Items Section */}
      {hasPinnedItems && !multiSelectMode && (
        <div className="px-8 mb-6">
          <h3 className="text-lg font-semibold text-yellow-400 mb-3 flex items-center gap-2">
            <Pin className="w-4 h-4 fill-current" />
            Pinned
          </h3>
          <div className="flex gap-2 overflow-x-auto pb-2">
            {pinnedItems.map((item) => (
              <MediaCard
                key={item.id}
                item={item}
                isPinned={true}
                onPlay={onPlay}
                onPin={onPin}
                onUnpin={onUnpin}
                onAddToCollection={onAddToCollection}
                onRemove={onRemove}
                onEdit={onEdit}
                onDownload={onDownload}
                onViewDetails={onViewDetails}
                onClickDirector={onFilterByDirector}
                onClickActor={onFilterByActor}
                onClickGenre={onFilterByGenre}
                onClickTag={onFilterByTag}
              />
            ))}
          </div>
        </div>
      )}

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
            <MediaCard
              key={item.id}
              item={item}
              isSelected={selectedItems.has(item.id)}
              isPinned={pinnedItems?.some(p => p.id === item.id)}
              onSelect={toggleItemSelection}
              onPlay={onPlay}
              onPin={onPin}
              onUnpin={onUnpin}
              onAddToCollection={onAddToCollection}
              onRemove={onRemove}
              onEdit={onEdit}
              onDownload={onDownload}
              onViewDetails={onViewDetails}
              onClickDirector={onFilterByDirector}
              onClickActor={onFilterByActor}
              onClickGenre={onFilterByGenre}
              onClickTag={onFilterByTag}
              multiSelectMode={multiSelectMode}
            />
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

      {/* Empty State */}
      {displayItems.length === 0 && (
        <div className="px-8 py-12 text-center text-gray-400">
          <p>No items to display</p>
        </div>
      )}
    </div>
  );
};

export default ContentCarouselEnhanced;
