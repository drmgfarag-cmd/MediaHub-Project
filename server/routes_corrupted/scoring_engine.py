from flask import Blueprint, jsonify, request
import os, json, re
from datetime import datetime

scoring_bp = Blueprint('scoring', __name__)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STO = os.path.join(ROOT, 'storage')
PROFILES_PATH = os.path.join(STO, 'config', 'scoring_profiles.json')

def _load_profiles():
    """Load scoring profiles from configuration"""
    try:
        with open(PROFILES_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)
    except Exception:
        return {
            "default_profile": "balanced",
            "profiles": {}
        }

def _save_profiles(data):
    """Save scoring profiles to configuration"""
    os.makedirs(os.path.dirname(PROFILES_PATH), exist_ok=True)
    tmp_path = PROFILES_PATH + '.tmp'
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    os.replace(tmp_path, PROFILES_PATH)

def _parse_release_name(release_name):
    """
    Parse a release name to extract metadata fields
    Returns dict with: title, year, resolution, codec, audio, source, hdr, group, tags
    """
    metadata = {
        'title': '',
        'year': None,
        'resolution': None,
        'codec': None,
        'audio': None,
        'source': None,
        'hdr': None,
        'group': None,
        'tags': []
    }
    
    # Extract year
    year_match = re.search(r'\b(19\d{2}|20\d{2})\b', release_name)
    if year_match:
        metadata['year'] = year_match.group(1)
    
    # Extract resolution
    resolution_patterns = ['2160p', '1080p', '720p', '480p', '4K', 'UHD']
    for res in resolution_patterns:
        if res.upper() in release_name.upper():
            metadata['resolution'] = res if res not in ['4K', 'UHD'] else '2160p'
            break
    
    # Extract codec
    codec_patterns = ['HEVC', 'H265', 'H.265', 'x265', 'AVC', 'H264', 'H.264', 'x264', 'XviD']
    for codec in codec_patterns:
        if codec.upper() in release_name.upper().replace('.', ''):
            metadata['codec'] = codec
            break
    
    # Extract audio
    audio_patterns = ['Atmos', 'TrueHD', 'DTS-HD', 'DTS-HD.MA', 'DTS', 'DD+', 'DDP', 'DD', 'AC3', 'AAC', 'FLAC']
    for audio in audio_patterns:
        if audio.upper() in release_name.upper().replace('.', '-'):
            metadata['audio'] = audio
            break
    
    # Extract source
    source_patterns = ['Remux', 'BluRay', 'Blu-ray', 'BDRip', 'BRRip', 'WEB-DL', 'WEBRip', 'HDTV', 'DVDRip', 'CAM', 'TS', 'HDCAM']
    for source in source_patterns:
        if source.upper() in release_name.upper().replace('.', '-'):
            metadata['source'] = source
            break
    
    # Extract HDR info
    hdr_patterns = ['DV', 'DoVi', 'Dolby.Vision', 'HDR10+', 'HDR10', 'HDR']
    for hdr in hdr_patterns:
        if hdr.upper() in release_name.upper().replace('.', ''):
            metadata['hdr'] = hdr
            break
    
    # Extract release group (usually after the last dash)
    group_match = re.search(r'-([A-Za-z0-9]+)(?:\[.*?\])?$', release_name)
    if group_match:
        metadata['group'] = group_match.group(1)
    
    # Extract tags
    tag_patterns = ['PROPER', 'REPACK', 'INTERNAL', 'EXTENDED', 'UNRATED', 'DC', 'DIRECTORS.CUT']
    for tag in tag_patterns:
        if tag.upper() in release_name.upper().replace('.', ''):
            metadata['tags'].append(tag)
    
    # Extract title (everything before year or first quality indicator)
    title_match = re.match(r'^(.+?)(?:\.|\ )(?:19\d{2}|20\d{2}|2160p|1080p|720p|480p)', release_name)
    if title_match:
        metadata['title'] = title_match.group(1).replace('.', ' ').strip()
    else:
        metadata['title'] = release_name.split('.')[0]
    
    return metadata

