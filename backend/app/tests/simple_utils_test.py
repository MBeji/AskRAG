"""
Test simple et direct des modules utilitaires
"""

import sys
import os
import asyncio

# Add the backend directory to path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

def test_validation_basic():
    """Test basique du module de validation"""
    print("Testing validation module...")
    
    try:
        # Import direct
        from app.utils.validation import InputValidator
        
        validator = InputValidator()
        
        # Test simple
        result = validator.validate_query("Test query")
        print(f"Validation result: {result}")
        
        if result["valid"]:
            print("✅ Validation module works!")
            return True
        else:
            print("❌ Validation failed")
            return False
            
    except Exception as e:
        print(f"❌ Validation module error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_response_formatter_basic():
    """Test basique du module de formatage"""
    print("Testing response formatter module...")
    
    try:
        from app.utils.response_formatter import ResponseFormatter
        
        formatter = ResponseFormatter()
        
        # Test simple
        response = formatter.success({"test": "data"}, "Test message")
        print(f"Response: {response}")
        
        if response.success:
            print("✅ Response formatter works!")
            return True
        else:
            print("❌ Response formatter failed")
            return False
            
    except Exception as e:
        print(f"❌ Response formatter error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_cache_basic():
    """Test basique du système de cache"""
    print("Testing cache module...")
    
    try:
        from app.utils.cache import CacheManager
        
        cache = CacheManager.create_memory_cache()
        
        # Test simple
        await cache.backend.set("test_key", "test_value")
        value = await cache.backend.get("test_key")
        
        if value == "test_value":
            print("✅ Cache module works!")
            return True
        else:
            print("❌ Cache module failed")
            return False
            
    except Exception as e:
        print(f"❌ Cache module error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_debug_basic():
    """Test basique du module de debug"""
    print("Testing debug module...")
    
    try:
        from app.utils.debug_helpers import RAGDebugger
        
        debugger = RAGDebugger(enabled=True)
        
        # Test simple
        debugger.log_step("test_step", {"data": "test"})
        summary = debugger.get_debug_summary()
        
        if summary["total_steps"] == 1:
            print("✅ Debug module works!")
            return True
        else:
            print("❌ Debug module failed")
            return False
            
    except Exception as e:
        print(f"❌ Debug module error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_metrics_basic():
    """Test basique du module de métriques"""
    print("Testing metrics module...")
    
    try:
        from app.utils.metrics import MetricsCollector, Counter
        
        collector = MetricsCollector()
        counter = Counter("test_counter")
        
        # Test simple
        counter.increment()
        
        if counter.get_value() == 1:
            print("✅ Metrics module works!")
            return True
        else:
            print("❌ Metrics module failed")
            return False
            
    except Exception as e:
        print(f"❌ Metrics module error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Fonction principale de test"""
    print("🚀 Testing utility modules...\n")
    
    results = []
    
    # Tests synchrones
    results.append(test_validation_basic())
    results.append(test_response_formatter_basic())
    results.append(test_debug_basic())
    results.append(test_metrics_basic())
    
    # Tests asynchrones
    results.append(await test_cache_basic())
    
    success_count = sum(results)
    total_count = len(results)
    
    print(f"\n📊 Results: {success_count}/{total_count} tests passed")
    
    if success_count == total_count:
        print("🎉 All utility modules are working correctly!")
        print("✅ Step 16.3.6 - Utility modules tests completed successfully!")
    else:
        print("❌ Some utility modules have issues")
    
    return success_count == total_count

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
