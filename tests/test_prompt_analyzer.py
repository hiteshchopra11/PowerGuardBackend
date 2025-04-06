import pytest
from app.prompt_analyzer import (
    classify_user_prompt,
    is_prompt_relevant,
    ALLOWED_ACTIONABLE_TYPES
)

def test_classify_user_prompt():
    # Test battery optimization prompts
    battery_prompt = "Please optimize my battery life"
    battery_result = classify_user_prompt(battery_prompt)
    assert battery_result["is_relevant"] == True
    assert battery_result["optimize_battery"] == True
    assert not battery_result["optimize_data"]
    assert "OPTIMIZE_BATTERY" in battery_result["actionable_focus"]
    
    # Test data optimization prompts
    data_prompt = "Reduce my network data usage"
    data_result = classify_user_prompt(data_prompt)
    assert data_result["is_relevant"] == True
    assert data_result["optimize_data"] == True
    assert not data_result["optimize_battery"]
    assert "ENABLE_DATA_SAVER" in data_result["actionable_focus"]
    
    # Test combined optimization prompt
    combined_prompt = "Save both battery and data"
    combined_result = classify_user_prompt(combined_prompt)
    assert combined_result["is_relevant"] == True
    assert combined_result["optimize_battery"] == True
    assert combined_result["optimize_data"] == True
    
    # Test specific action prompt
    kill_prompt = "Kill battery-draining apps"
    kill_result = classify_user_prompt(kill_prompt)
    assert kill_result["is_relevant"] == True
    assert "KILL_APP" in kill_result["actionable_focus"]
    
    # Test irrelevant prompt
    irrelevant_prompt = "What's the weather like today?"
    irrelevant_result = classify_user_prompt(irrelevant_prompt)
    assert irrelevant_result["is_relevant"] == False
    
    # Test empty prompt
    empty_result = classify_user_prompt("")
    assert empty_result["is_relevant"] == False
    
    # Test None prompt
    none_result = classify_user_prompt(None)
    assert none_result["is_relevant"] == False

def test_is_prompt_relevant():
    assert is_prompt_relevant("Optimize my battery") == True
    assert is_prompt_relevant("Save my network data") == True
    assert is_prompt_relevant("What's the weather today?") == False
    assert is_prompt_relevant("") == False
    assert is_prompt_relevant(None) == False

def test_negation_handling():
    # Test negation for battery
    negation_prompt = "Check my data usage but ignore the battery"
    negation_result = classify_user_prompt(negation_prompt)
    assert negation_result["is_relevant"] == True
    assert negation_result["optimize_data"] == True
    assert negation_result["optimize_battery"] == False
    
    # Test negation for data
    negation_prompt = "Optimize battery but not data usage"
    negation_result = classify_user_prompt(negation_prompt)
    assert negation_result["is_relevant"] == True
    assert negation_result["optimize_battery"] == True
    assert negation_result["optimize_data"] == False 