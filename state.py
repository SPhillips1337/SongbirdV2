from typing import TypedDict, List, Optional

class SongState(TypedDict):
    genre: str
    user_direction: str
    artist_name: Optional[str]
    artist_background: Optional[str]
    artist_style: Optional[str]
    seed: Optional[int]
    musical_direction: Optional[dict]
    lyrics: Optional[str]
    cleaned_lyrics: Optional[str]
    audio_path: Optional[str]
    research_notes: Optional[str]
    history: List[dict]
    song_title: Optional[str]
    album_name: Optional[str]
    track_number: Optional[int]
    vocals: Optional[str]
    vocal_strength: Optional[float]
    key: Optional[str]
