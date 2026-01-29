"""
Utility module - re-exports for backward compatibility.

This module re-exports functions from the new modular structure
to maintain backward compatibility with existing imports.
"""

import json
import os
from typing import Dict, List

# Re-export display utilities
from ywh_program_selector.display import (
    banner,
    format_number,
    green,
    orange,
    red,
)

# Re-export scoring utilities
from ywh_program_selector.scoring import (
    get_date_from,
    score_and_colorize,
    score_date,
)

# Re-export parsing utilities
from ywh_program_selector.parsing import (
    get_ips_from_subnet,
    get_name,
    is_ip,
    is_valid_domain,
)

# Re-export API utilities
from ywh_program_selector.api import (
    fetch_all,
    fetch_all_v1,
    fetch_all_v2,
    get_data_from_ywh,
)

# Re-export collaboration utilities
from ywh_program_selector.collaboration import (
    analyze_common_ids,
    build_pid_to_name_map,
    convert_ids_to_slug,
    display_collaborations,
)

# Re-export program utilities
from ywh_program_selector.programs import (
    extract_programs_info,
    extract_programs_list,
    extract_programs_scopes,
    find_program_by_scope,
)


# =============================================================================
# Additional utilities that don't fit in other modules
# =============================================================================

def get_expanded_path(path: str) -> str:
    """Expand ~ to full home directory path."""
    if path.startswith('~'):
        return os.path.expanduser(path)
    return path


def load_json_files(file_paths: List[str]) -> Dict:
    """Load and merge all JSON files into a single dictionary."""
    all_data = {}
    for file_path in file_paths:
        with open(file_path, 'r') as f:
            data = json.load(f)
            all_data.update(data)
    return all_data


# Export all public symbols
__all__ = [
    # Display
    'banner',
    'format_number',
    'green',
    'orange', 
    'red',
    # Scoring
    'get_date_from',
    'score_and_colorize',
    'score_date',
    # Parsing
    'get_ips_from_subnet',
    'get_name',
    'is_ip',
    'is_valid_domain',
    # API
    'fetch_all',
    'fetch_all_v1',
    'fetch_all_v2',
    'get_data_from_ywh',
    # Collaboration
    'analyze_common_ids',
    'build_pid_to_name_map',
    'convert_ids_to_slug',
    'display_collaborations',
    # Programs
    'extract_programs_info',
    'extract_programs_list',
    'extract_programs_scopes',
    'find_program_by_scope',
    # Local utilities
    'get_expanded_path',
    'load_json_files',
]
