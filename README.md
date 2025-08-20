# AI Music Platform

A comprehensive AI-powered music platform built with Django REST Framework backend and React TypeScript frontend. This project demonstrates scalable architecture, modern web technologies, and AI-powered music capabilities.

## 🎵 Platform Overview

The AI Music Platform consists of three core services:

1. **AI Music Composition Tool** - Generate original music using simulated AI models
2. **Music Streaming & Discovery Platform** - Stream music with personalized recommendations  
3. **Real-time Audio Processing Service** - Process and visualize audio data in real-time

## 🚀 Features

### Backend (Django REST Framework)
- **RESTful API** with comprehensive endpoints for all services
- **Real-time WebSocket** support for audio processing
- **Dual Database Design** - SQL (SQLite/PostgreSQL) + NoSQL simulation with Redis/cache
- **Scalable Architecture** designed for high-volume traffic
- **AI Model Integration** with simulated music generation algorithms
- **Advanced Audio Processing** with spectrum analysis, beat detection, and mood analysis

### Frontend (React TypeScript)
- **Modern React** with TypeScript for type safety
- **Responsive Design** with mobile-first approach
- **Real-time Features** via WebSocket connections
- **Interactive UI** for music creation, streaming, and visualization
- **Component-Based Architecture** for maintainability

### Key Technical Capabilities
- ⚡ **High Performance** - Designed to handle massive consumer traffic
- 📈 **Scalable** - Modern framework architecture with database indexing
- 🔍 **Observable** - Comprehensive logging and error handling
- 🤖 **AI-Powered** - Simulated AI models for music composition
- 💾 **Multi-Database** - SQL for structured data, NoSQL patterns for real-time data
- 🔄 **Real-time** - WebSocket support for live audio processing

## 📋 Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn

## 🛠️ Installation & Setup

### Backend Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd AI-Music
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run database migrations**:
   ```bash
   python manage.py migrate
   ```

4. **Create a superuser** (optional):
   ```bash
   python manage.py createsuperuser
   ```

5. **Populate sample data**:
   ```bash
   python manage.py populate_compositions
   python manage.py populate_streaming
   ```

6. **Start the Django server**:
   ```bash
   python manage.py runserver
   ```

The backend will be available at `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Start the React development server**:
   ```bash
   npm start
   ```

The frontend will be available at `http://localhost:3000`

## 📚 API Documentation

### Base URLs
- Backend API: `http://localhost:8000/api/`
- Composition API: `http://localhost:8000/composition/api/`
- Streaming API: `http://localhost:8000/streaming/api/`
- Audio Processing API: `http://localhost:8000/audio-processing/api/`

### Key Endpoints

#### Composition Service
- `GET /composition/api/genres/` - List music genres
- `GET /composition/api/compositions/` - List AI compositions
- `POST /composition/api/compositions/generate/` - Generate new composition
- `POST /composition/api/compositions/{id}/like/` - Like/unlike composition
- `POST /composition/api/compositions/{id}/play/` - Record play event

#### Streaming Service
- `GET /streaming/api/artists/` - List artists
- `GET /streaming/api/tracks/` - List tracks with filtering
- `GET /streaming/api/playlists/` - List playlists
- `POST /streaming/api/tracks/{id}/play/` - Stream track
- `GET /streaming/api/tracks/recommendations/` - Get recommendations
- `GET /streaming/api/tracks/trending/` - Get trending tracks

#### Audio Processing Service
- `GET /audio-processing/api/jobs/` - List processing jobs
- `POST /audio-processing/api/jobs/` - Create processing job
- `GET /audio-processing/api/features/` - List audio features
- `GET /audio-processing/api/sessions/` - List real-time sessions
- `WebSocket /ws/audio/processing/` - Real-time audio processing

### WebSocket API

Connect to `ws://localhost:8000/ws/audio/processing/` for real-time audio processing:

