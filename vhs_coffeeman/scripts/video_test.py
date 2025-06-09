#!/usr/bin/env python3
"""
Video Player Test Script for VHS Coffeeman

This script tests the video player functionality including:
- Player initialization
- Video file discovery
- Playback control
- Error handling

Usage:
    python scripts/video_test.py [--media-dir /path/to/media]
"""

import sys
import os
import time
import argparse

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from media.video_player import VideoPlayer
from utils.logger import get_logger

logger = get_logger(__name__)


def test_video_player_initialization(media_dir):
    """Test video player initialization."""
    print(f"\n=== Testing Video Player Initialization ===")
    
    try:
        player = VideoPlayer(media_directory=media_dir)
        print(f"✓ Video player initialized successfully")
        print(f"  Media directory: {player.media_directory}")
        return player
    except Exception as e:
        print(f"✗ Video player initialization failed: {e}")
        return None


def test_video_file_discovery(player):
    """Test video file discovery functionality."""
    print(f"\n=== Testing Video File Discovery ===")
    
    try:
        videos = player.list_available_videos()
        print(f"✓ Video discovery completed")
        print(f"  Found {len(videos)} video files:")
        
        for tag_id, file_path in videos.items():
            print(f"    {tag_id}: {os.path.basename(file_path)}")
        
        return videos
    except Exception as e:
        print(f"✗ Video discovery failed: {e}")
        return {}


def test_video_playback(player, tag_id="Money"):
    """Test video playback functionality."""
    print(f"\n=== Testing Video Playback ===")
    
    try:
        # Check if video file exists for tag
        video_file = player.get_video_file_for_tag(tag_id)
        if not video_file:
            print(f"✗ No video file found for tag: {tag_id}")
            return False
        
        print(f"  Video file for {tag_id}: {os.path.basename(video_file)}")
        
        # Start playback
        print(f"  Starting playback...")
        success = player.play_video_for_tag(tag_id)
        
        if success:
            print(f"✓ Video playback started successfully")
            
            # Check status
            status = player.get_status()
            print(f"  Player status: {status}")
            
            # Let it play for a few seconds
            print(f"  Playing for 5 seconds...")
            time.sleep(5)
            
            # Stop playback
            print(f"  Stopping playback...")
            player.stop_video()
            print(f"✓ Video playback stopped")
            
            return True
        else:
            print(f"✗ Video playback failed to start")
            return False
            
    except Exception as e:
        print(f"✗ Video playback test failed: {e}")
        return False


def test_error_handling(player):
    """Test error handling scenarios."""
    print(f"\n=== Testing Error Handling ===")
    
    try:
        # Test with non-existent tag
        print(f"  Testing with non-existent tag...")
        success = player.play_video_for_tag("nonexistent_tag")
        if not success:
            print(f"✓ Correctly handled non-existent tag")
        else:
            print(f"✗ Should have failed with non-existent tag")
        
        # Test stopping when nothing is playing
        print(f"  Testing stop when nothing playing...")
        player.stop_video()
        print(f"✓ Stop operation completed safely")
        
        return True
        
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        return False


def test_completion_callback(player):
    """Test video completion callback."""
    print(f"\n=== Testing Completion Callback ===")
    
    callback_called = False
    
    def completion_callback():
        nonlocal callback_called
        callback_called = True
        print(f"  ✓ Completion callback triggered")
    
    try:
        # Set callback
        player.set_completion_callback(completion_callback)
        print(f"  Completion callback set")
        
        # Note: For a full test, we'd need a very short video
        # For now, just verify the callback can be set
        print(f"✓ Completion callback functionality ready")
        
        return True
        
    except Exception as e:
        print(f"✗ Completion callback test failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Test VHS Coffeeman video player')
    parser.add_argument('--media-dir', 
                       default='/home/zack/VHS-Coffeeman/vhs_coffeeman/vhs_coffeeman/media',
                       help='Media directory path')
    
    args = parser.parse_args()
    
    print("VHS Coffeeman Video Player Test")
    print("=" * 40)
    
    # Test initialization
    player = test_video_player_initialization(args.media_dir)
    if not player:
        print("\n✗ Cannot continue without video player")
        sys.exit(1)
    
    # Test video discovery
    videos = test_video_file_discovery(player)
    
    # Test playback if videos are available
    if videos:
        # Use first available video for testing
        first_tag = list(videos.keys())[0]
        test_video_playback(player, first_tag)
    else:
        print("\n⚠ No videos available for playback testing")
    
    # Test error handling
    test_error_handling(player)
    
    # Test completion callback
    test_completion_callback(player)
    
    # Cleanup
    print(f"\n=== Cleanup ===")
    player.cleanup()
    print(f"✓ Video player cleanup completed")
    
    print(f"\n=== Video Player Test Complete ===")


if __name__ == "__main__":
    main()