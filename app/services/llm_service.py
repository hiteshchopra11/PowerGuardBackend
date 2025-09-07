"""LLM integration service."""

import os
import logging
from typing import Dict, Any, Optional, List
from groq import Groq
from dotenv import load_dotenv

from app.prompts.query_processor import QueryProcessor
from app.core.exceptions import AnalysisException, RateLimitException

logger = logging.getLogger('powerguard_llm_service')
load_dotenv()


class LLMService:
    """Service for LLM integration and query processing."""
    
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
        
        self.groq_client = Groq(api_key=api_key)
        self.query_processor = QueryProcessor(self.groq_client)
    
    def analyze_with_prompt(
        self, 
        user_query: str, 
        device_data: Dict[str, Any],
        past_usage_patterns: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze device data using natural language prompt."""
        try:
            logger.info(f"[LLMService] Processing query: '{user_query}'")
            
            analysis_result = self.query_processor.process_query(
                user_query=user_query,
                device_data=device_data,
                past_usage_patterns=past_usage_patterns
            )
            
            # Transform result for backend compatibility
            return self._transform_analysis_result(analysis_result, device_data)
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[LLMService] Analysis error: {error_msg}", exc_info=True)
            
            if "429" in error_msg or "rate limit" in error_msg.lower():
                raise RateLimitException("Rate limit exceeded. Please try again later.")
            
            raise AnalysisException(f"LLM analysis failed: {error_msg}")
    
    def _transform_analysis_result(self, analysis_result: Dict[str, Any], device_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform new prompt system result to legacy format."""
        from datetime import datetime
        
        # Transform actionables
        legacy_actionables = []
        for actionable in analysis_result.get("actionable", []):
            legacy_actionable = {
                "id": f"action_{int(datetime.now().timestamp())}_{len(legacy_actionables)}",
                "type": actionable.get("type", "").upper(),
                "description": actionable.get("description", ""),
                "parameters": actionable.get("parameters", {}),
                "reason": f"Based on {analysis_result.get('resourceType', 'resource')} analysis"
            }
            
            # Add package name and mode from parameters
            params = actionable.get("parameters", {})
            if "packageName" in params:
                legacy_actionable["packageName"] = params["packageName"]
            if "newMode" in params:
                legacy_actionable["newMode"] = params["newMode"]
            
            legacy_actionables.append(legacy_actionable)
        
        # Transform insights
        legacy_insights = []
        for insight in analysis_result.get("insights", []):
            legacy_insights.append({
                "type": insight.get("type", "General"),
                "title": insight.get("title", ""),
                "description": insight.get("description", ""),
                "severity": insight.get("severity", "MEDIUM").lower()
            })
        
        # Calculate savings
        estimated_savings = self._calculate_estimated_savings(
            analysis_result.get("resourceType", "OTHER"),
            legacy_actionables
        )
        
        # Determine response type
        category = analysis_result.get("queryCategory", 6)
        if category in [1, 2]:
            response_type = "information"
        elif category == 6:
            response_type = "error"
        else:
            response_type = "optimization"
        
        return {
            "id": f"gen_{int(datetime.now().timestamp())}",
            "success": True,
            "timestamp": int(datetime.now().timestamp()),
            "message": "Analysis completed successfully",
            "responseType": response_type,
            "actionable": legacy_actionables,
            "insights": legacy_insights,
            "batteryScore": analysis_result.get("batteryScore", 50.0),
            "dataScore": analysis_result.get("dataScore", 50.0),
            "performanceScore": analysis_result.get("performanceScore", 50.0),
            "estimatedSavings": estimated_savings,
            "processing_metadata": analysis_result.get("processing_metadata", {})
        }
    
    def _calculate_estimated_savings(self, resource_type: str, actionables: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate estimated savings based on resource type and actionables."""
        savings = {"batteryMinutes": 0.0, "dataMB": 0.0}
        
        battery_savings_per_action = {
            "SET_STANDBY_BUCKET": 15.0,
            "KILL_APP": 25.0,
            "MANAGE_WAKE_LOCKS": 20.0,
            "THROTTLE_CPU_USAGE": 10.0
        }
        
        data_savings_per_action = {
            "RESTRICT_BACKGROUND_DATA": 30.0,
            "SET_STANDBY_BUCKET": 10.0,
            "KILL_APP": 15.0
        }
        
        for actionable in actionables:
            action_type = actionable.get("type", "")
            
            if resource_type in ["BATTERY", "OTHER"]:
                if action_type in battery_savings_per_action:
                    savings["batteryMinutes"] += battery_savings_per_action[action_type]
            
            if resource_type in ["DATA", "OTHER"]:
                if action_type in data_savings_per_action:
                    savings["dataMB"] += data_savings_per_action[action_type]
        
        # Apply focus multipliers
        if resource_type == "BATTERY":
            savings["batteryMinutes"] *= 1.5
        elif resource_type == "DATA":
            savings["dataMB"] *= 1.5
        
        return savings