```javascript
const socket = new WebSocket('ws://localhost:8000/ws/audio/processing/');

// Start processing session
socket.send(JSON.stringify({
    type: 'start_session',
    session_id: 'unique-session-id',
    processing_type: 'spectrum'
}));

// Send audio data
socket.send(JSON.stringify({
    type: 'audio_data',
    audio_data: 'base64-encoded-audio',
    config: { sensitivity: 1.0 }
}));
```

## 🏗️ Architecture

### Backend Architecture
```
ai_music_platform/
├── composition/          # AI music composition service
├── streaming/           # Music streaming service  
├── audio_processing/    # Real-time audio processing
├── ai_music_platform/   # Main Django project
└── templates/          # HTML templates
```

### Database Design
- **SQL Database**: User management, music metadata, compositions, playlists
- **Caching Layer**: Session data, real-time processing state
- **File Storage**: Audio files, images (configurable for cloud storage)

### Frontend Architecture
```
frontend/
├── src/
│   ├── App.tsx         # Main application component
│   ├── App.css         # Application styles
│   └── components/     # Reusable components (extensible)
├── public/             # Static assets
└── package.json        # Dependencies
```

## 🔧 Configuration

### Django Settings
Key configuration in `ai_music_platform/settings.py`:

- **CORS Settings** - Configured for React frontend
- **REST Framework** - API configuration
- **WebSocket Support** - Channels configuration
- **Database** - SQLite for development, PostgreSQL for production
- **Media Storage** - Local storage (configurable for AWS S3/CloudFront)

### Environment Variables
Create `.env` file for production:
```env
DEBUG=False
SECRET_KEY=your-secret-key
DATABASE_URL=postgres://user:pass@host:port/dbname
REDIS_URL=redis://host:port/db
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_STORAGE_BUCKET_NAME=your-bucket
```

## 📊 Performance & Scalability

### Database Optimization
- **Indexed Fields** - Artist, genre, play_count, created_at
- **Query Optimization** - select_related, prefetch_related
- **Pagination** - Built-in API pagination support

### Caching Strategy
- **API Response Caching** - Redis for frequently accessed data
- **Session Storage** - WebSocket session management
- **Static Files** - CDN-ready configuration

### Load Handling
- **Asynchronous Processing** - Background jobs for AI generation
- **WebSocket Scaling** - Channels with Redis backend
- **Database Scaling** - Read replicas, connection pooling

## 🧪 Testing

### Backend Tests
```bash
python manage.py test
```

### Frontend Tests  
```bash
cd frontend
npm test
```

## 🚀 Deployment

### Production Deployment

1. **Environment Setup**:
   ```bash
   pip install gunicorn
   npm run build  # Build React frontend
   ```

2. **Database Migration**:
   ```bash
   python manage.py migrate --settings=ai_music_platform.settings_production
   ```

3. **Static Files**:
   ```bash
   python manage.py collectstatic
   ```

4. **Run with Gunicorn**:
   ```bash
   gunicorn ai_music_platform.wsgi:application
   ```

### Docker Deployment
```dockerfile
# Dockerfile example structure
FROM python:3.9
# ... backend setup
FROM node:16
# ... frontend build
# ... nginx configuration
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙋‍♀️ Support

For questions and support:
- Create an issue in the repository
- Check the API documentation at `/api/`
- Review the Django admin interface at `/admin/`

## 🎯 Future Enhancements

- [ ] Machine Learning integration for real AI music generation
- [ ] Advanced audio visualization with D3.js/Three.js
- [ ] User authentication and authorization
- [ ] Social features (sharing, collaboration)
- [ ] Mobile app with React Native
- [ ] Advanced recommendation algorithms
- [ ] Real-time collaborative composition
- [ ] Music theory analysis and suggestions
- [ ] Integration with external music services (Spotify, Apple Music)
- [ ] Advanced audio effects and processing

---

*Built with ❤️ using Django REST Framework and React TypeScript*