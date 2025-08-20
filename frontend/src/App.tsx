import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

// Import new components
import { AuthProvider, useAuth, LoginForm, RegisterForm } from './components/Auth';
import AudioVisualizer from './components/AudioVisualizer';
import Audio3DVisualizer from './components/Audio3DVisualizer';

// Types
interface Genre {
  id: number;
  name: string;
  description: string;
}

interface Artist {
  id: number;
  name: string;
  bio: string;
}

interface Track {
  id: number;
  title: string;
  artist: Artist;
  duration_formatted: string;
  play_count: number;
  genre: string;
}

interface Composition {
  id: number;
  title: string;
  user: {
    username: string;
  };
  genre?: Genre;
  tempo: string;
  key_signature: string;
  duration: number;
  play_count: number;
  like_count: number;
}

interface AIModel {
  id: number;
  name: string;
  model_type: string;
  version: string;
  description: string;
  quality_score: number;
  is_premium: boolean;
}

const API_BASE = 'http://localhost:8000';

const MainApp: React.FC = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const [activeTab, setActiveTab] = useState<'home' | 'compositions' | 'streaming' | 'processing' | 'ai' | 'social'>('home');
  const [genres, setGenres] = useState<Genre[]>([]);
  const [compositions, setCompositions] = useState<Composition[]>([]);
  const [tracks, setTracks] = useState<Track[]>([]);
  const [aiModels, setAIModels] = useState<AIModel[]>([]);
  const [loading, setLoading] = useState(false);
  const [webSocket, setWebSocket] = useState<WebSocket | null>(null);
  const [audioData, setAudioData] = useState({
    frequencyData: Array.from({ length: 128 }, () => Math.random() * 255),
    amplitudeData: Array.from({ length: 256 }, () => Math.random() * 2 - 1),
    beatData: []
  });

  // Simulate real-time audio data updates
  useEffect(() => {
    const interval = setInterval(() => {
      setAudioData({
        frequencyData: Array.from({ length: 128 }, () => Math.random() * 255),
        amplitudeData: Array.from({ length: 256 }, () => Math.random() * 2 - 1),
        beatData: []
      });
    }, 100);

    return () => clearInterval(interval);
  }, []);

  // Fetch data based on active tab
  useEffect(() => {
    fetchData();
  }, [activeTab]);

  const fetchData = async () => {
    setLoading(true);
    try {
      switch (activeTab) {
        case 'compositions':
          await Promise.all([fetchGenres(), fetchCompositions()]);
          break;
        case 'streaming':
          await fetchTracks();
          break;
        case 'ai':
          await fetchAIModels();
          break;
        default:
          await Promise.all([fetchGenres(), fetchCompositions(), fetchTracks()]);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
    }
    setLoading(false);
  };

  const fetchGenres = async () => {
    try {
      const response = await axios.get(`${API_BASE}/composition/api/genres/`);
      setGenres(response.data.results || response.data);
    } catch (error) {
      console.error('Error fetching genres:', error);
    }
  };

  const fetchCompositions = async () => {
    try {
      const response = await axios.get(`${API_BASE}/composition/api/compositions/`);
      setCompositions(response.data.results || response.data);
    } catch (error) {
      console.error('Error fetching compositions:', error);
    }
  };

  const fetchTracks = async () => {
    try {
      const response = await axios.get(`${API_BASE}/streaming/api/tracks/`);
      setTracks(response.data.results || response.data);
    } catch (error) {
      console.error('Error fetching tracks:', error);
    }
  };

  const fetchAIModels = async () => {
    try {
      const response = await axios.get(`${API_BASE}/ai/api/models/`);
      setAIModels(response.data.results || response.data);
    } catch (error) {
      console.error('Error fetching AI models:', error);
    }
  };

  const generateComposition = async () => {
    if (!isAuthenticated) {
      alert('Please log in to generate compositions');
      return;
    }

    try {
      setLoading(true);
      const response = await axios.post(`${API_BASE}/ai/api/generate/`, {
        ai_model_id: aiModels[0]?.id || 1,
        title: 'AI Generated Composition',
        genre_id: genres[0]?.id || null,
        duration: 60,
        tempo: 120,
        creativity_level: 0.7
      });
      
      alert('Composition generation started! Check your requests for progress.');
      console.log('Generation response:', response.data);
    } catch (error) {
      console.error('Error generating composition:', error);
      alert('Failed to generate composition. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const connectWebSocket = () => {
    if (webSocket) {
      webSocket.close();
    }

    const ws = new WebSocket('ws://localhost:8000/ws/audio/processing/');
    
    ws.onopen = () => {
      console.log('WebSocket connected');
      setWebSocket(ws);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('WebSocket message:', data);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setWebSocket(null);
    };

  return (
    <div className="App">
      <header className="App-header">
        <div className="header-content">
          <h1>🎵 AI Music Platform</h1>
          
          {isAuthenticated ? (
            <div className="user-info">
              <span>Welcome, {user?.username}!</span>
              <button onClick={logout} className="logout-btn">Logout</button>
            </div>
          ) : null}
        </div>
        
        <nav className="App-nav">
          <button 
            className={activeTab === 'home' ? 'active' : ''} 
            onClick={() => setActiveTab('home')}
          >
            Home
          </button>
          <button 
            className={activeTab === 'compositions' ? 'active' : ''} 
            onClick={() => setActiveTab('compositions')}
          >
            AI Compositions
          </button>
          <button 
            className={activeTab === 'streaming' ? 'active' : ''} 
            onClick={() => setActiveTab('streaming')}
          >
            Music Streaming
          </button>
          <button 
            className={activeTab === 'processing' ? 'active' : ''} 
            onClick={() => setActiveTab('processing')}
          >
            Audio Processing
          </button>
          <button 
            className={activeTab === 'ai' ? 'active' : ''} 
            onClick={() => setActiveTab('ai')}
          >
            AI Models
          </button>
          <button 
            className={activeTab === 'social' ? 'active' : ''} 
            onClick={() => setActiveTab('social')}
          >
            Social
          </button>
        </nav>
      </header>

      <main className="App-main">
        {loading && <div className="loading">Loading...</div>}
        
        {activeTab === 'home' && (
          <div className="home-content">
            <h2>Welcome to the AI Music Platform</h2>
            <p>Experience the future of music creation with AI-powered composition tools.</p>
            
            <div className="features-grid">
              <div className="feature-card">
                <h3>🤖 AI Music Composition</h3>
                <p>Generate original music using advanced AI models with customizable parameters.</p>
                <button onClick={generateComposition}>Generate Sample Composition</button>
              </div>
              
              <div className="feature-card">
                <h3>🎵 Music Streaming</h3>
                <p>Browse and stream music with personalized recommendations.</p>
                <button onClick={() => setActiveTab('streaming')}>Explore Music</button>
              </div>
              
              <div className="feature-card">
                <h3>📊 Real-time Audio Processing</h3>
                <p>Connect to WebSocket for live audio analysis and visualization.</p>
                <button onClick={connectWebSocket}>Connect WebSocket</button>
              </div>
              
              <div className="feature-card">
                <h3>👥 Social Features</h3>
                <p>Collaborate with other musicians and share your creations.</p>
                <button onClick={() => setActiveTab('social')}>Join Community</button>
              </div>
            </div>

            {/* Audio Visualizations */}
            <div className="visualization-section">
              <h3>Audio Visualizations</h3>
              <AudioVisualizer 
                audioData={audioData}
                width={800}
                height={300}
                type="spectrum"
                colorScheme="fire"
                sensitivity={1.2}
              />
              
              <Audio3DVisualizer 
                audioData={audioData}
                width={800}
                height={400}
                visualizationType="wave3d"
              />
            </div>
          </div>
        )}

        {activeTab === 'compositions' && (
          <div className="compositions-content">
            <h2>AI Music Compositions</h2>
            
            <div className="section">
              <h3>Music Genres</h3>
              <div className="genres-list">
                {genres.map(genre => (
                  <span key={genre.id} className="genre-tag">
                    {genre.name}
                  </span>
                ))}
              </div>
            </div>

            <div className="section">
              <h3>Generated Compositions</h3>
              <div className="compositions-list">
                {compositions.map(composition => (
                  <div key={composition.id} className="composition-card">
                    <div className="composition-info">
                      <h4>{composition.title}</h4>
                      <p>by {composition.user.username}</p>
                      <div className="composition-details">
                        <span>{composition.genre?.name || 'Various'}</span>
                        <span>{composition.tempo}</span>
                        <span>{composition.key_signature}</span>
                        <span>{Math.floor(composition.duration / 60)}:{(composition.duration % 60).toString().padStart(2, '0')}</span>
                      </div>
                    </div>
                    <div className="composition-stats">
                      <span>▶ {composition.play_count}</span>
                      <span>♥ {composition.like_count}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'streaming' && (
          <div className="streaming-content">
            <h2>Music Streaming</h2>
            
            <div className="section">
              <h3>Available Tracks</h3>
              <div className="tracks-list">
                {tracks.map(track => (
                  <div key={track.id} className="track-card">
                    <div className="track-info">
                      <h4>{track.title}</h4>
                      <p>by {track.artist.name}</p>
                      <span className="track-genre">{track.genre}</span>
                    </div>
                    <div className="track-stats">
                      <span>{track.duration_formatted}</span>
                      <span>▶ {track.play_count}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'processing' && (
          <div className="processing-content">
            <h2>Real-time Audio Processing</h2>
            
            <div className="websocket-status">
              <p>WebSocket Status: {webSocket ? '🟢 Connected' : '🔴 Disconnected'}</p>
            </div>

            <div className="visualization-controls">
              <h3>Visualization Controls</h3>
              <div className="control-panel">
                <AudioVisualizer 
                  audioData={audioData}
                  width={800}
                  height={400}
                  type="circular"
                  colorScheme="ocean"
                  sensitivity={1.5}
                />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'ai' && (
          <div className="ai-content">
            <h2>AI Music Generation</h2>
            
            <div className="section">
              <h3>Available AI Models</h3>
              <div className="ai-models-list">
                {aiModels.map(model => (
                  <div key={model.id} className="ai-model-card">
                    <h4>{model.name} v{model.version}</h4>
                    <p>{model.description}</p>
                    <div className="model-details">
                      <span className="model-type">{model.model_type}</span>
                      <span className="quality-score">⭐ {model.quality_score}/10</span>
                      {model.is_premium && <span className="premium-badge">Premium</span>}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="generation-section">
              <h3>Generate New Composition</h3>
              <button onClick={generateComposition} className="generate-btn">
                Generate AI Composition
              </button>
            </div>
          </div>
        )}

        {activeTab === 'social' && (
          <div className="social-content">
            <h2>Social Features</h2>
            
            {!isAuthenticated ? (
              <div className="auth-required">
                <p>Please log in to access social features</p>
              </div>
            ) : (
              <div className="social-dashboard">
                <h3>Community Dashboard</h3>
                <p>Connect with other musicians, share compositions, and collaborate in real-time.</p>
                
                <div className="social-features">
                  <div className="feature-card">
                    <h4>👥 Follow Artists</h4>
                    <p>Discover and follow your favorite musicians</p>
                  </div>
                  
                  <div className="feature-card">
                    <h4>🎼 Share Compositions</h4>
                    <p>Share your AI-generated music with the community</p>
                  </div>
                  
                  <div className="feature-card">
                    <h4>🤝 Collaborate</h4>
                    <p>Work together on compositions in real-time</p>
                  </div>
                  
                  <div className="feature-card">
                    <h4>💬 Discuss</h4>
                    <p>Join discussions about music theory and composition</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
};

// Authentication wrapper component
const AuthenticationScreen: React.FC = () => {
  const [showRegister, setShowRegister] = useState(false);

  return (
    <div className="auth-screen">
      <div className="auth-container">
        <h1>🎵 AI Music Platform</h1>
        <p className="auth-subtitle">Create, collaborate, and discover AI-generated music</p>
        
        {showRegister ? (
          <>
            <RegisterForm onSuccess={() => setShowRegister(false)} />
            <p className="auth-switch">
              Already have an account?{' '}
              <button onClick={() => setShowRegister(false)}>Login here</button>
            </p>
          </>
        ) : (
          <>
            <LoginForm onSuccess={() => {}} />
            <p className="auth-switch">
              Don't have an account?{' '}
              <button onClick={() => setShowRegister(true)}>Register here</button>
            </p>
          </>
        )}
      </div>
    </div>
  );
};

// Main App component with authentication wrapper
const App: React.FC = () => {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
};

const AppContent: React.FC = () => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="app-loading">
        <div className="loading-spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  return isAuthenticated ? <MainApp /> : <AuthenticationScreen />;
};

export default App;
  useEffect(() => {
    setLoading(true);
    
    if (activeTab === 'compositions') {
      Promise.all([
        axios.get(`${API_BASE}/composition/api/genres/`),
        axios.get(`${API_BASE}/composition/api/compositions/`)
      ]).then(([genresRes, compositionsRes]) => {
        setGenres(genresRes.data);
        setCompositions(compositionsRes.data);
        setLoading(false);
      }).catch(err => {
        console.error('Error fetching composition data:', err);
        setLoading(false);
      });
    } else if (activeTab === 'streaming') {
      axios.get(`${API_BASE}/streaming/api/tracks/`).then(res => {
        setTracks(res.data);
        setLoading(false);
      }).catch(err => {
        console.error('Error fetching tracks:', err);
        setLoading(false);
      });
    } else {
      setLoading(false);
    }
  }, [activeTab]);

  const generateComposition = async () => {
    try {
      const response = await axios.post(`${API_BASE}/composition/api/compositions/generate/`, {
        genre: 'electronic',
        tempo: 'moderate',
        key: 'C',
        duration: 180,
        mood: 'energetic'
      });
      alert(`Generated composition: ${response.data.title}`);
      // Refresh compositions
      if (activeTab === 'compositions') {
        const compositionsRes = await axios.get(`${API_BASE}/composition/api/compositions/`);
        setCompositions(compositionsRes.data);
      }
    } catch (error) {
      alert('Error generating composition. Please ensure the Django server is running and authentication is set up.');
      console.error('Error:', error);
    }
  };

  const connectWebSocket = () => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//localhost:8000/ws/audio/processing/`;
    
    const socket = new WebSocket(wsUrl);
    
    socket.onopen = function(event) {
      console.log('WebSocket connected');
      alert('WebSocket connection established! Check browser console for real-time data.');
      
      socket.send(JSON.stringify({
        type: 'start_session',
        session_id: 'demo-session-' + Date.now(),
        processing_type: 'spectrum'
      }));
    };
    
    socket.onmessage = function(event) {
      const data = JSON.parse(event.data);
      console.log('Received real-time data:', data);
    };
    
    socket.onclose = function(event) {
      console.log('WebSocket closed');
    };
    
    socket.onerror = function(error) {
      console.error('WebSocket error:', error);
      alert('WebSocket connection failed. Make sure the Django server is running with ASGI support.');
    };
    
    // Close connection after 10 seconds for demo
    setTimeout(() => {
      socket.close();
      console.log('Demo WebSocket connection closed');
    }, 10000);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🎵 AI Music Platform</h1>
        <p>Modern React Frontend for AI-Powered Music Services</p>
        
        <nav className="nav-tabs">
          <button 
            className={activeTab === 'home' ? 'active' : ''} 
            onClick={() => setActiveTab('home')}
          >
            Home
          </button>
          <button 
            className={activeTab === 'compositions' ? 'active' : ''} 
            onClick={() => setActiveTab('compositions')}
          >
            AI Compositions
          </button>
          <button 
            className={activeTab === 'streaming' ? 'active' : ''} 
            onClick={() => setActiveTab('streaming')}
          >
            Music Streaming
          </button>
          <button 
            className={activeTab === 'processing' ? 'active' : ''} 
            onClick={() => setActiveTab('processing')}
          >
            Audio Processing
          </button>
        </nav>
      </header>

      <main className="App-main">
        {loading && <div className="loading">Loading...</div>}
        
        {activeTab === 'home' && (
          <div className="home-content">
            <h2>Welcome to the AI Music Platform</h2>
            <p>This React frontend demonstrates integration with our Django REST API backend.</p>
            
            <div className="features-grid">
              <div className="feature-card">
                <h3>🎼 AI Music Composition</h3>
                <p>Generate original music using AI models with customizable parameters.</p>
                <button onClick={generateComposition}>Generate Sample Composition</button>
              </div>
              
              <div className="feature-card">
                <h3>🎵 Music Streaming</h3>
                <p>Browse and stream music with personalized recommendations.</p>
                <button onClick={() => setActiveTab('streaming')}>Explore Music</button>
              </div>
              
              <div className="feature-card">
                <h3>📊 Real-time Audio Processing</h3>
                <p>Connect to WebSocket for live audio analysis and visualization.</p>
                <button onClick={connectWebSocket}>Connect WebSocket</button>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'compositions' && (
          <div className="compositions-content">
            <h2>AI Music Compositions</h2>
            
            <div className="section">
              <h3>Music Genres</h3>
              <div className="genres-list">
                {genres.map(genre => (
                  <span key={genre.id} className="genre-tag">
                    {genre.name}
                  </span>
                ))}
              </div>
            </div>

            <div className="section">
              <h3>Generated Compositions</h3>
              <div className="compositions-list">
                {compositions.map(comp => (
                  <div key={comp.id} className="composition-card">
                    <h4>{comp.title}</h4>
                    <p>By: {comp.user.username}</p>
                    <p>Genre: {comp.genre?.name || 'Unknown'}</p>
                    <p>Key: {comp.key_signature} | Tempo: {comp.tempo}</p>
                    <p>Duration: {Math.floor(comp.duration / 60)}:{(comp.duration % 60).toString().padStart(2, '0')}</p>
                    <div className="stats">
                      <span>👍 {comp.like_count}</span>
                      <span>▶️ {comp.play_count}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'streaming' && (
          <div className="streaming-content">
            <h2>Music Streaming</h2>
            
            <div className="tracks-list">
              {tracks.map(track => (
                <div key={track.id} className="track-card">
                  <h4>{track.title}</h4>
                  <p>By: {track.artist.name}</p>
                  <p>Genre: {track.genre} | Duration: {track.duration_formatted}</p>
                  <p>Plays: {track.play_count.toLocaleString()}</p>
                  <button className="play-btn">▶️ Play</button>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'processing' && (
          <div className="processing-content">
            <h2>Real-time Audio Processing</h2>
            
            <div className="processing-demo">
              <h3>WebSocket Audio Processing Demo</h3>
              <p>This section demonstrates real-time audio analysis capabilities.</p>
              
              <div className="demo-controls">
                <button onClick={connectWebSocket}>Start Real-time Session</button>
                <button onClick={() => alert('Audio upload simulation - file processing would happen here')}>
                  Upload Audio File
                </button>
              </div>
              
              <div className="visualization-placeholder">
                <p>🎵 Audio Visualization Area</p>
                <p>Real-time frequency spectrum, waveforms, and beat detection would be displayed here</p>
                <div className="mock-visualization">
                  <div className="bar" style={{height: '20px'}}></div>
                  <div className="bar" style={{height: '40px'}}></div>
                  <div className="bar" style={{height: '60px'}}></div>
                  <div className="bar" style={{height: '30px'}}></div>
                  <div className="bar" style={{height: '50px'}}></div>
                  <div className="bar" style={{height: '35px'}}></div>
                  <div className="bar" style={{height: '45px'}}></div>
                  <div className="bar" style={{height: '25px'}}></div>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      <footer className="App-footer">
        <p>AI Music Platform - Built with React + Django REST Framework</p>
      </footer>
    </div>
  );
}

export default App;
