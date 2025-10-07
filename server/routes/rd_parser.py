from flask import Blueprint, jsonify, request
from .security import require_api_key
import re
import urllib.parse
import base64
import bencodepy  # For torrent parsing
from typing import List, Dict, Optional

rd_parser_bp = Blueprint('rd_parser', __name__)

class RDLinksParser:
    """Parse Real-Debrid links and extract torrent information"""
    
    @staticmethod
    def parse_magnet_link(magnet: str) -> Dict:
        """Extract information from magnet link"""
        try:
            # Extract infohash
            infohash_match = re.search(r'urn:btih:([a-fA-F0-9]{40})', magnet)
            infohash = infohash_match.group(1) if infohash_match else None
            
            # Extract display name
            dn_match = re.search(r'dn=([^&]+)', magnet)
            display_name = urllib.parse.unquote(dn_match.group(1)) if dn_match else None
            
            # Extract trackers
            trackers = re.findall(r'tr=([^&]+)', magnet)
            trackers = [urllib.parse.unquote(t) for t in trackers]
            
            return {
                'type': 'magnet',
                'infohash': infohash,
                'display_name': display_name,
                'trackers': trackers,
                'raw': magnet
            }
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def parse_torrent_file(torrent_data: bytes) -> Dict:
        """Extract information from .torrent file"""
        try:
            # Decode bencode
            torrent = bencodepy.decode(torrent_data)
            
            info = torrent.get(b'info', {})
            
            # Extract name
            name = info.get(b'name', b'').decode('utf-8', errors='ignore')
            
            # Extract files
            files = []
            if b'files' in info:
                # Multi-file torrent
                for f in info[b'files']:
                    path_parts = [p.decode('utf-8', errors='ignore') for p in f[b'path']]
                    files.append({
                        'path': '/'.join(path_parts),
                        'size': f[b'length']
                    })
            else:
                # Single file torrent
                files.append({
                    'path': name,
                    'size': info.get(b'length', 0)
                })
            
            # Calculate infohash
            import hashlib
            info_encoded = bencodepy.encode(info)
            infohash = hashlib.sha1(info_encoded).hexdigest()
            
            return {
                'type': 'torrent',
                'name': name,
                'infohash': infohash,
                'files': files,
                'total_size': sum(f['size'] for f in files),
                'file_count': len(files)
            }
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def extract_filenames_from_text(text: str) -> List[str]:
        """Extract potential filenames from text"""
        # Common video extensions
        video_extensions = r'\.(mkv|mp4|avi|mov|wmv|flv|webm|m4v|mpg|mpeg|m2ts|ts)'
        
        # Find all potential filenames
        pattern = r'[\w\-\.]+' + video_extensions
        matches = re.findall(pattern, text, re.IGNORECASE)
        
        return list(set(matches))  # Remove duplicates
    
    @staticmethod
    def parse_rd_link(link: str) -> Dict:
        """Parse Real-Debrid download link"""
        try:
            # Extract filename from URL
            parsed = urllib.parse.urlparse(link)
            path = parsed.path
            filename = path.split('/')[-1]
            filename = urllib.parse.unquote(filename)
            
            return {
                'type': 'rd_link',
                'url': link,
                'filename': filename,
                'host': parsed.netloc
            }
        except Exception as e:
            return {'error': str(e)}

