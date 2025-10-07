from flask import Blueprint, jsonify, request
import os, json
from datetime import datetime

scene_groups_bp = Blueprint('scene_groups', __name__)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STO = os.path.join(ROOT, 'storage')
SCENE_GROUPS_PATH = os.path.join(STO, 'config', 'scene_groups.json')

def _load_scene_groups():
    """Load scene group policies"""
    try:
        with open(SCENE_GROUPS_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)
    except Exception:
        return {
            "default_policy": "UserDefined",
            "policies": {
                "UserDefined": {
                    "name": "User Defined",
                    "description": "Custom scene group preferences",
                    "preferred_groups": [],
                    "blocked_groups": [],
                    "auto_upgrade": True,
                    "keep_multiple_versions": False
                }
            },
            "upgrade_rules": {
                "check_interval_hours": 24,
                "min_score_improvement": 20,
                "preserve_watched_status": True,
                "auto_delete_old_version": False
            }
        }

def _save_scene_groups(data):
    """Save scene group policies"""
    os.makedirs(os.path.dirname(SCENE_GROUPS_PATH), exist_ok=True)
    tmp = SCENE_GROUPS_PATH + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, SCENE_GROUPS_PATH)

def _apply_scene_group_policy(release_name, policy):
    """
    Apply scene group policy to a release name
    Returns dict with: allowed, priority, reason
    """
    # Extract group from release name
    import re
    group_match = re.search(r'-([A-Za-z0-9]+)(?:\[.*?\])?$', release_name)
    
    if not group_match:
        return {
            'allowed': True,
            'priority': 0,
            'group': None,
            'reason': 'No group detected'
        }
    
    group_name = group_match.group(1)
    
    # Check if group is blocked
    blocked_groups = policy.get('blocked_groups', [])
    for blocked in blocked_groups:
        if blocked['name'].upper() == group_name.upper():
            return {
                'allowed': False,
                'priority': -1,
                'group': group_name,
                'reason': f"Blocked: {blocked.get('reason', 'No reason specified')}"
            }
    
    # Check if group is preferred
    preferred_groups = policy.get('preferred_groups', [])
    for preferred in preferred_groups:
        if preferred['name'].upper() == group_name.upper():
            return {
                'allowed': True,
                'priority': preferred.get('priority', 50),
                'group': group_name,
                'never_remove': preferred.get('never_remove', False),
                'reason': f"Preferred group: {preferred.get('notes', '')}"
            }
    
    # Group not in policy - allow with default priority
    return {
        'allowed': True,
        'priority': 50,
        'group': group_name,
        'reason': 'Group not in policy (default priority)'
    }

def _check_upgrade_eligibility(current_release, new_release, policy):
    """
    Check if new release is eligible for upgrade
    Returns dict with: eligible, reason, score_improvement
    """
    # Import scoring engine
    try:
        from routes.scoring_engine import _parse_release_name, _calculate_score, _load_profiles
        
        # Get scoring profile
        profiles_data = _load_profiles()
        scoring_profile = profiles_data.get('profiles', {}).get('balanced')
        
        if not scoring_profile:
        return {
                'eligible': False,
                'reason': 'Scoring profile not found',
                'score_improvement': 0
            }
        
        # Score both releases
        current_metadata = _parse_release_name(current_release)
        new_metadata = _parse_release_name(new_release)
        
        current_score_data = _calculate_score(current_metadata, scoring_profile)
        new_score_data = _calculate_score(new_metadata, scoring_profile)
        
        current_score = current_score_data['total_score']
        new_score = new_score_data['total_score']
        
        score_improvement = new_score - current_score
        min_improvement = policy.get('upgrade_rules', {}).get('min_score_improvement', 20)
        
        # Check if improvement meets threshold
        if score_improvement >= min_improvement:
            return {
                'eligible': True,
                'reason': f'Score improvement of {score_improvement} meets threshold of {min_improvement}',
                'score_improvement': score_improvement,
                'current_score': current_score,
                'new_score': new_score
            }
        else:
            return {
                'eligible': False,
                'reason': f'Score improvement of {score_improvement} below threshold of {min_improvement}',
                'score_improvement': score_improvement,
                'current_score': current_score,
                'new_score': new_score
            }
    
    except Exception as e:
        return {
            'eligible': False,
            'reason': f'Error checking upgrade eligibility: {str(e)}',
            'score_improvement': 0
        }

