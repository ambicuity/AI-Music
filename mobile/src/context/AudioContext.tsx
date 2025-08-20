import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import TrackPlayer, { 
  State, 
  Track, 
  Event, 
  useTrackPlayerEvents,
  useProgress,
  RepeatMode 
} from 'react-native-track-player';

interface AudioContextType {
  currentTrack: Track | null;
  isPlaying: boolean;
  progress: {
    position: number;
    buffered: number;
    duration: number;
  };
  playlist: Track[];
  playTrack: (track: Track) => Promise<void>;
  pauseTrack: () => Promise<void>;
  resumeTrack: () => Promise<void>;
  stopTrack: () => Promise<void>;
  skipToNext: () => Promise<void>;
  skipToPrevious: () => Promise<void>;
  seekTo: (position: number) => Promise<void>;
  setPlaylist: (tracks: Track[]) => Promise<void>;
  addToPlaylist: (track: Track) => Promise<void>;
  toggleShuffle: () => Promise<void>;
  toggleRepeat: () => Promise<void>;
  shuffle: boolean;
  repeatMode: RepeatMode;
}

const AudioContext = createContext<AudioContextType | undefined>(undefined);

export const AudioProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [currentTrack, setCurrentTrack] = useState<Track | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playlist, setPlaylistState] = useState<Track[]>([]);
  const [shuffle, setShuffle] = useState(false);
  const [repeatMode, setRepeatModeState] = useState<RepeatMode>(RepeatMode.Off);
  
  const progress = useProgress();

  // Initialize TrackPlayer
  useEffect(() => {
    const setupTrackPlayer = async () => {
      try {
        await TrackPlayer.setupPlayer();
        await TrackPlayer.updateOptions({
          stopWithApp: true,
          capabilities: [
            TrackPlayer.CAPABILITY_PLAY,
            TrackPlayer.CAPABILITY_PAUSE,
            TrackPlayer.CAPABILITY_SKIP_TO_NEXT,
            TrackPlayer.CAPABILITY_SKIP_TO_PREVIOUS,
            TrackPlayer.CAPABILITY_STOP,
            TrackPlayer.CAPABILITY_SEEK_TO,
          ],
          compactCapabilities: [
            TrackPlayer.CAPABILITY_PLAY,
            TrackPlayer.CAPABILITY_PAUSE,
            TrackPlayer.CAPABILITY_SKIP_TO_NEXT,
          ],
        });
      } catch (error) {
        console.error('Error setting up TrackPlayer:', error);
      }
    };

    setupTrackPlayer();
  }, []);

  // Track player event listeners
  useTrackPlayerEvents([Event.PlaybackState], async (event) => {
    if (event.state === State.Playing) {
      setIsPlaying(true);
    } else {
      setIsPlaying(false);
    }
  });

  useTrackPlayerEvents([Event.PlaybackTrackChanged], async (event) => {
    if (event.nextTrack !== undefined) {
      const track = await TrackPlayer.getTrack(event.nextTrack);
      setCurrentTrack(track);
    }
  });

  const playTrack = async (track: Track): Promise<void> => {
    try {
      await TrackPlayer.reset();
      await TrackPlayer.add(track);
      await TrackPlayer.play();
      setCurrentTrack(track);
    } catch (error) {
      console.error('Error playing track:', error);
    }
  };

  const pauseTrack = async (): Promise<void> => {
    try {
      await TrackPlayer.pause();
    } catch (error) {
      console.error('Error pausing track:', error);
    }
  };

  const resumeTrack = async (): Promise<void> => {
    try {
      await TrackPlayer.play();
    } catch (error) {
      console.error('Error resuming track:', error);
    }
  };

  const stopTrack = async (): Promise<void> => {
    try {
      await TrackPlayer.stop();
      setCurrentTrack(null);
    } catch (error) {
      console.error('Error stopping track:', error);
    }
  };

  const skipToNext = async (): Promise<void> => {
    try {
      await TrackPlayer.skipToNext();
    } catch (error) {
      console.error('Error skipping to next:', error);
    }
  };

  const skipToPrevious = async (): Promise<void> => {
    try {
      await TrackPlayer.skipToPrevious();
    } catch (error) {
      console.error('Error skipping to previous:', error);
    }
  };

  const seekTo = async (position: number): Promise<void> => {
    try {
      await TrackPlayer.seekTo(position);
    } catch (error) {
      console.error('Error seeking:', error);
    }
  };

  const setPlaylist = async (tracks: Track[]): Promise<void> => {
    try {
      await TrackPlayer.reset();
      await TrackPlayer.add(tracks);
      setPlaylistState(tracks);
      
      if (tracks.length > 0) {
        setCurrentTrack(tracks[0]);
      }
    } catch (error) {
      console.error('Error setting playlist:', error);
    }
  };

  const addToPlaylist = async (track: Track): Promise<void> => {
    try {
      await TrackPlayer.add(track);
      setPlaylistState(prev => [...prev, track]);
    } catch (error) {
      console.error('Error adding to playlist:', error);
    }
  };

  const toggleShuffle = async (): Promise<void> => {
    try {
      const newShuffleState = !shuffle;
      setShuffle(newShuffleState);
      // Note: react-native-track-player doesn't have built-in shuffle
      // You would need to implement custom shuffle logic
    } catch (error) {
      console.error('Error toggling shuffle:', error);
    }
  };

  const toggleRepeat = async (): Promise<void> => {
    try {
      let newRepeatMode: RepeatMode;
      switch (repeatMode) {
        case RepeatMode.Off:
          newRepeatMode = RepeatMode.Track;
          break;
        case RepeatMode.Track:
          newRepeatMode = RepeatMode.Queue;
          break;
        case RepeatMode.Queue:
          newRepeatMode = RepeatMode.Off;
          break;
        default:
          newRepeatMode = RepeatMode.Off;
      }
      
      await TrackPlayer.setRepeatMode(newRepeatMode);
      setRepeatModeState(newRepeatMode);
    } catch (error) {
      console.error('Error toggling repeat:', error);
    }
  };

  const value: AudioContextType = {
    currentTrack,
    isPlaying,
    progress,
    playlist,
    playTrack,
    pauseTrack,
    resumeTrack,
    stopTrack,
    skipToNext,
    skipToPrevious,
    seekTo,
    setPlaylist,
    addToPlaylist,
    toggleShuffle,
    toggleRepeat,
    shuffle,
    repeatMode,
  };

  return (
    <AudioContext.Provider value={value}>
      {children}
    </AudioContext.Provider>
  );
};

export const useAudio = (): AudioContextType => {
  const context = useContext(AudioContext);
  if (context === undefined) {
    throw new Error('useAudio must be used within an AudioProvider');
  }
  return context;
};