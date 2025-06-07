#!/usr/bin/env python3
"""
Flask Application Runner for Windows
Run this script to start the Flask backend server
No virtual environment required
"""

import os
import sys
import subprocess
import importlib.util

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("❌ Python 3.7 or higher is required")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    
    print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
    return True

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = {
        'flask': 'Flask',
        'flask_cors': 'Flask-CORS', 
        'requests': 'requests'
    }
    
    missing_packages = []
    installed_packages = []
    
    for package_name, display_name in required_packages.items():
        try:
            spec = importlib.util.find_spec(package_name)
            if spec is not None:
                installed_packages.append(display_name)
            else:
                missing_packages.append(display_name)
        except ImportError:
            missing_packages.append(display_name)
    
    if installed_packages:
        print("✅ Installed packages:")
        for pkg in installed_packages:
            print(f"   - {pkg}")
    
    if missing_packages:
        print("❌ Missing required packages:")
        for pkg in missing_packages:
            print(f"   - {pkg}")
        print("\n📦 To install missing packages, run:")
        print("   pip install flask flask-cors requests python-dotenv")
        return False
    
    print("✅ All required packages are installed")
    return True

def check_environment():
    """Check environment variables"""
    env_vars = {
        'GITHUB_TOKEN': 'GitHub Personal Access Token',
        'GITHUB_WEBHOOK_SECRET': 'GitHub Webhook Secret'
    }
    
    configured_vars = []
    missing_vars = []
    
    for var, description in env_vars.items():
        value = os.getenv(var)
        if value and value not in ['your_github_personal_access_token_here', 'your_webhook_secret_here', 'ghp_demo_token_replace_with_real_token', 'demo-webhook-secret-12345']:
            configured_vars.append(f"{var} ({description})")
        else:
            missing_vars.append(f"{var} ({description})")
    
    if configured_vars:
        print("✅ Configured environment variables:")
        for var in configured_vars:
            print(f"   - {var}")
    
    if missing_vars:
        print("⚠️  Missing or default environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n📄 To configure:")
        print("   1. Create a .env file in the backend directory")
        print("   2. Add your GitHub credentials:")
        print("      GITHUB_TOKEN=your_actual_github_token")
        print("      GITHUB_WEBHOOK_SECRET=your_webhook_secret")
        print("   3. The app will work with demo data without these")
    
    return True

def install_missing_packages():
    """Attempt to install missing packages"""
    print("🔄 Attempting to install missing packages...")
    
    packages_to_install = ["flask", "flask-cors", "requests", "python-dotenv"]
    
    try:
        for package in packages_to_install:
            print(f"   Installing {package}...")
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", package
            ], capture_output=True, text=True, check=True)
            
        print("✅ Packages installed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install packages: {e}")
        print("   Please run manually: pip install flask flask-cors requests python-dotenv")
        return False
    except Exception as e:
        print(f"❌ Installation error: {e}")
        return False

def load_environment():
    """Load environment variables from .env file if it exists"""
    env_file = ".env"
    if os.path.exists(env_file):
        try:
            from dotenv import load_dotenv
            load_dotenv()
            print(f"✅ Loaded environment variables from {env_file}")
        except ImportError:
            print("⚠️  python-dotenv not installed, skipping .env file loading")
        except Exception as e:
            print(f"⚠️  Failed to load .env file: {e}")
    else:
        print("ℹ️  No .env file found (this is optional)")

def check_port_availability():
    """Check if port 5000 is available"""
    import socket
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', 5000))
        print("✅ Port 5000 is available")
        return True
    except OSError:
        print("⚠️  Port 5000 is already in use")
        print("   The Flask app will try to use an alternative port")
        return False

def main():
    """Main runner function"""
    print("🚀 GitHub PR Auto-Fix Flask Backend")
    print("🪟 Windows Version (No Virtual Environment)")
    print("=" * 60)
    
    # Check Python version
    if not check_python_version():
        input("Press Enter to exit...")
        sys.exit(1)
    
    print()
    
    # Load environment variables
    load_environment()
    
    print()
    
    # Check dependencies
    if not check_dependencies():
        print("\n🔧 Would you like to install missing packages automatically? (y/n): ", end="")
        response = input().strip().lower()
        if response in ['y', 'yes']:
            if install_missing_packages():
                print("✅ Installation complete! Continuing with startup...")
            else:
                print("❌ Installation failed. Please install packages manually.")
                input("Press Enter to exit...")
                sys.exit(1)
        else:
            print("❌ Cannot continue without required packages")
            input("Press Enter to exit...")
            sys.exit(1)
    
    print()
    
    # Check environment
    check_environment()
    
    print()
    
    # Check port availability
    check_port_availability()
    
    print()
    print("🎯 Starting Flask Application...")
    print("📊 Demo data is pre-loaded for testing")
    print("🌐 API will be available at: http://localhost:5000")
    print("📋 Test the API at: http://localhost:5000/api/health")
    print("🔄 Server will auto-reload on file changes")
    print("🛑 Press Ctrl+C to stop the server")
    print("=" * 60)
    
    # Import and run the Flask app
    try:
        from app import app
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except ImportError as e:
        print(f"\n❌ Failed to import Flask app: {e}")
        print("   Make sure app.py is in the same directory")
        input("Press Enter to exit...")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        print("   Check the error details above")
        input("Press Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    main()