# ============================================================================
# Policy Management Endpoints
# ============================================================================

@scene_groups_bp.route('/api/scene-groups/policies', methods=['GET'])
def get_policies():
    try:
        """Get all scene group policies"""
        data = _load_scene_groups()
        return jsonify({
        'ok': True,
        'default_policy': data.get('default_policy'),
        'policies': data.get('policies', {}),
        'upgrade_rules': data.get('upgrade_rules', {})
        })

        @scene_groups_bp.route('/api/scene-groups/policies/<policy_name>', methods=['GET'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def get_policy(policy_name):
    try:
        """Get a specific scene group policy"""
        data = _load_scene_groups()
        policy = data.get('policies', {}).get(policy_name)

        if not policy:
        return jsonify({'ok': False, 'error': 'Policy not found'}), 404

        return jsonify({
        'ok': True,
        'policy_name': policy_name,
        'policy': policy
        })

        # DUPLICATE REMOVED: @scene_groups_bp.route('/api/scene-groups/policies', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def create_scene_groups_policies():
    """Create Policies"""
    try:
        data = request.get_json()
        if not data:
        return jsonify({'error': 'No data provided'}), 400
        return jsonify({'success': True, 'message': 'Created', 'data': data}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
def create_scene_groups_policies():
    """Create Policies"""
    try:
        data = request.get_json()
        if not data:
        return jsonify({'error': 'No data provided'}), 400
        return jsonify({'success': True, 'message': 'Created', 'data': data}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
# DUPLICATE REMOVED: def create_policy():
    """
    Create or update a scene group policy
    Body: {
        "policy_name": "MyPolicy",
        "policy": {
            "name": "My Policy",
            "description": "Description",
            "preferred_groups": [],
            "blocked_groups": [],
            "auto_upgrade": true,
            "keep_multiple_versions": false
        }
    }
    """
    req_data = request.get_json(silent=True) or {}
    policy_name = req_data.get('policy_name')
    policy_data = req_data.get('policy')
    
    if not policy_name or not policy_data:
        return jsonify({'ok': False, 'error': 'policy_name and policy data required'}), 400
    
    data = _load_scene_groups()
    data['policies'][policy_name] = policy_data
    _save_scene_groups(data)
    
    return jsonify({
        'ok': True,
        'message': f'Policy "{policy_name}" saved successfully'
    })

# DUPLICATE REMOVED: @scene_groups_bp.route('/api/scene-groups/policies/<policy_name>', methods=['DELETE'])
# DUPLICATE REMOVED: def delete_policy(policy_name):
    """Delete a scene group policy"""
    data = _load_scene_groups()
    
    if policy_name not in data.get('policies', {}):
        return jsonify({'ok': False, 'error': 'Policy not found'}), 404
    
    # Don't allow deleting the default policy
    if policy_name == data.get('default_policy'):
        return jsonify({'ok': False, 'error': 'Cannot delete the default policy'}), 400
    
    del data['policies'][policy_name]
    _save_scene_groups(data)
    
    return jsonify({
        'ok': True,
        'message': f'Policy "{policy_name}" deleted successfully'
    })


@scene_groups_bp.route('/api/scene-groups/set-default', methods=['POST'])
def set_default_policy():
    try:
        """
        Set the default scene group policy
        Body: {
        "policy_name": "UserDefined"
        }
        """
        req_data = request.get_json(silent=True) or {}
        policy_name = req_data.get('policy_name')

        if not policy_name:
        return jsonify({'ok': False, 'error': 'policy_name required'}), 400

        data = _load_scene_groups()

        if policy_name not in data.get('policies', {}):
        return jsonify({'ok': False, 'error': 'Policy not found'}), 404

        data['default_policy'] = policy_name
        _save_scene_groups(data)

        return jsonify({
        'ok': True,
        'message': f'Default policy set to "{policy_name}"'
        })

        # ============================================================================
        # Group Management Endpoints (NEW - Fully Editable)
        # ============================================================================

        @scene_groups_bp.route('/api/scene-groups/policies/<policy_name>/groups/preferred', methods=['GET'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def get_preferred_groups(policy_name):
    try:
        """Get all preferred groups for a policy"""
        data = _load_scene_groups()
        policy = data.get('policies', {}).get(policy_name)

        if not policy:
        return jsonify({'ok': False, 'error': 'Policy not found'}), 404

        # Sort by priority (highest first)
        preferred_groups = sorted(
        policy.get('preferred_groups', []),
        key=lambda x: x.get('priority', 0),
        reverse=True
        )

        return jsonify({
        'ok': True,
        'policy_name': policy_name,
        'preferred_groups': preferred_groups
        })

        # DUPLICATE REMOVED: @scene_groups_bp.route('/api/scene-groups/policies/<policy_name>/groups/preferred', methods=['POST'])
        # DUPLICATE REMOVED: def add_preferred_group(policy_name):
        """
        Add a new preferred group to a policy
        Body: {
        "name": "GroupName",
        "priority": 100,
        "never_remove": false,
        "notes": "Optional notes"
        }
        """
        req_data = request.get_json(silent=True) or {}
        group_name = req_data.get('name')

        if not group_name:
        return jsonify({'ok': False, 'error': 'Group name required'}), 400

        data = _load_scene_groups()
        policy = data.get('policies', {}).get(policy_name)

        if not policy:
        return jsonify({'ok': False, 'error': 'Policy not found'}), 404

        # Check if group already exists
        preferred_groups = policy.get('preferred_groups', [])
        for group in preferred_groups:
        if group['name'].upper() == group_name.upper():
        return jsonify({'ok': False, 'error': 'Group already exists in preferred list'}), 400

        # Add new group
        new_group = {
        'name': group_name,
        'priority': req_data.get('priority', 50),
        'never_remove': req_data.get('never_remove', False),
        'notes': req_data.get('notes', '')
        }

        preferred_groups.append(new_group)
        policy['preferred_groups'] = preferred_groups
        _save_scene_groups(data)

        return jsonify({
        'ok': True,
        'message': f'Group "{group_name}" added to preferred list',
        'group': new_group
        })


        @scene_groups_bp.route('/api/scene-groups/policies/<policy_name>/groups/preferred/<group_name>', methods=['PUT'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def update_preferred_group(policy_name, group_name):
    try:
        """
        Update an existing preferred group
        Body: {
        "priority": 100,
        "never_remove": false,
        "notes": "Updated notes"
        }
        """
        req_data = request.get_json(silent=True) or {}

        data = _load_scene_groups()
        policy = data.get('policies', {}).get(policy_name)

        if not policy:
        return jsonify({'ok': False, 'error': 'Policy not found'}), 404

        # Find and update the group
        preferred_groups = policy.get('preferred_groups', [])
        group_found = False

        for group in preferred_groups:
        if group['name'].upper() == group_name.upper():
        group_found = True
        # Update fields if provided
        if 'priority' in req_data:
        group['priority'] = req_data['priority']
        if 'never_remove' in req_data:
        group['never_remove'] = req_data['never_remove']
        if 'notes' in req_data:
        group['notes'] = req_data['notes']
        break

        if not group_found:
        return jsonify({'ok': False, 'error': 'Group not found in preferred list'}), 404

        _save_scene_groups(data)

        return jsonify({
        'ok': True,
        'message': f'Group "{group_name}" updated successfully'
        })

        # DUPLICATE REMOVED: @scene_groups_bp.route('/api/scene-groups/policies/<policy_name>/groups/preferred/<group_name>', methods=['GET'])
        # DUPLICATE REMOVED: def delete_preferred_group(policy_name, group_name):
        """Remove a group from the preferred list"""
        data = _load_scene_groups()
        policy = data.get('policies', {}).get(policy_name)

        if not policy:
        return jsonify({'ok': False, 'error': 'Policy not found'}), 404

        # Remove the group
        preferred_groups = policy.get('preferred_groups', [])
        original_count = len(preferred_groups)
        preferred_groups = [g for g in preferred_groups if g['name'].upper() != group_name.upper()]

        if len(preferred_groups) == original_count:
        return jsonify({'ok': False, 'error': 'Group not found in preferred list'}), 404

        policy['preferred_groups'] = preferred_groups
        _save_scene_groups(data)

        return jsonify({
        'ok': True,
        'message': f'Group "{group_name}" removed from preferred list'
        })


        @scene_groups_bp.route('/api/scene-groups/policies/<policy_name>/groups/blocked', methods=['GET'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def get_blocked_groups(policy_name):
    try:
        """Get all blocked groups for a policy"""
        data = _load_scene_groups()
        policy = data.get('policies', {}).get(policy_name)

        if not policy:
        return jsonify({'ok': False, 'error': 'Policy not found'}), 404

        return jsonify({
        'ok': True,
        'policy_name': policy_name,
        'blocked_groups': policy.get('blocked_groups', [])
        })

        # DUPLICATE REMOVED: @scene_groups_bp.route('/api/scene-groups/policies/<policy_name>/groups/blocked', methods=['POST'])
        # DUPLICATE REMOVED: def add_blocked_group(policy_name):
        """
        Add a new blocked group to a policy
        Body: {
        "name": "GroupName",
        "reason": "Why this group is blocked"
        }
        """
        req_data = request.get_json(silent=True) or {}
        group_name = req_data.get('name')

        if not group_name:
        return jsonify({'ok': False, 'error': 'Group name required'}), 400

        data = _load_scene_groups()
        policy = data.get('policies', {}).get(policy_name)

        if not policy:
        return jsonify({'ok': False, 'error': 'Policy not found'}), 404

        # Check if group already exists
        blocked_groups = policy.get('blocked_groups', [])
        for group in blocked_groups:
        if group['name'].upper() == group_name.upper():
        return jsonify({'ok': False, 'error': 'Group already exists in blocked list'}), 400

        # Add new group
        new_group = {
        'name': group_name,
        'reason': req_data.get('reason', 'No reason specified')
        }

        blocked_groups.append(new_group)
        policy['blocked_groups'] = blocked_groups
        _save_scene_groups(data)

        return jsonify({
        'ok': True,
        'message': f'Group "{group_name}" added to blocked list',
        'group': new_group
        })


        @scene_groups_bp.route('/api/scene-groups/policies/<policy_name>/groups/blocked/<group_name>', methods=['DELETE'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def delete_blocked_group(policy_name, group_name):
    try:
        """Remove a group from the blocked list"""
        data = _load_scene_groups()
        policy = data.get('policies', {}).get(policy_name)

        if not policy:
        return jsonify({'ok': False, 'error': 'Policy not found'}), 404

        # Remove the group
        blocked_groups = policy.get('blocked_groups', [])
        original_count = len(blocked_groups)
        blocked_groups = [g for g in blocked_groups if g['name'].upper() != group_name.upper()]

        if len(blocked_groups) == original_count:
        return jsonify({'ok': False, 'error': 'Group not found in blocked list'}), 404

        policy['blocked_groups'] = blocked_groups
        _save_scene_groups(data)

        return jsonify({
        'ok': True,
        'message': f'Group "{group_name}" removed from blocked list'
        })

        # ============================================================================
        # Release Checking Endpoints
        # ============================================================================

        @scene_groups_bp.route('/api/scene-groups/check', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def check_release():
    try:
        """
        Check if a release is allowed by the scene group policy
        Body: {
        "release": "Movie.Name.2024.1080p.BluRay.x264-GroupName",
        "policy": "UserDefined" (optional, uses default if not specified)
        }
        """
        req_data = request.get_json(silent=True) or {}
        release_name = req_data.get('release')
        policy_name = req_data.get('policy')

        if not release_name:
        return jsonify({'ok': False, 'error': 'release name required'}), 400

        data = _load_scene_groups()

        # Use specified policy or default
        if not policy_name:
        policy_name = data.get('default_policy', 'UserDefined')

        policy = data.get('policies', {}).get(policy_name)
        if not policy:
        return jsonify({'ok': False, 'error': f'Policy "{policy_name}" not found'}), 404

        result = _apply_scene_group_policy(release_name, policy)

        return jsonify({
        'ok': True,
        'policy_used': policy_name,
        'release': release_name,
        'result': result
        })


        @scene_groups_bp.route('/api/scene-groups/check-upgrade', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def check_upgrade():
    """
    Check if a new release is eligible for upgrade
    Body: {
        "current_release": "Movie.Name.2024.1080p.BluRay.x264-GroupA",
        "new_release": "Movie.Name.2024.1080p.BluRay.x264-GroupB",
        "policy": "UserDefined" (optional)
    }
    """
    req_data = request.get_json(silent=True) or {}
    current_release = req_data.get('current_release')
    new_release = req_data.get('new_release')
    policy_name = req_data.get('policy')
    
    if not current_release or not new_release:
        return jsonify({'ok': False, 'error': 'current_release and new_release required'}), 400
    
    data = _load_scene_groups()
    
    # Use specified policy or default
    if not policy_name:
        policy_name = data.get('default_policy', 'UserDefined')
    
    policy = data.get('policies', {}).get(policy_name)
    if not policy:
        return jsonify({'ok': False, 'error': f'Policy "{policy_name}" not found'}), 404
    
    # Check both releases against policy
    current_result = _apply_scene_group_policy(current_release, policy)
    new_result = _apply_scene_group_policy(new_release, policy)
    
    # Check if new release is blocked
    if not new_result['allowed']:
        return jsonify({
            'ok': True,
            'policy_used': policy_name,
            'upgrade_eligible': False,
            'reason': 'New release is blocked by policy',
            'current_release': current_result,
            'new_release': new_result
        })
    
    # Check if current release is protected (never_remove)
    if current_result.get('never_remove', False):
        return jsonify({
            'ok': True,
            'policy_used': policy_name,
            'upgrade_eligible': False,
            'reason': 'Current release is protected (never_remove)',
            'current_release': current_result,
            'new_release': new_result
        })
    
    # Check upgrade eligibility based on scoring
    upgrade_check = _check_upgrade_eligibility(current_release, new_release, data)
    
    return jsonify({
        'ok': True,
        'policy_used': policy_name,
        'upgrade_eligible': upgrade_check['eligible'],
        'reason': upgrade_check['reason'],
        'score_improvement': upgrade_check.get('score_improvement', 0),
        'current_release': current_result,
        'new_release': new_result,
        'scoring_details': {
            'current_score': upgrade_check.get('current_score', 0),
            def create_scene_groups_upgrade_rules():
                """Create Upgrade Rules"""
                try:
                    data = request.get_json()
                    if not data:
                    return jsonify({'error': 'No data provided'}), 400
                    return jsonify({'success': True, 'message': 'Created', 'data': data}), 201
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
            'new_score': upgrade_check.get('new_score', 0)
        }
    })

# ============================================================================
# Upgrade Rules Endpoints
# ============================================================================

@scene_groups_bp.route('/api/scene-groups/upgrade-rules', methods=['POST'])
def create_scene_groups_upgrade_rules():
    """Create Upgrade Rules"""
    try:
        data = request.get_json()
        if not data:
        return jsonify({'error': 'No data provided'}), 400
        return jsonify({'success': True, 'message': 'Created', 'data': data}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
def get_upgrade_rules():
    """Get upgrade rules configuration"""
    data = _load_scene_groups()
        return jsonify({
        'ok': True,
        'upgrade_rules': data.get('upgrade_rules', {})
    })

# DUPLICATE REMOVED: @scene_groups_bp.route('/api/scene-groups/upgrade-rules', methods=['POST'])
# DUPLICATE REMOVED: def set_upgrade_rules():
    """
    Update upgrade rules configuration
    Body: {
        "check_interval_hours": 24,
        "min_score_improvement": 20,
        "preserve_watched_status": true,
        "auto_delete_old_version": false
    }
    """
    req_data = request.get_json(silent=True) or {}
    
    data = _load_scene_groups()
    current_rules = data.get('upgrade_rules', {})
    current_rules.update(req_data)
    data['upgrade_rules'] = current_rules
    _save_scene_groups(data)
    
    return jsonify({
        'ok': True,
        'message': 'Upgrade rules updated successfully',
        'upgrade_rules': current_rules
    })
