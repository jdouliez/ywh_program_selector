"""
YWH Program Selector - CLI tool for managing YesWeHack private programs.

This package helps bug hunters analyze and prioritize their YesWeHack programs,
find collaboration opportunities, and extract scope information.
"""

__version__ = "0.2.0"
__author__ = "@_Ali4s_"

# Main entry point
from ywh_program_selector.ywh_program_selector import main

# Convenience exports for programmatic use
from ywh_program_selector.api import get_data_from_ywh
from ywh_program_selector.auth import get_credentials, get_token_from_credential
from ywh_program_selector.collaboration import analyze_common_ids, display_collaborations
from ywh_program_selector.display import banner, green, orange, red
from ywh_program_selector.programs import (
    extract_programs_info,
    extract_programs_list,
    extract_programs_scopes,
    find_program_by_scope,
)

__all__ = [
    "__version__",
    "__author__",
    "main",
    # API
    "get_data_from_ywh",
    # Auth
    "get_credentials",
    "get_token_from_credential",
    # Collaboration
    "analyze_common_ids",
    "display_collaborations",
    # Display
    "banner",
    "green",
    "orange",
    "red",
    # Programs
    "extract_programs_info",
    "extract_programs_list",
    "extract_programs_scopes",
    "find_program_by_scope",
]
