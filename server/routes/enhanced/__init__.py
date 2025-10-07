"""
Enhanced Routes Module
Provides all enhanced functionality for MediaHub Complete
"""

# Import all enhanced route modules
from . import downloader_enhanced
from . import text_editor_enhanced
from . import real_debrid_enhanced
from . import smart_collections
from . import rss_automation
from . import casting_enhanced
from . import testing_diagnostics

# Create aliases for backward compatibility
rd_manager_enhanced = real_debrid_enhanced
metadata_enhanced = smart_collections
rss_enhanced = rss_automation
diagnostics_enhanced = testing_diagnostics
profiles_enhanced = None  # Will be created separately

__all__ = [
    'downloader_enhanced',
    'text_editor_enhanced', 
    'real_debrid_enhanced',
    'smart_collections',
    'rss_automation',
    'casting_enhanced',
    'testing_diagnostics',
    'rd_manager_enhanced',
    'metadata_enhanced',
    'rss_enhanced',
    'diagnostics_enhanced'
]
