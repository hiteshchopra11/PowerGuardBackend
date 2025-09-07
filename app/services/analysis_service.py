"""Main analysis service orchestrating device data analysis."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.llm_service import LLMService
from app.services.pattern_service import PatternService
from app.services.scoring_service import ScoringService
from app.utils.strategy_analyzer import determine_strategy, calculate_savings
from app.utils.actionable_generator import generate_actionables, is_information_request
from app.utils.insight_generator import generate_insights
from app.core.exceptions import AnalysisException, ValidationException

logger = logging.getLogger('powerguard_analysis_service')


class AnalysisService:
    """Main service for analyzing device data and generating recommendations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.llm_service = LLMService()
        self.pattern_service = PatternService(db)
        self.scoring_service = ScoringService()
    
    def analyze_device_data(self, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze device data and return optimization recommendations."""
        try:
            device_id = device_data.get('deviceId', 'unknown')
            logger.info(f"[AnalysisService] Analyzing device data for: {device_id}")
            
            # Validate device data
            self._validate_device_data(device_data)
            
            # Extract prompt
            prompt = device_data.get("prompt", "").strip() if device_data.get("prompt") else ""
            
            # Route to appropriate analysis method
            if prompt:
                return self._analyze_with_prompt(device_data, prompt)
            else:
                return self._analyze_without_prompt(device_data)
            
        except Exception as e:
            logger.error(f"[AnalysisService] Analysis failed: {str(e)}", exc_info=True)
            return self._create_error_response(str(e))
    
    def _analyze_with_prompt(self, device_data: Dict[str, Any], prompt: str) -> Dict[str, Any]:
        """Analyze using LLM with natural language prompt."""
        try:
            # Get historical patterns
            device_id = device_data.get('deviceId', '')
            historical_patterns = ""
            if device_id:
                patterns_dict = self.pattern_service.get_patterns_for_device(device_id)
                historical_patterns = self._format_historical_patterns(patterns_dict)
            
            # Use LLM service for analysis
            analysis_result = self.llm_service.analyze_with_prompt(
                user_query=prompt,
                device_data=device_data,
                past_usage_patterns=historical_patterns
            )
            
            # Store patterns if it's an optimization request
            resource_type = analysis_result.get('processing_metadata', {}).get('resource_type', 'OTHER')
            category = analysis_result.get('processing_metadata', {}).get('category', 6)
            
            if category in [3, 5] and resource_type != 'OTHER':
                try:
                    strategy = {"critical_apps": []}  # Simplified for new system
                    self.pattern_service.store_device_patterns(device_data, strategy)
                except Exception as e:
                    logger.error(f"[AnalysisService] Failed to store patterns: {str(e)}")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"[AnalysisService] Prompt analysis failed: {str(e)}")
            # Fallback to legacy analysis
            return self._analyze_without_prompt(device_data)
    
    def _analyze_without_prompt(self, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze using legacy rule-based system."""
        try:
            logger.info("[AnalysisService] Using legacy analysis system")
            
            # Determine strategy
            strategy = determine_strategy(device_data, "")
            
            # Check if information request
            info_request = False
            
            # Generate insights and actionables
            insights = generate_insights(strategy, device_data, info_request, "")
            
            # Generate actionables only for optimization requests
            actionables = []
            if not info_request:
                actionables = generate_actionables(strategy, device_data)
            
            # Calculate scores
            battery_score = self.scoring_service.calculate_battery_score(device_data)
            data_score = self.scoring_service.calculate_data_score(device_data)
            performance_score = self.scoring_service.calculate_performance_score(device_data)
            
            # Calculate savings
            savings = calculate_savings(strategy, strategy.get("critical_apps", []))
            
            # Store usage patterns
            if not info_request:
                try:
                    self.pattern_service.store_device_patterns(device_data, strategy)
                except Exception as e:
                    logger.error(f"[AnalysisService] Failed to store patterns: {str(e)}")
            
            return {
                "id": f"gen_{int(datetime.now().timestamp())}",
                "success": True,
                "timestamp": int(datetime.now().timestamp()),
                "message": "Analysis completed successfully",
                "responseType": "information" if info_request else "optimization",
                "actionable": actionables,
                "insights": insights,
                "batteryScore": battery_score,
                "dataScore": data_score,
                "performanceScore": performance_score,
                "estimatedSavings": savings
            }
            
        except Exception as e:
            logger.error(f"[AnalysisService] Legacy analysis failed: {str(e)}")
            raise AnalysisException(f"Analysis failed: {str(e)}")
    
    def _validate_device_data(self, device_data: Dict[str, Any]) -> None:
        """Validate device data structure."""
        if not isinstance(device_data, dict):
            raise ValidationException("Device data must be a dictionary")
        
        if not device_data.get("deviceId"):
            raise ValidationException("Device ID is required")
        
        if "battery" not in device_data:
            raise ValidationException("Battery information is required")
        
        if "apps" not in device_data:
            raise ValidationException("Apps information is required")
    
    def _format_historical_patterns(self, patterns_dict: Dict[str, str]) -> str:
        """Format historical patterns for LLM context."""
        if not patterns_dict:
            return "No historical usage patterns available."
        
        pattern_lines = []
        for package_name, pattern in patterns_dict.items():
            pattern_lines.append(f"- {package_name}: {pattern}")
        
        return "\n".join(pattern_lines)
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error response."""
        # Determine error type
        if "rate limit" in error_message.lower() or "429" in error_message:
            friendly_message = "Service is currently experiencing high demand. Please try again in a few moments."
            error_type = "RateLimit"
        elif "timeout" in error_message.lower():
            friendly_message = "Analysis took too long to complete. Please try again with simplified data."
            error_type = "Timeout"
        elif "validation" in error_message.lower():
            friendly_message = f"Invalid device data: {error_message}"
            error_type = "Validation"
        else:
            friendly_message = f"An error occurred while analyzing your device data: {error_message}"
            error_type = "General"
        
        return {
            "id": f"error_{int(datetime.now().timestamp())}",
            "success": False,
            "timestamp": int(datetime.now().timestamp()),
            "message": "Analysis failed",
            "responseType": "error",
            "actionable": [],
            "insights": [{
                "type": error_type,
                "title": "Error Analyzing Device Data",
                "description": friendly_message,
                "severity": "high"
            }],
            "batteryScore": 50.0,
            "dataScore": 50.0,
            "performanceScore": 50.0,
            "estimatedSavings": {
                "batteryMinutes": 0,
                "dataMB": 0
            }
        }