"""SDK-aligned action normalization wiring."""

from __future__ import annotations

from typing import Any, Dict

from gtaf_sdk.actions import normalize_action


# Deterministic tool-name -> action-prefix mapping used by SDK normalize_action.
TOOL_ACTION_MAPPING: Dict[str, str] = {
    "execute_command": "execute_command",
    "email_operations": "email_operations",
    "contact_operations": "contact_operations",
    "weather_operations": "weather_operations",
    "generic_web_scraping": "generic_web_scraping",
    "crypto_data_operations": "crypto_data_operations",
    "spotify_operations": "spotify_operations",
}


def build_action_id(function_name: str, arguments: Dict[str, Any]) -> str:
    """Build canonical action IDs via gtaf_sdk.actions.normalize_action()."""
    return normalize_action(
        tool_name=function_name,
        arguments=arguments,
        mapping=TOOL_ACTION_MAPPING,
        on_unknown="return_unknown",
    )
