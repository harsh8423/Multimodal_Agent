#!/usr/bin/env python3
"""
Quick test script for media generation tools.
This script provides simple examples for testing each service.
"""

import os
import sys
from dotenv import load_dotenv

# Add the tools directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools', 'media_generation'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

# Load environment variables with error handling
try:
    load_dotenv()
except Exception as e:
    print(f"Warning: Could not load .env file: {e}")

def check_environment_variables():
    """Check and display environment variable status."""
    print("🔍 Environment Variables Check:")
    
    env_vars = {
        "KIE_API_KEY": "KIE Image Generation",
        "GEMINI_API_KEY": "Gemini Audio Generation", 
        "MINIMAX_API_KEY": "Minimax Audio Generation",
        "AZURE_SPEECH_KEY": "Microsoft TTS",
        "AZURE_SPEECH_REGION": "Microsoft TTS Region",
        "CLOUDINARY_CLOUD_NAME": "Cloudinary Cloud Name",
        "CLOUDINARY_UPLOAD_PRESET": "Cloudinary Upload Preset"
    }
    
    missing_vars = []
    for var, description in env_vars.items():
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var}: Set ({description})")
        else:
            print(f"  ❌ {var}: Not set ({description})")
            missing_vars.append(var)
    
    return missing_vars

def test_gemini_audio_quick():
    """Quick test for Gemini audio generation."""
    print("🎤 Testing Gemini Audio Generation...")
    
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ Skipped: GEMINI_API_KEY not set")
        return {"status": "failed", "url": None, "msg": "GEMINI_API_KEY not set", "skipped": True}
    
    try:
        from gemini_audio import generate_audio
        
        result = generate_audio(
            text="Hello! This is a quick test of Gemini TTS.",
            voice_name="Kore",
            cloudinary_options={"folder": "test/quick"}
        )
        
        if result.get("status") == "success":
            print(f"✅ Success! URL: {result.get('url')}")
        else:
            print(f"❌ Failed: {result.get('msg')}")
        
        return result
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return {"status": "failed", "url": None, "msg": str(e)}

def test_microsoft_tts_quick():
    """Quick test for Microsoft TTS."""
    print("🎤 Testing Microsoft TTS...")
    
    if not os.getenv("AZURE_SPEECH_KEY") or not os.getenv("AZURE_SPEECH_REGION"):
        print("❌ Skipped: AZURE_SPEECH_KEY or AZURE_SPEECH_REGION not set")
        return {"status": "failed", "url": None, "msg": "Azure Speech credentials not set", "skipped": True}
    
    try:
        from microsoft_tts import generate_audio_microsoft
        
        result = generate_audio_microsoft(
            text="Hello! This is a quick test of Microsoft TTS.",
            voice_name="en-US-AriaNeural",
            cloudinary_options={"folder": "test/quick"}
        )
        
        if result.get("status") == "success":
            print(f"✅ Success! URL: {result.get('url')}")
        else:
            print(f"❌ Failed: {result.get('msg')}")
        
        return result
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return {"status": "failed", "url": None, "msg": str(e)}

def test_minimax_audio_quick():
    """Quick test for Minimax audio generation."""
    print("🎤 Testing Minimax Audio Generation...")
    
    if not os.getenv("MINIMAX_API_KEY"):
        print("❌ Skipped: MINIMAX_API_KEY not set")
        return {"status": "failed", "url": None, "msg": "MINIMAX_API_KEY not set", "skipped": True}
    
    try:
        from minimax_audio_clone import generate_minimax_audio
        
        result = generate_minimax_audio(
            text="Hello! This is a quick test of Minimax TTS.",
            voice_id="English_expressive_narrator",
            max_wait_time=120,  # 2 minutes for quick test
            poll_interval=5,    # Check every 5 seconds
            cloudinary_options={"folder": "test/quick"}
        )
        
        if result.get("status") == "success":
            print(f"✅ Success! URL: {result.get('url')}")
        else:
            print(f"❌ Failed: {result.get('msg')}")
        
        return result
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return {"status": "failed", "url": None, "msg": str(e)}

def test_kie_image_quick():
    """Quick test for KIE image generation."""
    print("🖼️  Testing KIE Image Generation...")
    
    if not os.getenv("KIE_API_KEY"):
        print("❌ Skipped: KIE_API_KEY not set")
        return {"status": "failed", "url": None, "msg": "KIE_API_KEY not set", "skipped": True}
    
    try:
        from kie_image_generation import generate_kie_image
        
        result = generate_kie_image(
            prompt="A simple red apple on a white background",
            image_urls=["https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=512&h=512&fit=crop"],
            max_wait_time=300,  # 5 minutes for quick test
            poll_interval=10,   # Check every 10 seconds
            cloudinary_options={"folder": "test/quick"}
        )
        
        if result.get("status") == "success":
            print(f"✅ Success! URL: {result.get('url')}")
        else:
            print(f"❌ Failed: {result.get('msg')}")
        
        return result
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return {"status": "failed", "url": None, "msg": str(e)}

def main():
    """Run quick tests for all services."""
    print("🚀 Quick Media Generation Tests")
    print("=" * 40)
    
    # Check environment variables
    missing_vars = check_environment_variables()
    
    # Check if we have the basic required variables
    required_vars = ["CLOUDINARY_CLOUD_NAME", "CLOUDINARY_UPLOAD_PRESET"]
    critical_missing = [var for var in required_vars if var in missing_vars]
    
    if critical_missing:
        print(f"\n❌ Missing critical environment variables: {', '.join(critical_missing)}")
        print("Cannot proceed without Cloudinary configuration.")
        return
    
    print(f"\n✅ Critical environment variables found")
    if missing_vars:
        print(f"⚠️  Some optional variables missing: {', '.join(missing_vars)}")
        print("Some tests may be skipped.")
    print()
    
    # Test each service
    tests = [
        ("Gemini Audio", test_gemini_audio_quick),
        ("Microsoft TTS", test_microsoft_tts_quick),
        ("Minimax Audio", test_minimax_audio_quick),
        ("KIE Image", test_kie_image_quick),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            print(f"\n--- {test_name} ---")
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Exception in {test_name}: {str(e)}")
            results[test_name] = {"success": False, "error": str(e)}
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 Quick Test Summary")
    print("=" * 40)
    
    successful = sum(1 for result in results.values() if result.get("status") == "success")
    skipped = sum(1 for result in results.values() if result.get("skipped"))
    failed = len(results) - successful - skipped
    
    for test_name, result in results.items():
        if result.get("skipped"):
            status = "⏭️"
        elif result.get("status") == "success":
            status = "✅"
        else:
            status = "❌"
        print(f"{status} {test_name}")
    
    print(f"\nResults: {successful} passed, {failed} failed, {skipped} skipped")
    if successful + failed > 0:
        print(f"Success Rate: {successful}/{successful + failed} ({(successful/(successful + failed))*100:.1f}%)")
    
    # Show URLs for successful tests
    successful_results = {name: result for name, result in results.items() if result.get("status") == "success" and result.get("url")}
    if successful_results:
        print(f"\n🌐 Generated URLs:")
        for test_name, result in successful_results.items():
            print(f"  {test_name}: {result.get('url')}")

if __name__ == "__main__":
    main()