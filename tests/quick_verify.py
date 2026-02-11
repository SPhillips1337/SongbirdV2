#!/usr/bin/env python3
"""Quick verification script for lyrics cleaning functionality"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.lyrics import LyricsAgent

def test_basic_filtering():
    """Test basic filtering of musical directions"""
    agent = LyricsAgent()
    
    test_lyrics = """[Intro]
(Guitar riff: crushing, driving)
(Snare drum hit)
[Verse 1]
I wake up in the night (oh yeah)
(Epic drums, crushing riffs)
[Chorus]
Breaking all the rules"""

    result = agent.strip_musical_directions(test_lyrics)
    
    # Check removals
    assert "(Guitar riff: crushing, driving)" not in result, "Failed to remove guitar riff"
    assert "(Snare drum hit)" not in result, "Failed to remove snare drum"
    assert "(Epic drums, crushing riffs)" not in result, "Failed to remove epic drums"
    
    # Check preservations
    assert "(oh yeah)" in result, "Incorrectly removed background vocal"
    assert "[Intro]" in result, "Incorrectly removed structural marker"
    assert "I wake up in the night" in result, "Incorrectly removed lyrics"
    
    print("✓ Basic filtering test passed")

def test_square_brackets():
    """Test filtering of square bracket instrumental markers"""
    agent = LyricsAgent()
    
    test_lyrics = """[Verse]
Singing my song
[Guitar distortion kicks in]
Still singing
[Chorus]
The chorus"""

    result = agent.strip_musical_directions(test_lyrics)
    
    assert "[Guitar distortion kicks in]" not in result, "Failed to remove square bracket instrumental"
    assert "[Verse]" in result, "Incorrectly removed valid marker"
    assert "[Chorus]" in result, "Incorrectly removed valid marker"
    
    print("✓ Square bracket filtering test passed")

def test_empty_parentheses():
    """Test removal of empty parentheses"""
    agent = LyricsAgent()
    
    test_lyrics = """[Verse]
Normal line
()
Another line"""

    result = agent.strip_musical_directions(test_lyrics)
    
    assert "()" not in result, "Failed to remove empty parentheses"
    assert "Normal line" in result, "Incorrectly removed normal line"
    
    print("✓ Empty parentheses test passed")

def test_normalize_end_to_end():
    """Test the full normalize_lyrics pipeline"""
    agent = LyricsAgent()
    
    test_lyrics = """[Intro]
(Guitar riff: crushing, driving)
[Verse 1]
I wake up in the night (oh yeah)
[Guitar distortion kicks in]
Breaking all the rules"""

    result = agent.normalize_lyrics(test_lyrics)
    
    # Should remove instrumental directions
    assert "(Guitar riff: crushing, driving)" not in result
    assert "[Guitar distortion kicks in]" not in result
    
    # Should preserve background vocals and structure
    assert "(oh yeah)" in result
    assert "[Intro]" in result
    assert "[Verse 1]" in result
    assert "Breaking all the rules" in result
    
    print("✓ End-to-end normalization test passed")

if __name__ == "__main__":
    try:
        test_basic_filtering()
        test_square_brackets()
        test_empty_parentheses()
        test_normalize_end_to_end()
        print("\n✅ All tests passed!")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
