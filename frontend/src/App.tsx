import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

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

const API_BASE = 'http://localhost:8000';

function App() {
  const [activeTab, setActiveTab] = useState<'home' | 'compositions' | 'streaming' | 'processing'>('home');
  const [genres, setGenres] = useState<Genre[]>([]);
  const [compositions, setCompositions] = useState<Composition[]>([]);
  const [tracks, setTracks] = useState<Track[]>([]);
  const [loading, setLoading] = useState(false);

  // Fetch data based on active tab
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