def _evaluate_condition(metadata, condition):
    """
    Evaluate a single scoring condition against metadata
    Returns the score if condition matches, 0 otherwise
    """
    field = condition.get('field')
    operator = condition.get('operator')
    value = condition.get('value', '')
    score = condition.get('score', 0)
    
    field_value = metadata.get(field)
    
    if field_value is None:
        return 0
    
    # Convert to string for comparison
    field_value_str = str(field_value).upper()
    value_str = str(value).upper()
    
    if operator == 'equals':
        return score if field_value_str == value_str else 0
    elif operator == 'contains':
        if field == 'tags':
            # For tags, check if value is in the list
            return score if value_str in [t.upper() for t in field_value] else 0
        else:
            return score if value_str in field_value_str else 0
    elif operator == 'not_contains':
        if field == 'tags':
            return score if value_str not in [t.upper() for t in field_value] else 0
        else:
            return score if value_str not in field_value_str else 0
    elif operator == 'regex':
        try:
            return score if re.search(value, field_value_str, re.IGNORECASE) else 0
        except Exception:
            return 0
    
            return 0

def _calculate_score(metadata, profile):
    """
    Calculate total score for a release based on profile rules
    Returns dict with total score and breakdown by rule
    """
    total_score = 0
    breakdown = []
    
    for rule in profile.get('rules', []):
        rule_name = rule.get('name', 'Unnamed Rule')
        rule_score = 0
        matched_conditions = []
        
        for condition in rule.get('conditions', []):
            condition_score = _evaluate_condition(metadata, condition)
            if condition_score != 0:
                rule_score += condition_score
                matched_conditions.append({
                    'field': condition.get('field'),
                    'value': condition.get('value'),
                    'score': condition_score
                })
        
        if rule_score != 0:
            breakdown.append({
                'rule': rule_name,
                'score': rule_score,
                'matches': matched_conditions
            })
        
        total_score += rule_score
    
    return {
        'total_score': total_score,
        'breakdown': breakdown
    }

