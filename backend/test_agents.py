"""
Watchout Backend - Agent Testing Script
Tests all AI agents individually to verify they are working properly.
"""
import asyncio
import sys
import os
from typing import Dict, Any

# Set encoding for Windows console
sys.stdout.reconfigure(encoding='utf-8')

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from colorama import init, Fore, Style
init()  # Initialize colorama for Windows

def print_header(text: str):
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f" {text}")
    print(f"{'='*60}{Style.RESET_ALL}\n")

def print_success(text: str):
    print(f"{Fore.GREEN}[PASS] {text}{Style.RESET_ALL}")

def print_error(text: str):
    print(f"{Fore.RED}[FAIL] {text}{Style.RESET_ALL}")

def print_info(text: str):
    print(f"{Fore.YELLOW}-> {text}{Style.RESET_ALL}")

def print_result(key: str, value: Any):
    print(f"{Fore.WHITE}  {key}: {Fore.CYAN}{value}{Style.RESET_ALL}")


async def test_clarification_agent():
    """Test the Clarification Agent"""
    print_header("Testing ClarificationAgent")
    
    try:
        from app.agents.clarification import ClarificationAgent
        agent = ClarificationAgent()
        print_success(f"Agent created: {agent.name}")
        
        # Test initial greeting
        print_info("Testing initial greeting...")
        greeting = await agent.generate_initial_greeting()
        print_result("Greeting", greeting[:100] + "..." if len(greeting) > 100 else greeting)
        
        # Test preference extraction
        print_info("Testing preference extraction...")
        result = await agent.run(
            "I want to go to Goa for 5 days with my family, budget is around 50000 rupees",
            context={}
        )
        
        print_result("Response", result.get("response", "")[:150] + "...")
        print_result("Is Complete", result.get("is_complete", False))
        print_result("Extracted Prefs", result.get("extracted_preferences", {}))
        
        return True, "ClarificationAgent working properly"
        
    except Exception as e:
        print_error(f"ClarificationAgent failed: {str(e)}")
        return False, str(e)


async def test_weather_agent():
    """Test the Weather Agent"""
    print_header("Testing WeatherAgent")
    
    try:
        from app.agents.weather import WeatherAgent
        agent = WeatherAgent()
        print_success(f"Agent created: {agent.name}")
        
        # Test weather query with context
        print_info("Testing weather forecast for Mumbai...")
        result = await agent.run(
            "What's the weather like?",
            context={"city": "Mumbai"}
        )
        
        print_result("Response", result.get("response", "")[:200] + "..." if len(result.get("response", "")) > 200 else result.get("response", ""))
        print_result("Has Weather Data", result.get("weather") is not None)
        
        # Test multi-city weather
        print_info("Testing multi-city weather...")
        cities_weather = await agent.get_weather_for_trip(["Delhi", "Jaipur"])
        print_result("Cities Retrieved", len(cities_weather))
        
        return True, "WeatherAgent working properly"
        
    except Exception as e:
        print_error(f"WeatherAgent failed: {str(e)}")
        return False, str(e)


async def test_food_agent():
    """Test the Food Agent"""
    print_header("Testing FoodAgent")
    
    try:
        from app.agents.food import FoodAgent
        agent = FoodAgent()
        print_success(f"Agent created: {agent.name}")
        
        # Test food recommendations
        print_info("Testing food recommendations for Jaipur...")
        result = await agent.run(
            "What should I eat?",
            context={"city": "Jaipur"}
        )
        
        print_result("Response", result.get("response", "")[:200] + "..." if len(result.get("response", "")) > 200 else result.get("response", ""))
        print_result("Has Restaurants", result.get("restaurants") is not None)
        print_result("Restaurant Count", len(result.get("restaurants", [])) if result.get("restaurants") else 0)
        
        return True, "FoodAgent working properly"
        
    except Exception as e:
        print_error(f"FoodAgent failed: {str(e)}")
        return False, str(e)


async def test_stay_agent():
    """Test the Stay Agent"""
    print_header("Testing StayAgent")
    
    try:
        from app.agents.stay import StayAgent
        agent = StayAgent()
        print_success(f"Agent created: {agent.name}")
        
        # Test accommodation search
        print_info("Testing accommodation search in Goa...")
        result = await agent.run(
            "Find me a hotel",
            context={
                "city": "Goa",
                "budget": "mid-range",
                "preferences": {"type": "beach resort"}
            }
        )
        
        print_result("Response", result.get("response", "")[:200] + "..." if len(result.get("response", "")) > 200 else result.get("response", ""))
        print_result("Has Accommodations", result.get("accommodations") is not None)
        
        return True, "StayAgent working properly"
        
    except Exception as e:
        print_error(f"StayAgent failed: {str(e)}")
        return False, str(e)


async def test_transportation_agent():
    """Test the Transportation Agent"""
    print_header("Testing TransportationAgent")
    
    try:
        from app.agents.transportation import TransportationAgent
        agent = TransportationAgent()
        print_success(f"Agent created: {agent.name}")
        
        # Test transportation options
        print_info("Testing transport from Delhi to Jaipur...")
        result = await agent.run(
            "How do I get there?",
            context={
                "from_city": "Delhi",
                "to_city": "Jaipur",
                "budget": "mid-range"
            }
        )
        
        print_result("Response", result.get("response", "")[:250] + "..." if len(result.get("response", "")) > 250 else result.get("response", ""))
        print_result("Has Options", result.get("options") is not None or "transport" in result.get("response", "").lower())
        
        return True, "TransportationAgent working properly"
        
    except Exception as e:
        print_error(f"TransportationAgent failed: {str(e)}")
        return False, str(e)