class FilenameComparator:
    """Compare extracted filenames with input lists"""
    
    @staticmethod
    def normalize_filename(filename: str) -> str:
        """Normalize filename for comparison"""
        # Remove extension
        name = re.sub(r'\.\w+$', '', filename)
        # Convert to lowercase
        name = name.lower()
        # Remove special characters
        name = re.sub(r'[^\w\s]', ' ', name)
        # Normalize whitespace
        name = ' '.join(name.split())
        return name
    
    @staticmethod
    def extract_quality_tokens(filename: str) -> Dict:
        """Extract quality information from filename"""
        tokens = {
            'resolution': None,
            'source': None,
            'codec': None,
            'audio': None,
            'hdr': None,
            'group': None
        }
        
        # Resolution
        res_match = re.search(r'(2160p|1080p|720p|480p|4K|8K)', filename, re.IGNORECASE)
        if res_match:
            tokens['resolution'] = res_match.group(1).upper()
        
        # Source
        source_match = re.search(r'(WEB-DL|WEBRip|BluRay|BRRip|DVDRip|HDTV)', filename, re.IGNORECASE)
        if source_match:
            tokens['source'] = source_match.group(1).upper()
        
        # Codec
        codec_match = re.search(r'(H\.?264|H\.?265|x264|x265|HEVC|AVC)', filename, re.IGNORECASE)
        if codec_match:
            tokens['codec'] = codec_match.group(1).upper()
        
        # Audio
        audio_match = re.search(r'(DDP5\.1|DD5\.1|AAC|AC3|DTS|Atmos|TrueHD)', filename, re.IGNORECASE)
        if audio_match:
            tokens['audio'] = audio_match.group(1).upper()
        
        # HDR
        hdr_match = re.search(r'(HDR|HDR10|DV|Dolby\.?Vision)', filename, re.IGNORECASE)
        if hdr_match:
            tokens['hdr'] = hdr_match.group(1).upper()
        
        # Release group
        group_match = re.search(r'-([A-Za-z0-9]+)(?:\.\w+)?$', filename)
        if group_match:
            tokens['group'] = group_match.group(1)
        
        return tokens
    
    @staticmethod
    def compare_filenames(input_list: List[str], extracted_list: List[str]) -> Dict:
        """Compare two lists of filenames and find matches"""
        matches = []
        missing_from_extracted = []
        extra_in_extracted = []
        
        # Normalize all filenames
        input_normalized = {f: FilenameComparator.normalize_filename(f) for f in input_list}
        extracted_normalized = {f: FilenameComparator.normalize_filename(f) for f in extracted_list}
        
        # Find matches
        for input_file, input_norm in input_normalized.items():
            found = False
            for extracted_file, extracted_norm in extracted_normalized.items():
                # Simple substring match
                if input_norm in extracted_norm or extracted_norm in input_norm:
                    matches.append({
                        'input': input_file,
                        'extracted': extracted_file,
                        'confidence': 'high' if input_norm == extracted_norm else 'medium',
                        'input_tokens': FilenameComparator.extract_quality_tokens(input_file),
                        'extracted_tokens': FilenameComparator.extract_quality_tokens(extracted_file)
                    })
                    found = True
                    break
            
            if not found:
                missing_from_extracted.append(input_file)
        
        # Find extras
        matched_extracted = {m['extracted'] for m in matches}
        extra_in_extracted = [f for f in extracted_list if f not in matched_extracted]
        
        return {
            'matches': matches,
            'missing_from_extracted': missing_from_extracted,
            'extra_in_extracted': extra_in_extracted,
            'match_rate': len(matches) / len(input_list) if input_list else 0
        }

# API Endpoints

@rd_parser_bp.route("/api/rd/parse/magnet", methods=["POST"])
@require_api_key
def parse_magnet():
    """Parse magnet link"""
    data = request.get_json() or {}
    magnet = data.get('magnet', '')
    
    if not magnet:
        return jsonify({'error': 'No magnet link provided'}), 400
    
    result = RDLinksParser.parse_magnet_link(magnet)
    return jsonify(result)

@rd_parser_bp.route("/api/rd/parse/torrent", methods=["POST"])
@require_api_key
def parse_torrent():
    """Parse torrent file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    torrent_data = file.read()
    
    result = RDLinksParser.parse_torrent_file(torrent_data)
    return jsonify(result)

@rd_parser_bp.route("/api/rd/parse/text", methods=["POST"])
@require_api_key
def parse_text():
    """Extract filenames from text"""
    data = request.get_json() or {}
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    filenames = RDLinksParser.extract_filenames_from_text(text)
    return jsonify({'filenames': filenames, 'count': len(filenames)})

@rd_parser_bp.route("/api/rd/parse/link", methods=["POST"])
@require_api_key
def parse_link():
    """Parse RD download link"""
    data = request.get_json() or {}
    link = data.get('link', '')
    
    if not link:
        return jsonify({'error': 'No link provided'}), 400
    
    result = RDLinksParser.parse_rd_link(link)
    return jsonify(result)

@rd_parser_bp.route("/api/rd/compare", methods=["POST"])
@require_api_key
def compare_lists():
    """Compare input list with extracted filenames"""
    data = request.get_json() or {}
    input_list = data.get('input_list', [])
    extracted_list = data.get('extracted_list', [])
    
    if not input_list or not extracted_list:
        return jsonify({'error': 'Both input_list and extracted_list are required'}), 400
    
    result = FilenameComparator.compare_filenames(input_list, extracted_list)
    return jsonify(result)

@rd_parser_bp.route("/api/rd/parse/batch", methods=["POST"])
@require_api_key
def parse_batch():
    """Parse multiple links/magnets at once"""
    data = request.get_json() or {}
    items = data.get('items', [])
    
    if not items:
        return jsonify({'error': 'No items provided'}), 400
    
    results = []
    for item in items:
        if item.startswith('magnet:'):
            result = RDLinksParser.parse_magnet_link(item)
            result['input'] = item
            results.append(result)
        elif item.startswith('http'):
            result = RDLinksParser.parse_rd_link(item)
            result['input'] = item
            results.append(result)
    
    return jsonify({
        'results': results,
        'total': len(results),
        'success': len([r for r in results if 'error' not in r])
    })
