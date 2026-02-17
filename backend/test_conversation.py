"""
Test script to verify conversation persistence is working correctly.
"""
import asyncio
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime


async def test_conversation_storage():
    """Test the ConversationManager functionality."""
    
    print("\n" + "=" * 60)
    print("  TESTING CONVERSATION PERSISTENCE")
    print("=" * 60 + "\n")
    
    # Import after path setup
    from app.services.conversation_manager import ConversationManager
    from app.db.mongo import MongoDB
    
    # Connect to MongoDB
    print("[1] Connecting to MongoDB...")
    try:
        await MongoDB.connect()
        print("    [OK] Connected to MongoDB\n")
    except Exception as e:
        print(f"    [FAIL] Could not connect to MongoDB: {e}")
        print("    Make sure MONGODB_URI is set in .env")
        return False
    
    # Test data
    test_user_id = "test_user_123"
    test_trip_id = f"test_trip_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    print(f"[2] Testing with:")
    print(f"    User ID: {test_user_id}")
    print(f"    Trip ID: {test_trip_id}\n")
    
    # Test 1: Save user message
    print("[3] Saving user message...")
    try:
        await ConversationManager.save_message(
            trip_id=test_trip_id,
            user_id=test_user_id,
            role="user",
            content="I want to plan a 5-day trip to Goa with beaches and parties"
        )
        print("    [OK] User message saved\n")
    except Exception as e:
        print(f"    [FAIL] Could not save user message: {e}")
        return False
    
    # Test 2: Save assistant message
    print("[4] Saving assistant message...")
    try:
        await ConversationManager.save_message(
            trip_id=test_trip_id,
            user_id=test_user_id,
            role="assistant",
            content="That sounds exciting! Goa is perfect for beaches and nightlife. Let me help you plan...",
            metadata={"agents_used": ["clarification", "itinerary"]}
        )
        print("    [OK] Assistant message saved\n")
    except Exception as e:
        print(f"    [FAIL] Could not save assistant message: {e}")
        return False
    
    # Test 3: Retrieve history
    print("[5] Retrieving conversation history...")
    try:
        history = await ConversationManager.get_history(
            trip_id=test_trip_id,
            user_id=test_user_id,
            limit=10
        )
        print(f"    [OK] Retrieved {len(history)} messages\n")
        
        # Display messages
        print("    STORED MESSAGES:")
        print("    " + "-" * 50)
        for i, msg in enumerate(history, 1):
            role = msg.get("role", "unknown").upper()
            content = msg.get("content", "")[:80]
            timestamp = msg.get("timestamp", "N/A")
            metadata = msg.get("metadata", {})
            
            print(f"    [{i}] {role}: {content}...")
            print(f"        Timestamp: {timestamp}")
            if metadata:
                print(f"        Metadata: {metadata}")
            print()
        
    except Exception as e:
        print(f"    [FAIL] Could not retrieve history: {e}")
        return False
    
    # Test 4: Build agent context
    print("[6] Building agent context...")
    try:
        context = await ConversationManager.build_agent_context(
            trip_id=test_trip_id,
            user_id=test_user_id,
            current_message="What about food options?"
        )
        
        print("    [OK] Context built successfully")
        print(f"    - Conversation history: {len(context.get('conversation_history', []))} messages")
        print(f"    - Preferences: {context.get('preferences', {})}")
        print(f"    - Memories: {len(context.get('memories', []))} items\n")
        
    except Exception as e:
        print(f"    [FAIL] Could not build context: {e}")
        return False
    
    # Test 5: Update preferences
    print("[7] Testing preference updates...")
    try:
        success = await ConversationManager.update_trip_preferences(
            trip_id=test_trip_id,
            user_id=test_user_id,
            preferences={
                "destinations": ["Goa"],
                "duration_days": 5,
                "budget_range": "mid_range",
                "travel_vibe": ["party", "beach"]
            }
        )
        print(f"    [OK] Preferences updated: {success}\n")
    except Exception as e:
        print(f"    [FAIL] Could not update preferences: {e}")
        return False
    
    # Test 6: Clear conversation (cleanup)
    print("[8] Cleaning up test data...")
    try:
        cleared = await ConversationManager.clear_conversation(
            trip_id=test_trip_id,
            user_id=test_user_id
        )
        print(f"    [OK] Test conversation cleared: {cleared}\n")
    except Exception as e:
        print(f"    [WARN] Could not clear test data: {e}")
    
    # Disconnect
    await MongoDB.disconnect()
    
    print("=" * 60)
    print("  ALL TESTS PASSED - Conversation persistence working!")
    print("=" * 60 + "\n")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(test_conversation_storage())
    sys.exit(0 if success else 1)
