#!/usr/bin/env python3
"""
Calendly Analytics - Complete Application Runner
Single script to setup and run the entire application
"""

import os
import sys
import subprocess
import threading
import time
import webbrowser
from pathlib import Path
import json
from datetime import datetime

class CalendlyAppRunner:
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.processes = []
        self.backend_ready = False
        self.frontend_ready = False
        self.setup_directories()
        
    def log(self, message, level="INFO"):
        """Print formatted log message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        colors = {
            "INFO": "\033[94m",     # Blue
            "SUCCESS": "\033[92m",  # Green
            "WARNING": "\033[93m",  # Yellow
            "ERROR": "\033[91m",    # Red
            "RESET": "\033[0m"
        }
        color = colors.get(level, colors["INFO"])
        reset = colors["RESET"]
        print(f"{color}[{timestamp}] {level}: {message}{reset}")
        
    def setup_directories(self):
        """Create the necessary directory structure"""
        directories = [
            'backend/app',
            'backend/app/api',
            'backend/app/core', 
            'backend/app/services',
            'backend/app/models',
            'frontend/src/components',
            'frontend/src/hooks',
            'frontend/src/services',
            'frontend/src/styles',
            'frontend/src/utils',
            'calendly_dump/invitees',
            'scripts'
        ]
        
        for dir_path in directories:
            (self.root_dir / dir_path).mkdir(parents=True, exist_ok=True)
        
        self.log("Directory structure created", "SUCCESS")
    
    def check_dependencies(self):
        """Check and install dependencies"""
        self.log("Checking dependencies...")
        
        # Check Python
        try:
            result = subprocess.run([sys.executable, '--version'], check=True, capture_output=True, text=True)
            self.log(f"Python version: {result.stdout.strip()}", "SUCCESS")
        except:
            self.log("Python is required but not found", "ERROR")
            sys.exit(1)
        
        # Check Node.js
        try:
            result = subprocess.run(['node', '--version'], check=True, capture_output=True, text=True)
            self.log(f"Node.js version: {result.stdout.strip()}", "SUCCESS")
        except:
            self.log("Node.js is not installed - frontend will be skipped", "WARNING")
        
        self.log("All required dependencies are available", "SUCCESS")
    
    def create_frontend_files(self):
        """Create all necessary frontend files"""
        frontend_dir = self.root_dir / 'frontend'
        
        self.log("Creating frontend configuration files...")
        
        # Check if files already exist
        required_files = ['package.json', 'index.html', 'vite.config.ts', 'tsconfig.json']
        missing_files = [f for f in required_files if not (frontend_dir / f).exists()]
        
        if missing_files:
            self.log(f"Missing frontend files: {', '.join(missing_files)}", "WARNING")
            self.log("Creating frontend files from templates...", "INFO")
            
            # Create package.json
            package_json = {
                "name": "calendly-analytics-frontend",
                "version": "1.0.0",
                "type": "module",
                "scripts": {
                    "dev": "vite",
                    "build": "tsc && vite build",
                    "preview": "vite preview"
                },
                "dependencies": {
                    "react": "^18.2.0",
                    "react-dom": "^18.2.0",
                    "react-query": "^3.39.3",
                    "axios": "^1.6.2",
                    "recharts": "^2.10.3",
                    "framer-motion": "^10.16.16",
                    "lucide-react": "^0.294.0"
                },
                "devDependencies": {
                    "@types/react": "^18.2.43",
                    "@types/react-dom": "^18.2.17",
                    "@vitejs/plugin-react": "^4.2.1",
                    "typescript": "^5.3.3",
                    "vite": "^4.5.1",
                    "tailwindcss": "^3.3.6",
                    "autoprefixer": "^10.4.16",
                    "postcss": "^8.4.32"
                }
            }
            
            with open(frontend_dir / 'package.json', 'w') as f:
                json.dump(package_json, f, indent=2)
            self.log("Created package.json", "SUCCESS")
            
            # Create index.html
            index_html = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Calendly Analytics Dashboard</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
"""
            with open(frontend_dir / 'index.html', 'w') as f:
                f.write(index_html)
            self.log("Created index.html", "SUCCESS")
            
            # Create vite.config.ts
            vite_config = """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true
  }
})
"""
            with open(frontend_dir / 'vite.config.ts', 'w') as f:
                f.write(vite_config)
            self.log("Created vite.config.ts", "SUCCESS")
            
            # Create tsconfig.json
            tsconfig = {
                "compilerOptions": {
                    "target": "ES2020",
                    "useDefineForClassFields": True,
                    "lib": ["ES2020", "DOM", "DOM.Iterable"],
                    "module": "ESNext",
                    "skipLibCheck": True,
                    "moduleResolution": "bundler",
                    "allowImportingTsExtensions": True,
                    "resolveJsonModule": True,
                    "isolatedModules": True,
                    "noEmit": True,
                    "jsx": "react-jsx",
                    "strict": True,
                    "noUnusedLocals": True,
                    "noUnusedParameters": True,
                    "noFallthroughCasesInSwitch": True
                },
                "include": ["src"],
                "references": [{"path": "./tsconfig.node.json"}]
            }
            with open(frontend_dir / 'tsconfig.json', 'w') as f:
                json.dump(tsconfig, f, indent=2)
            self.log("Created tsconfig.json", "SUCCESS")
            
            # Create tsconfig.node.json
            tsconfig_node = {
                "compilerOptions": {
                    "composite": True,
                    "skipLibCheck": True,
                    "module": "ESNext",
                    "moduleResolution": "bundler",
                    "allowSyntheticDefaultImports": True
                },
                "include": ["vite.config.ts"]
            }
            with open(frontend_dir / 'tsconfig.node.json', 'w') as f:
                json.dump(tsconfig_node, f, indent=2)
            self.log("Created tsconfig.node.json", "SUCCESS")
            
            # Create tailwind.config.js
            tailwind_config = """/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
"""
            with open(frontend_dir / 'tailwind.config.js', 'w') as f:
                f.write(tailwind_config)
            self.log("Created tailwind.config.js", "SUCCESS")
            
            # Create postcss.config.js
            postcss_config = """export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
"""
            with open(frontend_dir / 'postcss.config.js', 'w') as f:
                f.write(postcss_config)
            self.log("Created postcss.config.js", "SUCCESS")
            
        else:
            self.log("All frontend configuration files exist", "SUCCESS")
        
        # Check if src files exist
        src_dir = frontend_dir / 'src'
        if not (src_dir / 'main.tsx').exists():
            self.log("Frontend source files are missing!", "ERROR")
            self.log("Please ensure these files exist in frontend/src/:", "INFO")
            self.log("  - main.tsx", "INFO")
            self.log("  - App.tsx", "INFO")
            self.log("  - index.css", "INFO")
            self.log("  - components/Dashboard.tsx", "INFO")
            self.log("\nRefer to the previous messages for the complete file contents.", "INFO")
            return False
        
        return True
    
    def setup_backend(self):
        """Setup FastAPI backend"""
        backend_dir = self.root_dir / 'backend'
        
        self.log("Setting up backend...")
        
        # Create requirements.txt with Python 3.13 compatible versions
        requirements = """fastapi
            uvicorn
            python-dotenv
            pandas
            plotly
            numpy
            scipy
            scikit-learn
            matplotlib
            seaborn
            requests
            aiofiles
            python-multipart
            pydantic
            pydantic-settings
        """
        
        with open(backend_dir / 'requirements.txt', 'w') as f:
            f.write(requirements)
        
        # Create .env file if it doesn't exist
        env_file = backend_dir / '.env'
        if not env_file.exists():
            env_content = """CALENDLY_API_KEY=your_calendly_api_key_here
SECRET_KEY=your-secret-key-change-in-production
ALLOWED_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
DATA_DIR=./calendly_dump
"""
            with open(env_file, 'w') as f:
                f.write(env_content)
            self.log("Please update backend/.env with your Calendly API key", "WARNING")
        
        self.log("Backend setup complete", "SUCCESS")
    
    def setup_frontend(self):
        """Setup React frontend"""
        self.log("Setting up frontend...")
        
        if not self.create_frontend_files():
            self.log("Frontend setup incomplete - missing source files", "ERROR")
            return False
        
        self.log("Frontend setup complete", "SUCCESS")
        return True
    
    def install_dependencies(self):
        """Install all dependencies"""
        self.log("Installing dependencies...")
        self.log("This may take several minutes, especially for scipy and matplotlib...", "INFO")
        
        # Upgrade pip first
        self.log("Upgrading pip...")
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'
        ], capture_output=True)
        
        # Backend Python dependencies
        backend_dir = self.root_dir / 'backend'
        self.log("Installing Python packages (downloading pre-built wheels)...")
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', 
            '--prefer-binary',
            '-r', str(backend_dir / 'requirements.txt')
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            self.log("Error installing Python dependencies:", "ERROR")
            self.log(result.stderr, "ERROR")
            sys.exit(1)
        
        self.log("Python dependencies installed successfully", "SUCCESS")
        
        # Frontend Node.js dependencies
        frontend_dir = self.root_dir / 'frontend'
        if (frontend_dir / 'package.json').exists():
            self.log("Installing Node.js packages...")
            
            # Check if node_modules exists
            if not (frontend_dir / 'node_modules').exists():
                self.log("node_modules not found, running npm install...", "INFO")
                result = subprocess.run(
                    ['npm', 'install'], 
                    cwd=frontend_dir, 
                    capture_output=True, 
                    text=True
                )
                if result.returncode != 0:
                    self.log("Error installing Node.js dependencies:", "ERROR")
                    self.log(result.stderr, "ERROR")
                    return False
                self.log("Node.js dependencies installed", "SUCCESS")
            else:
                self.log("node_modules found, skipping npm install", "INFO")
        
        self.log("All dependencies installed", "SUCCESS")
        return True
    
    def start_backend(self):
        """Start FastAPI backend"""
        backend_dir = self.root_dir / 'backend'
        
        self.log("Starting backend server...")
        
        def run_backend():
            try:
                subprocess.run([
                    sys.executable, '-m', 'uvicorn', 'app.main:app', 
                    '--host', '0.0.0.0', 
                    '--port', '8000',
                    '--reload'
                ], cwd=backend_dir)
            except KeyboardInterrupt:
                pass
        
        backend_thread = threading.Thread(target=run_backend)
        backend_thread.daemon = True
        backend_thread.start()
        self.processes.append(backend_thread)
        
        time.sleep(5)
        self.log("Backend server started on http://localhost:8000", "SUCCESS")
        self.backend_ready = True
    
    def start_frontend(self):
        """Start React frontend"""
        frontend_dir = self.root_dir / 'frontend'
        
        self.log("Starting frontend server...")
        
        # Verify required files
        required_files = ['index.html', 'package.json', 'src/main.tsx']
        missing = [f for f in required_files if not (frontend_dir / f).exists()]
        
        if missing:
            self.log(f"Cannot start frontend - missing files: {', '.join(missing)}", "ERROR")
            self.log("Frontend will not be available", "WARNING")
            return False
        
        def run_frontend():
            try:
                result = subprocess.run(
                    ['npm', 'run', 'dev'], 
                    cwd=frontend_dir,
                    capture_output=False  # Show output in console
                )
            except KeyboardInterrupt:
                pass
        
        frontend_thread = threading.Thread(target=run_frontend)
        frontend_thread.daemon = True
        frontend_thread.start()
        self.processes.append(frontend_thread)
        
        time.sleep(3)
        self.log("Frontend server started on http://localhost:3000", "SUCCESS")
        self.frontend_ready = True
        return True
    
    def check_services(self):
        """Check if services are running properly"""
        self.log("Checking services...")
        
        # Check backend
        if self.backend_ready:
            max_retries = 5
            for i in range(max_retries):
                try:
                    import requests
                    response = requests.get('http://localhost:8000/health', timeout=10)
                    if response.status_code == 200:
                        self.log("Backend is healthy", "SUCCESS")
                        break
                except ImportError:
                    self.log("requests module not found, skipping health check", "WARNING")
                    break
                except Exception as e:
                    if i < max_retries - 1:
                        self.log(f"Backend not ready yet, retrying... ({i+1}/{max_retries})", "INFO")
                        time.sleep(2)
                    else:
                        self.log(f"Backend health check failed: {e}", "WARNING")
        
        # Check frontend
        if self.frontend_ready:
            time.sleep(2)
            try:
                import requests
                response = requests.get('http://localhost:3000', timeout=5)
                if response.status_code == 200:
                    self.log("Frontend is healthy and serving content", "SUCCESS")
                else:
                    self.log(f"Frontend responded with status {response.status_code}", "WARNING")
            except Exception as e:
                self.log(f"Frontend check: {str(e)}", "WARNING")
                self.log("This is normal if frontend is still starting up", "INFO")
    
    def open_browser(self):
        """Open browser after services are ready"""
        time.sleep(5)
        self.log("Opening application in browser...")
        try:
            if self.frontend_ready:
                webbrowser.open('http://localhost:3000')
                self.log("Opened: http://localhost:3000 (Frontend)", "INFO")
            time.sleep(1)
            webbrowser.open('http://localhost:8000/api/docs')
            self.log("Opened: http://localhost:8000/api/docs (API Docs)", "INFO")
        except Exception as e:
            self.log(f"Could not open browser automatically: {e}", "WARNING")
    
    def print_startup_info(self):
        """Print application startup information"""
        print("\n" + "=" * 70)
        print("🎉 CALENDLY ANALYTICS APPLICATION IS RUNNING!")
        print("=" * 70)
        
        if self.backend_ready:
            print("\n📊 BACKEND (FastAPI):")
            print("   🔗 API Root:        http://localhost:8000")
            print("   📚 API Docs:        http://localhost:8000/api/docs")
            print("   ❤️  Health Check:   http://localhost:8000/health")
        
        if self.frontend_ready:
            print("\n🖥️  FRONTEND (React + Vite):")
            print("   🔗 Dashboard:       http://localhost:3000")
            print("   📱 Responsive UI with charts and analytics")
        else:
            print("\n⚠️  FRONTEND:")
            print("   Frontend is not running due to missing source files")
            print("   Please ensure all frontend source files are in place")
        
        print("\n" + "=" * 70)
        print("⌨️  Press Ctrl+C to stop both servers")
        print("=" * 70 + "\n")
    
    def run(self):
        """Main method to run the entire application"""
        print("\n🚀 Starting Calendly Analytics Application...")
        print("=" * 70 + "\n")
        
        try:
            self.check_dependencies()
            self.setup_backend()
            
            frontend_ok = self.setup_frontend()
            
            if not self.install_dependencies():
                self.log("Dependency installation failed", "ERROR")
                sys.exit(1)
            
            self.start_backend()
            
            if frontend_ok:
                self.start_frontend()
            
            self.check_services()
            self.print_startup_info()
            
            # Start browser
            browser_thread = threading.Thread(target=self.open_browser)
            browser_thread.daemon = True
            browser_thread.start()
            
            # Keep main thread alive
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.log("Shutting down Calendly Analytics Application...", "INFO")
            self.log("Thank you for using Calendly Analytics! 👋", "SUCCESS")
        except Exception as e:
            self.log(f"Error: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            sys.exit(1)

def main():
    runner = CalendlyAppRunner()
    runner.run()

if __name__ == '__main__':
    main()