"""
video_player.py - Video Player Module for VHS Coffeeman

This module provides video playback functionality for the VHS Coffeeman system.
It handles playing themed video clips that correspond to RFID-tagged VHS tapes.

Classes:
    VideoPlayer: Manages video playback operations

The VideoPlayer class handles:
    - Loading and playing video files based on recipe/tag ID
    - Coordinating playback timing with drink dispensing
    - Managing video playback state and control
    - Error handling for missing or corrupted media files

Usage:
    from media.video_player import VideoPlayer
    
    player = VideoPlayer()
    player.play_video_for_tag("tag_123")
    player.stop_video()
"""

import os
import subprocess
import threading
import time
import random
from typing import Optional, Callable, Dict, Any, List
from utils.logger import get_logger

logger = get_logger(__name__)


class VideoPlayer:
    """Manages video playback for the VHS Coffeeman system."""
    
    def __init__(self, media_directory: str = "/home/pi/vhs_coffeeman_media"):
        """
        Initialize the video player.
        
        Args:
            media_directory: Directory containing video files
        """
        self.media_directory = media_directory
        self.current_process: Optional[subprocess.Popen] = None
        self.is_playing = False
        self.current_video_file: Optional[str] = None
        
        # Playback completion callback
        self.completion_callback: Optional[Callable[[], None]] = None
        
        # Monitoring thread
        self._monitor_thread: Optional[threading.Thread] = None
        self._monitoring = False
        
        logger.info(f"Video player initialized with media directory: {media_directory}")
        
        # Verify media directory exists
        if not os.path.exists(media_directory):
            logger.warning(f"Media directory does not exist: {media_directory}")
            try:
                os.makedirs(media_directory, exist_ok=True)
                logger.info(f"Created media directory: {media_directory}")
            except Exception as e:
                logger.error(f"Failed to create media directory: {e}")
    
    def set_completion_callback(self, callback: Callable[[], None]):
        """Set callback to be called when video playback completes."""
        self.completion_callback = callback
        logger.debug("Video completion callback set")
    
    def get_video_clips_for_movie(self, movie_name: str) -> List[str]:
        """
        Get all video clips for a given movie from its folder.
        
        Args:
            movie_name: The movie name (folder name)
            
        Returns:
            List[str]: List of video file paths, empty if none found
        """
        video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv']
        clips = []
        
        movie_folder = os.path.join(self.media_directory, movie_name)
        
        if not os.path.exists(movie_folder) or not os.path.isdir(movie_folder):
            logger.debug(f"Movie folder not found: {movie_folder}")
            return clips
        
        try:
            for filename in os.listdir(movie_folder):
                name, ext = os.path.splitext(filename)
                
                if ext.lower() in video_extensions:
                    full_path = os.path.join(movie_folder, filename)
                    if os.path.isfile(full_path):
                        clips.append(full_path)
            
            logger.debug(f"Found {len(clips)} clips for movie '{movie_name}'")
            
        except Exception as e:
            logger.error(f"Error listing clips for movie '{movie_name}': {e}")
        
        return clips

    def get_video_file_for_tag(self, tag_id: str) -> Optional[str]:
        """
        Get a random video file path for a given RFID tag ID.
        Looks for clips in a folder named after the movie.
        
        Args:
            tag_id: The RFID tag identifier (movie name)
            
        Returns:
            str: Path to randomly selected video file, or None if not found
        """
        # Primary: Get all clips for this movie folder
        clips = self.get_video_clips_for_movie(tag_id)
        
        if clips:
            # Randomly select one clip
            selected_clip = random.choice(clips)
            logger.info(f"Selected random clip for '{tag_id}': {os.path.basename(selected_clip)}")
            return selected_clip
        
        # Fallback: Check for a default video
        video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv']
        for ext in video_extensions:
            default_file = os.path.join(self.media_directory, f"default{ext}")
            if os.path.exists(default_file):
                logger.info(f"No clips found for '{tag_id}', using default video: {default_file}")
                return default_file
        
        logger.warning(f"No video file found for tag {tag_id} and no default video available")
        return None
    
    def play_video_for_tag(self, tag_id: str) -> bool:
        """
        Play video associated with the given RFID tag.
        
        Args:
            tag_id: The RFID tag identifier
            
        Returns:
            bool: True if playback started successfully, False otherwise
        """
        try:
            # Stop any current playback
            self.stop_video()
            
            # Find the video file
            video_file = self.get_video_file_for_tag(tag_id)
            if not video_file:
                logger.error(f"No video file available for tag: {tag_id}")
                return False
            
            logger.info(f"Starting video playback: {video_file}")
            
            # Try video players in order of preference: mpv -> VLC -> omxplayer
            
            # First try mpv (lightweight, modern)
            try:
                command = [
                    'mpv',
                    '--fullscreen',     # Fullscreen mode
                    '--no-osc',         # No on-screen controls
                    '--really-quiet',   # Minimal output
                    video_file
                ]
                
                self.current_process = subprocess.Popen(
                    command,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                logger.debug("Using mpv for video playback")
                
            except FileNotFoundError:
                # Fall back to VLC
                logger.info("mpv not found, trying VLC")
                try:
                    command = [
                        'vlc',
                        '--play-and-exit',  # Exit when done
                        '--fullscreen',     # Fullscreen mode
                        video_file
                    ]
                    
                    self.current_process = subprocess.Popen(
                        command,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    logger.debug("Using VLC for video playback")
                    
                except FileNotFoundError:
                    # Last resort: omxplayer (deprecated but might be available)
                    logger.info("VLC not found, trying omxplayer")
                    try:
                        command = [
                            'omxplayer',
                            '--no-osd',  # No on-screen display
                            '--aspect-mode', 'stretch',  # Stretch to fill screen
                            video_file
                        ]
                        
                        self.current_process = subprocess.Popen(
                            command,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                        logger.debug("Using omxplayer for video playback")
                        
                    except FileNotFoundError:
                        logger.error("No video player found (tried mpv, VLC, omxplayer)")
                        return False
            
            self.is_playing = True
            self.current_video_file = video_file
            
            # Start monitoring thread
            self._start_monitoring()
            
            logger.info(f"Video playback started successfully: {os.path.basename(video_file)}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting video playback: {e}")
            return False
    
    def stop_video(self):
        """Stop current video playback."""
        if self.current_process:
            try:
                logger.info("Stopping video playback")
                self.current_process.terminate()
                
                # Wait for process to terminate
                try:
                    self.current_process.wait(timeout=2.0)
                except subprocess.TimeoutExpired:
                    logger.warning("Video process did not terminate, killing")
                    self.current_process.kill()
                    self.current_process.wait()
                
                self.current_process = None
                
            except Exception as e:
                logger.error(f"Error stopping video: {e}")
        
        self.is_playing = False
        self.current_video_file = None
        self._stop_monitoring()
        
        logger.debug("Video playback stopped")
    
    def _start_monitoring(self):
        """Start monitoring video playback for completion."""
        if self._monitoring:
            return
            
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_playback, daemon=True)
        self._monitor_thread.start()
        logger.debug("Video monitoring started")
    
    def _stop_monitoring(self):
        """Stop monitoring video playback."""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
        logger.debug("Video monitoring stopped")
    
    def _monitor_playback(self):
        """Monitor video playback for completion (runs in separate thread)."""
        while self._monitoring and self.current_process:
            try:
                # Check if process is still running
                return_code = self.current_process.poll()
                
                if return_code is not None:
                    # Process has ended
                    logger.info("Video playback completed")
                    self.is_playing = False
                    self.current_video_file = None
                    self.current_process = None
                    
                    # Call completion callback
                    if self.completion_callback:
                        try:
                            self.completion_callback()
                        except Exception as e:
                            logger.error(f"Error in video completion callback: {e}")
                    
                    break
                
                # Brief delay before next check
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error monitoring video playback: {e}")
                break
        
        self._monitoring = False
    
    def is_video_playing(self) -> bool:
        """Check if video is currently playing."""
        return self.is_playing and self.current_process is not None
    
    def get_status(self) -> Dict[str, Any]:
        """Get current video player status."""
        return {
            "is_playing": self.is_playing,
            "current_file": os.path.basename(self.current_video_file) if self.current_video_file else None,
            "media_directory": self.media_directory,
            "process_active": self.current_process is not None
        }
    
    def list_available_videos(self) -> Dict[str, List[str]]:
        """
        List all available video files organized by movie folders.
        
        Returns:
            dict: Mapping of movie names to lists of video file paths
        """
        videos = {}
        
        if not os.path.exists(self.media_directory):
            return videos
        
        try:
            # First, scan for movie folders
            for item in os.listdir(self.media_directory):
                item_path = os.path.join(self.media_directory, item)
                
                if os.path.isdir(item_path):
                    # This is a movie folder
                    clips = self.get_video_clips_for_movie(item)
                    if clips:
                        videos[item] = clips
            
            # Also include direct video files (for backward compatibility)
            video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv']
            
            for filename in os.listdir(self.media_directory):
                name, ext = os.path.splitext(filename)
                
                if ext.lower() in video_extensions:
                    full_path = os.path.join(self.media_directory, filename)
                    if os.path.isfile(full_path):
                        if name not in videos:
                            videos[name] = []
                        videos[name].append(full_path)
            
            total_clips = sum(len(clips) for clips in videos.values())
            logger.debug(f"Found {len(videos)} movies with {total_clips} total clips")
            
        except Exception as e:
            logger.error(f"Error listing video files: {e}")
        
        return videos
    
    def cleanup(self):
        """Clean up video player resources."""
        logger.info("Cleaning up video player")
        
        # Stop any current playback
        self.stop_video()
        
        # Stop monitoring
        self._stop_monitoring()
        
        logger.info("Video player cleanup completed")