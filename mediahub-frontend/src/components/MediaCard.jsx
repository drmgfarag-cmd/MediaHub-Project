import React, { useState } from 'react';
import { 
  Play, Plus, ThumbsUp, ChevronDown, Info, 
  Pin, PinOff, Trash2, Edit, FolderPlus, 
  Download, Share2, Star, Check 
} from 'lucide-react';
import {
  ContextMenu,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuSeparator,
  ContextMenuSub,
  ContextMenuSubContent,
  ContextMenuSubTrigger,
  ContextMenuTrigger,
} from './ui/context-menu';

/**
 * Enhanced MediaCard Component with Context Menu Integration
 * 
 * Features:
 * - Right-click context menu
 * - Multi-select support
 * - Clickable metadata (directors, actors, genres, tags)
 * - Pin/unpin functionality
 * - Collection management
 * - Bulk operations
 */
const MediaCard = ({ 
  item, 
  isSelected = false,
  isPinned = false,
  onSelect,
  onPlay,
  onPin,
  onUnpin,
  onAddToCollection,
  onRemove,
  onEdit,
  onDownload,
  onViewDetails,
  onClickDirector,
  onClickActor,
  onClickGenre,
  onClickTag,
  multiSelectMode = false
}) => {
  const [isHovered, setIsHovered] = useState(false);

  const handleCardClick = (e) => {
    if (multiSelectMode) {
      e.preventDefault();
      onSelect?.(item.id);
    }
  };

  const handleMetadataClick = (e, type, value) => {
    e.stopPropagation();
    switch(type) {
      case 'director':
        onClickDirector?.(value);
        break;
      case 'actor':
        onClickActor?.(value);
        break;
      case 'genre':
        onClickGenre?.(value);
        break;
      case 'tag':
        onClickTag?.(value);
        break;
    }
  };

  return (
    <ContextMenu>
      <ContextMenuTrigger>
        <div
          className={`relative flex-shrink-0 w-[200px] transition-all duration-300 hover:scale-110 hover:z-10 cursor-pointer ${
            isSelected ? 'ring-2 ring-blue-500' : ''
          }`}
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
          onClick={handleCardClick}
        >
          {/* Selection Checkbox (Multi-select Mode) */}
          {multiSelectMode && (
            <div className="absolute top-2 left-2 z-30">
              <div className={`w-6 h-6 rounded-full flex items-center justify-center ${
                isSelected ? 'bg-blue-500' : 'bg-black/60 border-2 border-white/60'
              }`}>
                {isSelected && <Check className="w-4 h-4 text-white" />}
              </div>
            </div>
          )}

          {/* Pin Indicator */}
          {isPinned && (
            <div className="absolute top-2 right-2 z-30">
              <div className="bg-yellow-500 rounded-full p-1.5">
                <Pin className="w-3 h-3 text-white fill-current" />
              </div>
            </div>
          )}

          {/* Poster */}
          <div className="relative aspect-[2/3] rounded-md overflow-hidden">
            <img
              src={item.poster || item.thumbnail || '/placeholder-poster.jpg'}
              alt={item.title}
              className="w-full h-full object-cover"
              loading="lazy"
            />
            
            {/* Hover Overlay */}
            {isHovered && !multiSelectMode && (
              <div className="absolute inset-0 bg-gradient-to-t from-black via-black/50 to-transparent flex flex-col justify-end p-3 animate-in fade-in duration-200">
                {/* Quick Actions */}
                <div className="flex gap-2 mb-2">
                  <button 
                    onClick={(e) => { e.stopPropagation(); onPlay?.(item); }}
                    className="bg-white text-black rounded-full p-2 hover:bg-white/90 transition-colors"
                    title="Play"
                  >
                    <Play className="w-4 h-4 fill-current" />
                  </button>
                  <button 
                    onClick={(e) => { e.stopPropagation(); onAddToCollection?.(item); }}
                    className="bg-gray-800/80 text-white rounded-full p-2 hover:bg-gray-700/80 transition-colors"
                    title="Add to Collection"
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                  <button 
                    onClick={(e) => { e.stopPropagation(); /* Handle like */ }}
                    className="bg-gray-800/80 text-white rounded-full p-2 hover:bg-gray-700/80 transition-colors"
                    title="Like"
                  >
                    <ThumbsUp className="w-4 h-4" />
                  </button>
                  <button 
                    onClick={(e) => { e.stopPropagation(); onViewDetails?.(item); }}
                    className="bg-gray-800/80 text-white rounded-full p-2 hover:bg-gray-700/80 transition-colors ml-auto"
                    title="More Info"
                  >
                    <ChevronDown className="w-4 h-4" />
                  </button>
                </div>

                {/* Info */}
                <div className="space-y-1">
                  {/* Rating, Year, Maturity */}
                  <div className="flex items-center gap-2 text-xs text-white/90">
                    {item.rating && (
                      <span className="text-green-400 font-semibold flex items-center gap-1">
                        <Star className="w-3 h-3 fill-current" />
                        {item.rating}
                      </span>
                    )}
                    {item.year && <span>{item.year}</span>}
                    {item.maturity && (
                      <span className="border border-white/40 px-1">{item.maturity}</span>
                    )}
                  </div>

                  {/* Seasons/Duration */}
                  {item.seasons && (
                    <div className="text-xs text-white/80">{item.seasons}</div>
                  )}
                  {item.duration && (
                    <div className="text-xs text-white/80">{item.duration}</div>
                  )}

                  {/* Clickable Genres */}
                  {item.genres && item.genres.length > 0 && (
                    <div className="flex gap-1 flex-wrap">
                      {item.genres.slice(0, 3).map((genre, index) => (
                        <button
                          key={index}
                          onClick={(e) => handleMetadataClick(e, 'genre', genre)}
                          className="text-xs text-white/70 hover:text-white hover:underline transition-colors"
                        >
                          {genre}
                          {index < Math.min(item.genres.length, 3) - 1 && ' •'}
                        </button>
                      ))}
                    </div>
                  )}

                  {/* Clickable Director */}
                  {item.director && (
                    <button
                      onClick={(e) => handleMetadataClick(e, 'director', item.director)}
                      className="text-xs text-white/70 hover:text-white hover:underline transition-colors block"
                    >
                      Dir: {item.director}
                    </button>
                  )}

                  {/* Clickable Actors */}
                  {item.actors && item.actors.length > 0 && (
                    <div className="flex gap-1 flex-wrap">
                      {item.actors.slice(0, 2).map((actor, index) => (
                        <button
                          key={index}
                          onClick={(e) => handleMetadataClick(e, 'actor', actor)}
                          className="text-xs text-white/70 hover:text-white hover:underline transition-colors"
                        >
                          {actor}
                          {index < Math.min(item.actors.length, 2) - 1 && ','}
                        </button>
                      ))}
                    </div>
                  )}

                  {/* Clickable Tags */}
                  {item.tags && item.tags.length > 0 && (
                    <div className="flex gap-1 flex-wrap mt-1">
                      {item.tags.slice(0, 3).map((tag, index) => (
                        <button
                          key={index}
                          onClick={(e) => handleMetadataClick(e, 'tag', tag)}
                          className="text-xs bg-white/10 hover:bg-white/20 px-1.5 py-0.5 rounded transition-colors"
                        >
                          #{tag}
                        </button>
                      ))}
                    </div>
                  )}
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
      </ContextMenuTrigger>

      {/* Context Menu */}
      <ContextMenuContent className="w-56">
        <ContextMenuItem onClick={() => onPlay?.(item)}>
          <Play className="mr-2 h-4 w-4" />
          <span>Play</span>
        </ContextMenuItem>
        
        <ContextMenuItem onClick={() => onViewDetails?.(item)}>
          <Info className="mr-2 h-4 w-4" />
          <span>View Details</span>
        </ContextMenuItem>

        <ContextMenuSeparator />

        {isPinned ? (
          <ContextMenuItem onClick={() => onUnpin?.(item)}>
            <PinOff className="mr-2 h-4 w-4" />
            <span>Unpin</span>
          </ContextMenuItem>
        ) : (
          <ContextMenuItem onClick={() => onPin?.(item)}>
            <Pin className="mr-2 h-4 w-4" />
            <span>Pin to Top</span>
          </ContextMenuItem>
        )}

        <ContextMenuSub>
          <ContextMenuSubTrigger>
            <FolderPlus className="mr-2 h-4 w-4" />
            <span>Add to Collection</span>
          </ContextMenuSubTrigger>
          <ContextMenuSubContent className="w-48">
            <ContextMenuItem onClick={() => onAddToCollection?.(item, 'favorites')}>
              Favorites
            </ContextMenuItem>
            <ContextMenuItem onClick={() => onAddToCollection?.(item, 'watchlist')}>
              Watch Later
            </ContextMenuItem>
            <ContextMenuItem onClick={() => onAddToCollection?.(item, 'new')}>
              <Plus className="mr-2 h-4 w-4" />
              New Collection...
            </ContextMenuItem>
          </ContextMenuSubContent>
        </ContextMenuSub>

        <ContextMenuSeparator />

        <ContextMenuItem onClick={() => onEdit?.(item)}>
          <Edit className="mr-2 h-4 w-4" />
          <span>Edit Metadata</span>
        </ContextMenuItem>

        <ContextMenuItem onClick={() => onDownload?.(item)}>
          <Download className="mr-2 h-4 w-4" />
          <span>Download</span>
        </ContextMenuItem>

        <ContextMenuItem onClick={() => navigator.clipboard.writeText(item.title)}>
          <Share2 className="mr-2 h-4 w-4" />
          <span>Copy Title</span>
        </ContextMenuItem>

        <ContextMenuSeparator />

        <ContextMenuItem 
          variant="destructive"
          onClick={() => onRemove?.(item)}
        >
          <Trash2 className="mr-2 h-4 w-4" />
          <span>Remove from Library</span>
        </ContextMenuItem>
      </ContextMenuContent>
    </ContextMenu>
  );
};

export default MediaCard;
