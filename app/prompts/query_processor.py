"""
Query processing module for PowerGuard AI - handles 2-step query analysis.
"""

import json
import logging
from typing import Dict, Any, Optional, Tuple
from groq import Groq

from .system_prompts import (
    get_resource_type_prompt,
    get_categorization_prompt,
    get_main_analysis_prompt,
    extract_number_from_query
)

logger = logging.getLogger('powerguard_query_processor')

class QueryProcessor:
    """Handles the 2-step query processing flow from Android app."""
    
    def __init__(self, groq_client: Groq):
        self.groq_client = groq_client
        
    def process_query(
        self, 
        user_query: str, 
        device_data: Dict[str, Any],
        past_usage_patterns: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process user query using 2-step analysis flow.
        
        Args:
            user_query: User's query string
            device_data: Device data dictionary  
            past_usage_patterns: Optional past usage patterns text
            
        Returns:
            Processed analysis result
        """
        try:
            # Step 1: Detect resource type
            resource_type = self._detect_resource_type(user_query)
            logger.debug(f"[PowerGuard] Detected resource type: {resource_type}")
            
            # Step 2: Categorize query
            category = self._categorize_query(user_query, resource_type)
            logger.debug(f"[PowerGuard] Detected category: {category}")
            
            # Extract number if specified in query
            number = extract_number_from_query(user_query)
            
            # Step 3: Generate analysis using category-specific template
            analysis_result = self._generate_analysis(
                user_query=user_query,
                device_data=device_data,
                resource_type=resource_type,
                category=category,
                number=number,
                past_usage_patterns=past_usage_patterns
            )
            
            # Add metadata to result
            analysis_result.update({
                "resourceType": resource_type,
                "queryCategory": category,
                "processing_metadata": {
                    "resource_type": resource_type,
                    "category": category,
                    "number_requested": number
                }
            })
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"[PowerGuard] Error in query processing: {str(e)}", exc_info=True)
            return self._generate_error_response(str(e))
    
    def _detect_resource_type(self, user_query: str) -> str:
        """Step 1: Detect if query is about BATTERY, DATA, or OTHER."""
        try:
            prompt = get_resource_type_prompt(user_query)
            
            completion = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a query classifier. Respond with only BATTERY, DATA, or OTHER."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=10
            )
            
            resource_type = completion.choices[0].message.content.strip().upper()
            
            # Validate response
            if resource_type not in ["BATTERY", "DATA", "OTHER"]:
                logger.warning(f"[PowerGuard] Invalid resource type: {resource_type}, defaulting to OTHER")
                return "OTHER"
                
            return resource_type
            
        except Exception as e:
            logger.error(f"[PowerGuard] Error detecting resource type: {str(e)}")
            return "OTHER"
    
    def _categorize_query(self, user_query: str, resource_type: str) -> int:
        """Step 2: Categorize query into one of 6 categories."""
        try:
            prompt = get_categorization_prompt(user_query, resource_type)
            
            completion = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant", 
                messages=[
                    {"role": "system", "content": "You are a query categorizer. Respond with only a number 1-6."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=5
            )
            
            category_str = completion.choices[0].message.content.strip()
            
            try:
                category = int(category_str)
                if 1 <= category <= 6:
                    return category
                else:
                    logger.warning(f"[PowerGuard] Category out of range: {category}, defaulting to 6")
                    return 6
            except ValueError:
                logger.warning(f"[PowerGuard] Invalid category format: {category_str}, defaulting to 6")
                return 6
                
        except Exception as e:
            logger.error(f"[PowerGuard] Error categorizing query: {str(e)}")
            return 6  # Invalid query
    
    def _generate_analysis(
        self,
        user_query: str,
        device_data: Dict[str, Any],
        resource_type: str,
        category: int,
        number: Optional[int] = None,
        past_usage_patterns: Optional[str] = None
    ) -> Dict[str, Any]:
        """Step 3: Generate analysis using category-specific template."""
        try:
            # Generate the main analysis prompt
            analysis_prompt = get_main_analysis_prompt(
                user_query=user_query,
                device_data=device_data,
                category=category,
                resource_type=resource_type,
                number=number,
                past_usage_patterns=past_usage_patterns
            )
            
            logger.debug(f"[PowerGuard] Generated analysis prompt for category {category}")
            
            # Get analysis from LLM
            completion = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a device optimization AI. Return only valid JSON."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.2,
                max_tokens=2048,
                response_format={"type": "json_object"}
            )
            
            response_text = completion.choices[0].message.content.strip()
            
            try:
                analysis_result = json.loads(response_text)
                
                # Validate required fields
                required_fields = ["batteryScore", "dataScore", "performanceScore", "insights", "actionable"]
                for field in required_fields:
                    if field not in analysis_result:
                        analysis_result[field] = self._get_default_value(field)
                
                # Ensure scores are numeric
                for score_field in ["batteryScore", "dataScore", "performanceScore"]:
                    try:
                        analysis_result[score_field] = float(analysis_result[score_field])
                    except (ValueError, TypeError):
                        analysis_result[score_field] = 50.0
                
                # Ensure insights and actionable are lists
                if not isinstance(analysis_result["insights"], list):
                    analysis_result["insights"] = []
                if not isinstance(analysis_result["actionable"], list):
                    analysis_result["actionable"] = []
                
                return analysis_result
                
            except json.JSONDecodeError as e:
                logger.error(f"[PowerGuard] JSON decode error: {str(e)}")
                logger.error(f"[PowerGuard] Response text: {response_text}")
                return self._generate_fallback_response(user_query, resource_type, category)
                
        except Exception as e:
            logger.error(f"[PowerGuard] Error generating analysis: {str(e)}", exc_info=True)
            return self._generate_fallback_response(user_query, resource_type, category)
    
    def _get_default_value(self, field: str) -> Any:
        """Get default value for missing fields."""
        defaults = {
            "batteryScore": 50.0,
            "dataScore": 50.0,
            "performanceScore": 50.0,
            "insights": [],
            "actionable": []
        }
        return defaults.get(field, None)
    
    def _generate_fallback_response(self, user_query: str, resource_type: str, category: int) -> Dict[str, Any]:
        """Generate fallback response when LLM analysis fails."""
        return {
            "batteryScore": 50.0,
            "dataScore": 50.0,
            "performanceScore": 50.0,
            "insights": [{
                "type": resource_type,
                "title": "Analysis Error",
                "description": f"Unable to fully analyze your {resource_type.lower()} query. Please try rephrasing your request.",
                "severity": "MEDIUM"
            }],
            "actionable": [],
            "resourceType": resource_type,
            "queryCategory": category
        }
    
    def _generate_error_response(self, error_message: str) -> Dict[str, Any]:
        """Generate error response."""
        return {
            "batteryScore": 50.0,
            "dataScore": 50.0,
            "performanceScore": 50.0,
            "insights": [{
                "type": "ERROR",
                "title": "Processing Error",
                "description": f"An error occurred while processing your query: {error_message}",
                "severity": "HIGH"
            }],
            "actionable": [],
            "resourceType": "OTHER",
            "queryCategory": 6
        }

# Utility functions for backward compatibility
def process_user_query(
    user_query: str,
    device_data: Dict[str, Any], 
    groq_client: Groq,
    past_usage_patterns: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to process a user query.
    
    Args:
        user_query: User's query string
        device_data: Device data dictionary
        groq_client: Groq client instance
        past_usage_patterns: Optional past usage patterns
        
    Returns:
        Analysis result dictionary
    """
    processor = QueryProcessor(groq_client)
    return processor.process_query(user_query, device_data, past_usage_patterns)