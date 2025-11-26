"""
Feature Flags Service - Phase 10
Manages feature flags for gradual rollout
"""

import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.database import SessionLocal

logger = logging.getLogger(__name__)


class FeatureFlags:
    """Feature flags service"""
    
    # Default flags - Blueprint system only (legacy flags removed)
    DEFAULT_FLAGS = {
        "enable_blueprints": True,
        "enable_blueprint_publish": True,
        "enable_sandbox": True,
        "enable_blueprint_compiler": True,
        "enable_detection_engine": True,
        "enable_llm_evaluation": True,
        "enable_scoring_engine": True,
        "enable_semantic_matching": True,
        "enable_hybrid_detection": True,
    }
    
    def __init__(self):
        self.flags = self.DEFAULT_FLAGS.copy()
        # In production, would load from database or config service
    
    def is_enabled(self, flag_name: str, company_id: Optional[str] = None) -> bool:
        """
        Check if a feature flag is enabled
        
        Args:
            flag_name: Name of the feature flag
            company_id: Optional company ID for company-specific flags
        
        Returns:
            True if enabled, False otherwise
        """
        # Check company-specific override if provided
        if company_id:
            company_flag = f"{flag_name}_{company_id}"
            if company_flag in self.flags:
                return self.flags[company_flag]
        
        # Check global flag
        return self.flags.get(flag_name, False)
    
    def set_flag(self, flag_name: str, enabled: bool, company_id: Optional[str] = None):
        """
        Set a feature flag
        
        Args:
            flag_name: Name of the feature flag
            enabled: Whether to enable
            company_id: Optional company ID for company-specific flags
        """
        if company_id:
            self.flags[f"{flag_name}_{company_id}"] = enabled
        else:
            self.flags[flag_name] = enabled
    
    def get_all_flags(self, company_id: Optional[str] = None) -> Dict[str, bool]:
        """Get all feature flags"""
        result = {}
        for flag_name in self.DEFAULT_FLAGS.keys():
            result[flag_name] = self.is_enabled(flag_name, company_id)
        return result


# Singleton instance
feature_flags = FeatureFlags()

