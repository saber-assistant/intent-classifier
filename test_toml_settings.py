#!/usr/bin/env python3
"""
Test script to verify TOML-based settings configuration.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_settings():
    """Test the settings system."""
    print("🔧 Testing TOML-based settings configuration...")
    
    try:
        # Import settings
        from app.conf import settings, conf
        
        print(f"✅ Settings loaded successfully!")
        print(f"   Environment: {settings.ENVIRONMENT}")
        print(f"   API Key: {settings.API_KEY[:10]}..." if settings.API_KEY else "   API Key: NOT SET")
        print(f"   Database URL: {settings.DATABASE_URL}")
        print(f"   API Host: {settings.API_HOST}")
        print(f"   API Port: {settings.API_PORT}")
        print(f"   Queue Type: {settings.QUEUE_TYPE}")
        print(f"   Result Store Type: {settings.RESULT_STORE_TYPE}")
        print(f"   Result Store TTL: {settings.RESULT_STORE_TTL}")
        print(f"   Debug: {settings.DEBUG}")
        
        # Test conf alias
        assert conf.ENVIRONMENT == settings.ENVIRONMENT
        print(f"✅ Conf alias works correctly")
        
        # Test get method
        custom_value = settings.get("NONEXISTENT_SETTING", "default_value")
        assert custom_value == "default_value"
        print(f"✅ Get method with default works")
        
        # Test as_dict
        settings_dict = settings.as_dict()
        assert "API_KEY" in settings_dict
        print(f"✅ as_dict() method works")
        
        print(f"\n🎉 All tests passed! Settings system is working correctly.")
        
    except Exception as e:
        print(f"❌ Error testing settings: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_environment_override():
    """Test environment variable overrides."""
    print(f"\n🔧 Testing environment variable overrides...")
    
    try:
        # Set an environment variable
        os.environ["SABER_API_PORT"] = "9999"
        
        # Reload settings to pick up the change
        from app.conf import settings
        settings.reload()
        
        # Check if the override worked
        if str(settings.API_PORT) == "9999":
            print(f"✅ Environment variable override works! API_PORT = {settings.API_PORT}")
        else:
            print(f"❌ Environment variable override failed. Expected 9999, got {settings.API_PORT}")
            return False
            
        # Clean up
        del os.environ["SABER_API_PORT"]
        settings.reload()
        
    except Exception as e:
        print(f"❌ Error testing environment overrides: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Starting settings configuration tests...\n")
    
    success = True
    success &= test_settings()
    success &= test_environment_override()
    
    if success:
        print(f"\n🎊 All tests completed successfully!")
        sys.exit(0)
    else:
        print(f"\n💥 Some tests failed!")
        sys.exit(1)