async def test_route_agent():
    """Test the Route Agent"""
    print_header("Testing RouteAgent")
    
    try:
        from app.agents.route import RouteAgent
        agent = RouteAgent()
        print_success(f"Agent created: {agent.name}")
        
        # Test route calculation
        print_info("Testing route calculation...")
        stops = [
            {"name": "India Gate", "latitude": 28.6129, "longitude": 77.2295},
            {"name": "Lotus Temple", "latitude": 28.5535, "longitude": 77.2588},
            {"name": "Qutub Minar", "latitude": 28.5245, "longitude": 77.1855}
        ]
        
        result = await agent.run(
            "Calculate route",
            context={"stops": stops}
        )
        
        print_result("Response", result.get("response", "")[:200] + "..." if len(result.get("response", "")) > 200 else result.get("response", ""))
        print_result("Has Route", result.get("route") is not None)
        print_result("Total Travel Time", result.get("total_travel_time", "N/A"))
        
        return True, "RouteAgent working properly"
        
    except Exception as e:
        print_error(f"RouteAgent failed: {str(e)}")
        return False, str(e)


async def test_itinerary_agent():
    """Test the Itinerary Agent"""
    print_header("Testing ItineraryAgent")
    
    try:
        from app.agents.itinerary import ItineraryAgent
        agent = ItineraryAgent()
        print_success(f"Agent created: {agent.name}")
        
        # Test itinerary generation
        print_info("Testing itinerary generation for Goa trip...")
        result = await agent.run(
            "Plan my trip",
            context={
                "preferences": {
                    "destinations": ["Goa"],
                    "duration_days": 3,
                    "num_travelers": 2,
                    "budget_range": "mid-range",
                    "travel_vibe": ["beach", "relaxation"]
                },
                "places_data": {},
                "weather_data": {}
            }
        )
        
        print_result("Response", result.get("response", "")[:200] + "..." if len(result.get("response", "")) > 200 else result.get("response", ""))
        print_result("Has Itinerary", result.get("itinerary") is not None)
        print_result("Has Raw Plan", result.get("raw_plan") is not None)
        
        return True, "ItineraryAgent working properly"
        
    except Exception as e:
        print_error(f"ItineraryAgent failed: {str(e)}")
        return False, str(e)


async def test_supervisor_agent():
    """Test the Supervisor Agent (Orchestrator)"""
    print_header("Testing SupervisorAgent")
    
    try:
        from app.agents.supervisor import SupervisorAgent
        agent = SupervisorAgent()
        print_success("SupervisorAgent created")
        
        # Test message processing (initial greeting)
        print_info("Testing message processing...")
        events = []
        async for event in agent.process_message(
            user_id="test_user_123",
            message="Hi, I want to plan a trip to Goa",
            trip_context={}
        ):
            events.append(event)
            if event.get("type") == "token":
                # Just count tokens, don't print each one
                pass
            elif event.get("type") == "status":
                print_info(f"Status: {event.get('message', '')}")
            elif event.get("type") == "data":
                print_result("Data received", event.get("key", "unknown"))
        
        print_result("Total events", len(events))
        print_result("Event types", list(set(e.get("type") for e in events)))
        
        return True, "SupervisorAgent working properly"
        
    except Exception as e:
        print_error(f"SupervisorAgent failed: {str(e)}")
        return False, str(e)


async def run_all_tests():
    """Run all agent tests"""
    print(f"\n{Fore.MAGENTA}{'#'*60}")
    print("#           WATCHOUT BACKEND - AGENT TESTING")
    print(f"{'#'*60}{Style.RESET_ALL}")
    
    tests = [
        ("ClarificationAgent", test_clarification_agent),
        ("WeatherAgent", test_weather_agent),
        ("FoodAgent", test_food_agent),
        ("StayAgent", test_stay_agent),
        ("TransportationAgent", test_transportation_agent),
        ("RouteAgent", test_route_agent),
        ("ItineraryAgent", test_itinerary_agent),
        ("SupervisorAgent", test_supervisor_agent),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            success, message = await test_func()
            results.append((name, success, message))
        except Exception as e:
            results.append((name, False, str(e)))
    
    # Print summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for _, success, _ in results if success)
    failed = len(results) - passed
    
    for name, success, message in results:
        if success:
            print_success(f"{name}: {message}")
        else:
            print_error(f"{name}: {message}")
    
    print(f"\n{Fore.WHITE}{'-'*40}")
    print(f"Total: {len(results)} | {Fore.GREEN}Passed: {passed}{Fore.WHITE} | {Fore.RED}Failed: {failed}{Style.RESET_ALL}")
    
    if failed == 0:
        print(f"\n{Fore.GREEN}SUCCESS: All agents are working properly!{Style.RESET_ALL}\n")
    else:
        print(f"\n{Fore.RED}WARNING: Some agents need attention.{Style.RESET_ALL}\n")
    
    return results


if __name__ == "__main__":
    asyncio.run(run_all_tests())
