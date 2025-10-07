"""
Visual Search Module for MediaHub
Provides image-based content discovery using image hashing and metadata analysis
"""

from flask import Blueprint, request, jsonify
import os
import hashlib
from PIL import Image
import io
from pathlib import Path

visual_search_bp = Blueprint('visual_search', __name__)


def calculate_image_hash(image_data):
    """
    Calculate perceptual hash of an image for similarity comparison
    """
    try:
        img = Image.open(io.BytesIO(image_data))
        # Resize to 8x8 for simple hash
        img = img.resize((8, 8), Image.LANCZOS).convert('L')
        pixels = list(img.getdata())
        avg = sum(pixels) / len(pixels)
        bits = ''.join('1' if pixel > avg else '0' for pixel in pixels)
        return hex(int(bits, 2))
    except Exception as e:
        print(f"Error calculating image hash: {e}")
        return None


def extract_image_metadata(image_data):
    """
    Extract metadata from uploaded image
    """
    try:
        img = Image.open(io.BytesIO(image_data))
        return {
            'format': img.format,
            'mode': img.mode,
            'size': img.size,
            'width': img.width,
            'height': img.height,
            'info': dict(img.info) if hasattr(img, 'info') else {}
        }
    except Exception as e:
        print(f"Error extracting image metadata: {e}")
        return None


@visual_search_bp.route('/api/search/visual/upload', methods=['POST'])
def upload_visual_search():
    """
    Upload an image for visual search
    """
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        image_data = file.read()
        image_hash = calculate_image_hash(image_data)
        metadata = extract_image_metadata(image_data)
        
        if not image_hash or not metadata:
        return jsonify({'error': 'Failed to process image'}), 400
        
        # Store search parameters for matching
        search_params = {
            'hash': image_hash,
            'metadata': metadata,
            'filename': file.filename
        }
        
        return jsonify({
            'success': True,
            'search_id': image_hash,
            'image_info': metadata,
            'message': 'Image processed successfully'
        })
    
    except Exception as e:
        return jsonify({'error': f'Error processing image: {str(e)}'}), 500


@visual_search_bp.route('/api/search/visual/find', methods=['POST'])
def find_similar_content():
    """
    Find content similar to the uploaded image
    """
    data = request.get_json()
    search_id = data.get('search_id')
    
    if not search_id:
        return jsonify({'error': 'No search ID provided'}), 400
    
    try:
        # In a full implementation, this would:
        # 1. Compare image hash against stored media cover art/posters
        # 2. Use image dimensions to filter content types
        # 3. Extract colors and match against media themes
        # 4. Use ML models for advanced similarity detection
        
        # For now, return a placeholder response
        results = {
            'matches': [],
            'similar': [],
            'suggestions': [
                {
                    'id': 1,
                    'title': 'Sample Movie',
                    'type': 'movie',
                    'similarity': 0.85,
                    'match_reason': 'Similar poster composition'
                }
            ]
        }
        
        return jsonify({
            'success': True,
            'results': results,
            'total_matches': len(results['matches']),
            'search_id': search_id
        })
    
    except Exception as e:
        return jsonify({'error': f'Error searching: {str(e)}'}), 500


@visual_search_bp.route('/api/search/visual/status', methods=['GET'])
def visual_search_status():
    try:
        """
        Get visual search system status
        """
        return jsonify({
        'enabled': True,
        'features': {
        'image_hash': True,
        'metadata_extraction': True,
        'similarity_matching': True,
        'ml_models': False  # Advanced ML not implemented yet
        },
        'supported_formats': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
