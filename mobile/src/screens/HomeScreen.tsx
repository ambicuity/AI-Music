import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  Image,
  ActivityIndicator,
  Alert,
  RefreshControl,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { useAuth } from '../context/AuthContext';
import { useAudio } from '../context/AudioContext';
import { ApiService } from '../services/ApiService';

interface Composition {
  id: number;
  title: string;
  user: {
    username: string;
  };
  genre?: {
    name: string;
  };
  duration: number;
  tempo: number;
  key_signature: string;
  like_count: number;
  play_count: number;
  created_at: string;
  audio_file?: string;
}

interface RecentActivity {
  id: number;
  user: {
    username: string;
  };
  activity_type: string;
  created_at: string;
  metadata: any;
}

const HomeScreen: React.FC = () => {
  const { user, token } = useAuth();
  const { playTrack, currentTrack, isPlaying } = useAudio();
  
  const [compositions, setCompositions] = useState<Composition[]>([]);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadHomeData();
  }, []);

  const loadHomeData = async () => {
    try {
      setLoading(true);
      
      // Load recent compositions
      const compositionsData = await ApiService.getCompositions(token || undefined);
      setCompositions(compositionsData.slice(0, 10)); // Latest 10

      // Load recommendations if authenticated
      if (token) {
        try {
          const recommendationsData = await ApiService.getRecommendations(token);
          setRecommendations(recommendationsData.slice(0, 5));
          
          const activityData = await ApiService.getUserFeed(token);
          setRecentActivity(activityData.slice(0, 8));
        } catch (error) {
          console.error('Error loading personalized data:', error);
        }
      } else {
        // Load trending tracks for non-authenticated users
        const trendingData = await ApiService.getTrendingTracks();
        setRecommendations(trendingData.slice(0, 5));
      }

    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadHomeData();
    setRefreshing(false);
  };

  const handlePlayComposition = async (composition: Composition) => {
    try {
      if (composition.audio_file) {
        const track = {
          id: composition.id.toString(),
          url: composition.audio_file,
          title: composition.title,
          artist: composition.user.username,
          artwork: undefined, // Could add artwork URL
          duration: composition.duration,
        };
        
        await playTrack(track);
        
        // Record play
        if (token) {
          await ApiService.playTrack(composition.id, token);
        }
      } else {
        Alert.alert('Audio Not Available', 'This composition does not have an audio file yet.');
      }
    } catch (error: any) {
      Alert.alert('Playback Error', error.message || 'Failed to play composition');
    }
  };

  const handleLikeComposition = async (compositionId: number) => {
    if (!token) {
      Alert.alert('Authentication Required', 'Please log in to like compositions.');
      return;
    }

    try {
      await ApiService.likeComposition(compositionId, token);
      // Update local state
      setCompositions(prev =>
        prev.map(comp =>
          comp.id === compositionId
            ? { ...comp, like_count: comp.like_count + 1 }
            : comp
        )
      );
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to like composition');
    }
  };

  const formatDuration = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const renderCompositionCard = (composition: Composition) => (
    <View key={composition.id} style={styles.compositionCard}>
      <View style={styles.cardHeader}>
        <View style={styles.compositionInfo}>
          <Text style={styles.compositionTitle}>{composition.title}</Text>
          <Text style={styles.compositionArtist}>by {composition.user.username}</Text>
          <Text style={styles.compositionDetails}>
            {composition.genre?.name} • {composition.key_signature} • {composition.tempo} BPM
          </Text>
        </View>
        <TouchableOpacity
          style={styles.playButton}
          onPress={() => handlePlayComposition(composition)}
        >
          <Icon
            name={currentTrack?.id === composition.id.toString() && isPlaying ? "pause" : "play-arrow"}
            size={24}
            color="#4a9eff"
          />
        </TouchableOpacity>
      </View>
      
      <View style={styles.cardFooter}>
        <TouchableOpacity
          style={styles.actionButton}
          onPress={() => handleLikeComposition(composition.id)}
        >
          <Icon name="favorite-border" size={18} color="#666" />
          <Text style={styles.actionText}>{composition.like_count}</Text>
        </TouchableOpacity>
        
        <Text style={styles.actionText}>
          {composition.play_count} plays
        </Text>
        
        <Text style={styles.actionText}>
          {formatDuration(composition.duration)}
        </Text>
      </View>
    </View>
  );

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#4a9eff" />
        <Text style={styles.loadingText}>Loading...</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      {/* Welcome Section */}
      <View style={styles.welcomeSection}>
        <Text style={styles.welcomeText}>
          {user ? `Welcome back, ${user.username}!` : 'Welcome to AI Music'}
        </Text>
        <Text style={styles.welcomeSubtext}>
          Discover AI-generated music and create your own compositions
        </Text>
      </View>

      {/* Recommendations Section */}
      {recommendations.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>
            {token ? 'Recommended for You' : 'Trending Now'}
          </Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            {recommendations.map((item, index) => (
              <TouchableOpacity key={index} style={styles.recommendationCard}>
                <View style={styles.recommendationImage}>
                  <Icon name="music-note" size={40} color="#4a9eff" />
                </View>
                <Text style={styles.recommendationTitle} numberOfLines={2}>
                  {item.title}
                </Text>
                <Text style={styles.recommendationArtist}>
                  {item.artist || item.user?.username}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>
      )}

      {/* Recent Compositions */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Latest Compositions</Text>
          <TouchableOpacity>
            <Text style={styles.seeAllText}>See All</Text>
          </TouchableOpacity>
        </View>
        
        {compositions.map(renderCompositionCard)}
      </View>

      {/* Recent Activity */}
      {user && recentActivity.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Recent Activity</Text>
          {recentActivity.map((activity) => (
            <View key={activity.id} style={styles.activityItem}>
              <Icon name="person" size={20} color="#666" />
              <Text style={styles.activityText}>
                {activity.user.username} {activity.activity_type.replace('_', ' ')}
              </Text>
            </View>
          ))}
        </View>
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0a0a0a',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#0a0a0a',
  },
  loadingText: {
    color: '#fff',
    marginTop: 10,
    fontSize: 16,
  },
  welcomeSection: {
    padding: 20,
    paddingTop: 30,
  },
  welcomeText: {
    color: '#fff',
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  welcomeSubtext: {
    color: '#888',
    fontSize: 16,
  },
  section: {
    marginBottom: 30,
    paddingHorizontal: 20,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 15,
  },
  sectionTitle: {
    color: '#fff',
    fontSize: 20,
    fontWeight: 'bold',
  },
  seeAllText: {
    color: '#4a9eff',
    fontSize: 14,
  },
  recommendationCard: {
    width: 120,
    marginRight: 15,
    alignItems: 'center',
  },
  recommendationImage: {
    width: 100,
    height: 100,
    backgroundColor: '#1a1a1a',
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  recommendationTitle: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '500',
    textAlign: 'center',
    marginBottom: 4,
  },
  recommendationArtist: {
    color: '#888',
    fontSize: 12,
    textAlign: 'center',
  },
  compositionCard: {
    backgroundColor: '#1a1a1a',
    borderRadius: 12,
    padding: 15,
    marginBottom: 15,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  compositionInfo: {
    flex: 1,
  },
  compositionTitle: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  compositionArtist: {
    color: '#4a9eff',
    fontSize: 14,
    marginBottom: 2,
  },
  compositionDetails: {
    color: '#888',
    fontSize: 12,
  },
  playButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#2a2a2a',
    justifyContent: 'center',
    alignItems: 'center',
  },
  cardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  actionText: {
    color: '#666',
    fontSize: 12,
    marginLeft: 4,
  },
  activityItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
  },
  activityText: {
    color: '#ccc',
    fontSize: 14,
    marginLeft: 10,
  },
});

export default HomeScreen;