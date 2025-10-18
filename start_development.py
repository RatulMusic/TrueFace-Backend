"""
Development Startup Script for TrueFACE Backend
Configured for development with relaxed security settings
"""

import os
import sys
import logging

def setup_development_environment():
    """Setup development environment variables"""
    print("🔧 Setting up development environment...")
    
    # Development settings
    os.environ['DEBUG'] = 'true'
    os.environ['RELOAD'] = 'true'
    os.environ['LOG_LEVEL'] = 'INFO'
    os.environ['ENABLE_API_KEY_AUTH'] = 'false'  # Disabled for easier development
    
    # Relaxed security for development
    os.environ['ALLOWED_ORIGINS'] = '["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8080"]'
    os.environ['MAX_CONNECTIONS_PER_IP'] = '10'
    os.environ['API_KEY'] = 'dev_api_key_123'
    
    print("✅ Development environment configured")

def check_dependencies():
    """Check if core dependencies are installed"""
    print("📦 Checking core dependencies...")

    core_packages = {
        'fastapi': 'fastapi',
        'uvicorn': 'uvicorn',
        'torch': 'torch',
        'opencv-python': 'cv2'  # Correct import name
    }
    missing = []

    for package, import_name in core_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing.append(package)

    if missing:
        print("❌ Missing core dependencies:")
        for pkg in missing:
            print(f"   - {pkg}")
        print("\nInstall with: pip install -r requirements.txt")
        return False
    else:
        print("✅ Core dependencies available")
        return True

def start_server():
    """Start the development server"""
    print("🚀 Starting TrueFACE Backend in development mode...")
    
    import uvicorn
    from config import settings
    
    # Development server configuration
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=True,
        log_level="info",
        access_log=True
    )

def main():
    """Main startup function"""
    print("=" * 60)
    print("🛠️  TrueFACE Backend - Development Mode")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Setup environment
    setup_development_environment()
    
    print("\n🔧 DEVELOPMENT CONFIGURATION:")
    print("✅ Debug mode enabled")
    print("✅ Auto-reload active")
    print("✅ API authentication disabled")
    print("✅ Permissive CORS settings")
    print("✅ Detailed logging enabled")
    print("✅ API docs available at /docs")
    
    print(f"\n🌐 Server will be available at: http://localhost:{os.getenv('PORT', 8000)}")
    print(f"🔌 WebSocket endpoint: ws://localhost:{os.getenv('PORT', 8000)}/ws")
    print(f"📚 API Documentation: http://localhost:{os.getenv('PORT', 8000)}/docs")
    
    print("\n💡 DEVELOPMENT NOTES:")
    print("1. API authentication is disabled for easier testing")
    print("2. CORS allows localhost origins")
    print("3. Auto-reload watches for file changes")
    print("4. Detailed error messages are shown")
    print("5. Use test_real_detection.py to test functionality")
    
    print("\nStarting development server...")
    
    # Start the server
    start_server()

if __name__ == "__main__":
    main()