@scoring_bp.route('/api/scoring/profiles', methods=['GET'])
def get_profiles():
    try:
        """Get all scoring profiles"""
        profiles_data = _load_profiles()
        return jsonify({
        'ok': True,
        'default_profile': profiles_data.get('default_profile'),
        'profiles': profiles_data.get('profiles', {})
        })

        @scoring_bp.route('/api/scoring/profiles/<profile_name>', methods=['GET'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def get_profile(profile_name):
    try:
        """Get a specific scoring profile"""
        profiles_data = _load_profiles()
        profile = profiles_data.get('profiles', {}).get(profile_name)

        if not profile:
        return jsonify({'ok': False, 'error': 'Profile not found'}), 404

        return jsonify({
        'ok': True,
        'profile_name': profile_name,
        'profile': profile
        })

        # DUPLICATE REMOVED: @scoring_bp.route('/api/scoring/profiles', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def create_scoring_profiles():
    """Create Profiles"""
    try:
        data = request.get_json()
        if not data:
        return jsonify({'error': 'No data provided'}), 400
        return jsonify({'success': True, 'message': 'Created', 'data': data}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
def create_scoring_profiles():
    """Create Profiles"""
    try:
        data = request.get_json()
        if not data:
        return jsonify({'error': 'No data provided'}), 400
        return jsonify({'success': True, 'message': 'Created', 'data': data}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
# DUPLICATE REMOVED: def create_profile():
    """Create or update a scoring profile"""
    data = request.get_json(silent=True) or {}
    profile_name = data.get('profile_name')
    profile_data = data.get('profile')
    
    if not profile_name or not profile_data:
        return jsonify({'ok': False, 'error': 'profile_name and profile data required'}), 400
    
    profiles_data = _load_profiles()
    profiles_data['profiles'][profile_name] = profile_data
    _save_profiles(profiles_data)
    
    return jsonify({
        'ok': True,
        'message': f'Profile "{profile_name}" saved successfully'
    })

# DUPLICATE REMOVED: @scoring_bp.route('/api/scoring/profiles/<profile_name>', methods=['DELETE'])
# DUPLICATE REMOVED: def delete_profile(profile_name):
# DUPLICATE REMOVED:     """Delete a scoring profile"""
# DUPLICATE REMOVED:     profiles_data = _load_profiles()
# DUPLICATE REMOVED:     
# DUPLICATE REMOVED:     if profile_name not in profiles_data.get('profiles', {}):
# DUPLICATE REMOVED:         return jsonify({'ok': False, 'error': 'Profile not found'}), 404
# DUPLICATE REMOVED:     
# DUPLICATE REMOVED:     del profiles_data['profiles'][profile_name]
# DUPLICATE REMOVED:     _save_profiles(profiles_data)
# DUPLICATE REMOVED:     
# DUPLICATE REMOVED:     return jsonify({
# DUPLICATE REMOVED:         'ok': True,
# DUPLICATE REMOVED:         'message': f'Profile "{profile_name}" deleted successfully'
# DUPLICATE REMOVED:     })
# DUPLICATE REMOVED: 
# DUPLICATE REMOVED: @scoring_bp.route('/api/scoring/set-default', methods=['POST'])
# DUPLICATE REMOVED: def set_default_profile():
    """Set the default scoring profile"""
    data = request.get_json(silent=True) or {}
    profile_name = data.get('profile_name')
    
    if not profile_name:
        return jsonify({'ok': False, 'error': 'profile_name required'}), 400
    
    profiles_data = _load_profiles()
    
    if profile_name not in profiles_data.get('profiles', {}):
        return jsonify({'ok': False, 'error': 'Profile not found'}), 404
    
    profiles_data['default_profile'] = profile_name
    _save_profiles(profiles_data)
    
    return jsonify({
        'ok': True,
        'message': f'Default profile set to "{profile_name}"'
    })


@scoring_bp.route('/api/scoring/score', methods=['POST'])
def score_release():
    try:
        """
        Score a single release or list of releases
        Body: {
        "releases": ["Release.Name.2024.1080p.BluRay.x264-GROUP", ...],
        "profile": "balanced" (optional, uses default if not specified)
        }
        """
        data = request.get_json(silent=True) or {}
        releases = data.get('releases', [])
        profile_name = data.get('profile')

        if not releases:
        return jsonify({'ok': False, 'error': 'releases array required'}), 400

        # Ensure releases is a list
        if isinstance(releases, str):
        releases = [releases]

        profiles_data = _load_profiles()

        # Use specified profile or default
        if not profile_name:
        profile_name = profiles_data.get('default_profile', 'balanced')

        profile = profiles_data.get('profiles', {}).get(profile_name)
        if not profile:
        return jsonify({'ok': False, 'error': f'Profile "{profile_name}" not found'}), 404

        # Score each release
        results = []
        for release_name in releases:
        metadata = _parse_release_name(release_name)
        score_data = _calculate_score(metadata, profile)

        results.append({
        'release_name': release_name,
        'metadata': metadata,
        'score': score_data['total_score'],
        'breakdown': score_data['breakdown']
        })

        # Sort by score (highest first)
        results.sort(key=lambda x: x['score'], reverse=True)

        return jsonify({
        'ok': True,
        'profile_used': profile_name,
        'total_releases': len(results),
        'results': results
        })

        @scoring_bp.route('/api/scoring/parse', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def parse_release():
    try:
        """
        Parse release name(s) to extract metadata without scoring
        Body: {
        "releases": ["Release.Name.2024.1080p.BluRay.x264-GROUP", ...]
        }
        """
        data = request.get_json(silent=True) or {}
        releases = data.get('releases', [])

        if not releases:
        return jsonify({'ok': False, 'error': 'releases array required'}), 400

        # Ensure releases is a list
        if isinstance(releases, str):
        releases = [releases]

        results = []
        for release_name in releases:
        metadata = _parse_release_name(release_name)
        results.append({
        'release_name': release_name,
        'metadata': metadata
        })

        return jsonify({
        'ok': True,
        'total_releases': len(results),
        'results': results
        })

        @scoring_bp.route('/api/scoring/why-matched/<profile_name>', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def why_matched(profile_name):
    try:
        """
        Explain why a release matched and show detailed scoring breakdown
        Body: {
        "release": "Release.Name.2024.1080p.BluRay.x264-GROUP"
        }
        """
        data = request.get_json(silent=True) or {}
        release_name = data.get('release')

        if not release_name:
        return jsonify({'ok': False, 'error': 'release name required'}), 400

        profiles_data = _load_profiles()
        profile = profiles_data.get('profiles', {}).get(profile_name)

        if not profile:
        return jsonify({'ok': False, 'error': f'Profile "{profile_name}" not found'}), 404

        metadata = _parse_release_name(release_name)
        score_data = _calculate_score(metadata, profile)

        return jsonify({
        'ok': True,
        'release_name': release_name,
        'profile_name': profile_name,
        'profile_description': profile.get('description', ''),
        'metadata': metadata,
        'total_score': score_data['total_score'],
        'breakdown': score_data['breakdown'],
        'explanation': f"This release scored {score_data['total_score']} points using the '{profile_name}' profile."
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
