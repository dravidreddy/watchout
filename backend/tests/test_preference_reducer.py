"""
Tests for PreferenceReducer - Smart Preference Conflict Resolution
"""
import pytest
from app.services.preference_reducer import PreferenceReducer, preference_reducer


class TestIntentDetection:
    """Test intent detection from user messages"""
    
    def test_detect_replacement_intent_english(self):
        """Test replacement keywords in English"""
        reducer = PreferenceReducer()
        
        assert reducer.detect_intent("Actually, I want Goa") == 'replace'
        assert reducer.detect_intent("Instead of Delhi, let's go to Mumbai") == 'replace'
        assert reducer.detect_intent("No wait, change that to 7 days") == 'replace'
        assert reducer.detect_intent("I meant to say Bangalore") == 'replace'
        assert reducer.detect_intent("Scratch that, make it 5 days") == 'replace'
    
    def test_detect_replacement_intent_hindi(self):
        """Test replacement keywords in Hindi"""
        reducer = PreferenceReducer()
        
        assert reducer.detect_intent("नहीं, मुंबई") == 'replace'
        assert reducer.detect_intent("balki Goa") == 'replace'
    
    def test_detect_addition_intent(self):
        """Test addition keywords"""
        reducer = PreferenceReducer()
        
        assert reducer.detect_intent("Also add Mumbai") == 'add'
        assert reducer.detect_intent("And Goa too") == 'add'
        assert reducer.detect_intent("Delhi and Mumbai") == 'add'
        assert reducer.detect_intent("Plus Bangalore") == 'add'
        assert reducer.detect_intent("aur Mumbai bhi") == 'add'
    
    def test_detect_intent_heuristics(self):
        """Test intent detection without explicit keywords"""
        reducer = PreferenceReducer()
        
        # Multiple items with 'and' → add
        assert reducer.detect_intent("I want to visit Delhi, Mumbai, and Goa") == 'add'
        
        # Single item without keywords → replace (safer default)
        assert reducer.detect_intent("I want to visit Goa") == 'replace'


class TestPreferenceUpdates:
    """Test preference update logic"""
    
    def test_update_destinations_replace(self):
        """Test replacing destinations"""
        reducer = PreferenceReducer()
        current = {"destinations": ["Delhi"]}
        new = {"destinations": ["Goa"]}
        
        updated, summary = reducer.update_preferences(
            current, new, "Actually, I want to visit Goa instead"
        )
        
        assert updated["destinations"] == ["Goa"]
        assert "Changed destinations from ['Delhi'] to ['Goa']" in summary
    
    def test_update_destinations_add(self):
        """Test adding destinations"""
        reducer = PreferenceReducer()
        current = {"destinations": ["Delhi"]}
        new = {"destinations": ["Mumbai"]}
        
        updated, summary = reducer.update_preferences(
            current, new, "Also add Mumbai"
        )
        
        assert set(updated["destinations"]) == {"Delhi", "Mumbai"}
        assert "Added ['Mumbai'] to destinations" in summary
    
    def test_update_destinations_add_deduplicate(self):
        """Test that adding existing destination doesn't duplicate"""
        reducer = PreferenceReducer()
        current = {"destinations": ["Delhi"]}
        new = {"destinations": ["Delhi"]}
        
        updated, summary = reducer.update_preferences(
            current, new, "Also include Delhi"
        )
        
        assert updated["destinations"] == ["Delhi"]
        assert "already includes" in summary
    
    def test_update_scalar_duration(self):
        """Test updating scalar values like duration"""
        reducer = PreferenceReducer()
        current = {"duration": 5}
        new = {"duration": 7}
        
        updated, summary = reducer.update_preferences(
            current, new, "Change to 7 days"
        )
        
        assert updated["duration"] == 7
        assert "Updated duration from '5' to '7'" in summary
    
    def test_update_multiple_preferences(self):
        """Test updating multiple preferences at once"""
        reducer = PreferenceReducer()
        current = {
            "destinations": ["Delhi"],
            "duration": 5
        }
        new = {
            "destinations": ["Goa"],
            "duration": 7
        }
        
        updated, summary = reducer.update_preferences(
            current, new, "Actually, 7 days in Goa instead"
        )
        
        assert updated["destinations"] == ["Goa"]
        assert updated["duration"] == 7
        assert "Changed destinations" in summary
        assert "Updated duration" in summary
    
    def test_update_preserves_other_fields(self):
        """Test that unrelated fields are preserved"""
        reducer = PreferenceReducer()
        current = {
            "destinations": ["Delhi"],
            "budget": "medium",
            "interests": ["culture", "food"]
        }
        new = {"destinations": ["Goa"]}
        
        updated, summary = reducer.update_preferences(
            current, new, "Change to Goa"
        )
        
        assert updated["destinations"] == ["Goa"]
        assert updated["budget"] == "medium"
        assert updated["interests"] == ["culture", "food"]


class TestConfirmationMessages:
    """Test confirmation message generation"""
    
    def test_generate_confirmation_replace(self):
        """Test confirmation for replacement"""
        reducer = PreferenceReducer()
        
        confirmation = reducer.generate_confirmation(
            "Changed destinations from ['Delhi'] to ['Goa']",
            'replace'
        )
        
        assert "✅ Got it!" in confirmation
        assert "Changed destinations" in confirmation
    
    def test_generate_confirmation_add(self):
        """Test confirmation for addition"""
        reducer = PreferenceReducer()
        
        confirmation = reducer.generate_confirmation(
            "Added ['Mumbai'] to destinations",
            'add'
        )
        
        assert "✅ Added!" in confirmation
        assert "Mumbai" in confirmation


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_update_empty_current(self):
        """Test updating when current preferences are empty"""
        reducer = PreferenceReducer()
        current = {}
        new = {"destinations": ["Delhi"]}
        
        updated, summary = reducer.update_preferences(
            current, new, "I want to visit Delhi"
        )
        
        assert updated["destinations"] == ["Delhi"]
        assert "Set destinations to ['Delhi']" in summary
    
    def test_update_empty_new(self):
        """Test updating with empty new preferences"""
        reducer = PreferenceReducer()
        current = {"destinations": ["Delhi"]}
        new = {}
        
        updated, summary = reducer.update_preferences(
            current, new, "Some message"
        )
        
        assert updated == current
        assert summary == "No changes"
    
    def test_singleton_instance(self):
        """Test that preference_reducer is a singleton"""
        from app.services.preference_reducer import preference_reducer as pr1
        from app.services.preference_reducer import preference_reducer as pr2
        
        assert pr1 is pr2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
