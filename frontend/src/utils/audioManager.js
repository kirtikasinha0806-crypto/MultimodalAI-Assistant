/**
 * Global Audio Manager (Singleton)
 * 
 * Features:
 * - Enforces single active audio stream (prevents overlapping voices)
 * - Automatically stops playback on conversation switch
 * - Provides seamless toggle (play/pause/resume)
 * - Subscribes components for reactive UI updates
 */
class AudioManager {
  constructor() {
    this.currentAudio = null;
    this.currentMessageId = null;
    this.listeners = new Set();
    this.isPlaying = false;
  }

  // Subscribe to playback changes: (currentMessageId, isPlaying) => void
  subscribe(listener) {
    this.listeners.add(listener);
    listener(this.currentMessageId, this.isPlaying);
    return () => this.listeners.delete(listener);
  }

  notify() {
    this.listeners.forEach((listener) => {
      try {
        listener(this.currentMessageId, this.isPlaying);
      } catch (e) {
        console.error('AudioManager listener error:', e);
      }
    });
  }

  // Completely stop any playing audio across the app and reset to beginning
  stop() {
    if (this.currentAudio) {
      try {
        this.currentAudio.pause();
        this.currentAudio.currentTime = 0;
        this.currentAudio.src = '';
      } catch (e) {
        // ignore error on reset
      }
      this.currentAudio = null;
    }

    if (typeof window !== 'undefined' && window.speechSynthesis) {
      try {
        window.speechSynthesis.cancel();
      } catch (e) {
        // ignore
      }
    }

    this.currentMessageId = null;
    this.isPlaying = false;
    this.notify();
  }

  // Play audio from the start for messageId, or stop if already playing
  async play(messageId, audioUrl) {
    // If clicking the same message that's currently playing: stop and reset to start
    if (this.currentMessageId === messageId && this.isPlaying) {
      this.stop();
      return;
    }

    // Stop ANY previously playing audio first (prevents overlap completely)
    this.stop();

    try {
      const audio = new Audio(audioUrl);
      audio.currentTime = 0; // Always start from the very beginning
      this.currentAudio = audio;
      this.currentMessageId = messageId;
      this.isPlaying = true;

      audio.onended = () => {
        if (this.currentAudio === audio) {
          this.currentMessageId = null;
          this.isPlaying = false;
          this.currentAudio = null;
          this.notify();
        }
      };

      audio.onerror = (e) => {
        console.error('Audio playback error:', e);
        if (this.currentAudio === audio) {
          this.stop();
        }
      };

      audio.onpause = () => {
        if (this.currentAudio === audio && this.isPlaying) {
          this.isPlaying = false;
          this.notify();
        }
      };

      await audio.play();
      this.notify();
    } catch (err) {
      console.error('Failed to start audio playback:', err);
      this.stop();
      throw err;
    }
  }

  isMessagePlaying(messageId) {
    return this.isPlaying && this.currentMessageId === messageId;
  }
}

export const audioManager = new AudioManager();
