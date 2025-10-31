# Calendly Analytics - FAANG Grade Application

A state-of-the-art analytics platform for Calendly data with modern UI/UX and advanced visualizations.

## Features

- 🚀 **FastAPI Backend** - High-performance Python backend
- ⚛️ **React Frontend** - Modern, responsive UI with TypeScript
- 📊 **Advanced Analytics** - Comprehensive Calendly data analysis
- 🎨 **Modern UI/UX** - Glass morphism, animations, and beautiful charts
- 🔄 **Real-time Data** - Live data refresh and updates
- 📱 **Responsive Design** - Works on all devices
- 🐳 **Docker Support** - Easy deployment with Docker

## Quick Start

### Option 1: Single Script (Recommended)

```bash
# Run the complete application
python scripts/run_app.py
```

### Option 2: Manual Setup

#### Backend Setup:

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
``` 

#### Frontend Setup:

``` bash
cd frontend
npm install
npm run dev
```
### Access the application:

Frontend: http://localhost:3000
Backend API: http://localhost:8000
API Docs: http://localhost:8000/api/docs

### Option 3: Docker Deployment
#### Copy environment file
```bash
cp .env.example .env
```

#### Start with Docker Compose
```bash
docker-compose up -d
```
#### Edit .env with your Calendly API key
Environment Variables
Create a .env file with:

#### env
        CALENDLY_API_KEY=your_calendly_api_key_here
        SECRET_KEY=your-secret-key-change-in-production

#### API Endpoints
        GET /health - Health check
        GET /api/v1/analytics/cleverly-introduction - Get analytics
        POST /api/v1/analytics/refresh-data - Refresh Calendly data
        GET /api/v1/analytics/data-preview - Data preview

### Architecture
Backend: FastAPI with async/await support
Frontend: React 18 + TypeScript + Vite
Charts: Recharts with custom themes
Styling: Tailwind CSS with glass morphism
Animations: Framer Motion
Data Processing: Pandas + NumPy + SciPy

### Production Deployment
#### Using Docker:
```bash
docker-compose -f docker-compose.prod.yml up -d
```
#### Using Cloud Providers:
The application is ready for deployment on:

        AWS ECS/EKS
        Google Cloud Run
        Azure Container Instances
        Heroku
        DigitalOcean App Platform

### Development

#### Backend development
```bash
cd backend
uvicorn app.main:app --reload
```
#### Frontend development  
```bash
cd frontend
npm run dev
```
#### Run tests
```bash
pytest tests/  # Backend
npm test       # Frontend
```

### Contributing

        Fork the repository
        Create a feature branch
        Make your changes
        Add tests
        Submit a pull request

### License
MIT License - see LICENSE file for details



## This application provides:

### 🎯 Key Features:
1. **Modern Tech Stack**: FastAPI + React 18 + TypeScript
2. **Beautiful UI**: Glass morphism, smooth animations, dark theme
3. **Advanced Charts**: Recharts with custom styling and interactions
4. **Real-time Analytics**: Live data processing and visualization
5. **Responsive Design**: Works perfectly on all devices
6. **Production Ready**: Docker, environment configs, health checks

### 🚀 Performance:
- Async/await throughout the backend
- Optimized React components with React Query
- Efficient data processing with Pandas
- Caching and background tasks

### 🛠️ Deployment:
- Single script runner for development
- Docker support for production
- Cloud-native architecture
- Environment-based configuration

### 📊 Analytics Capabilities:
- Comprehensive event analysis
- Internal note grouping and metrics
- Temporal pattern analysis
- Conversion rate tracking
- Custom question insights
- Correlation and trend analysis
