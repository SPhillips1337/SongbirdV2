# Changelog

All notable changes to the Songbird project will be documented in this file.

## [2.1.0] - 2026-02-17

### Added
- **Suggestion Engine**: New `--suggest` flag uses GraphRAG (LightRAG) to analyze user history and propose personalized song ideas.
- **Trending Intelligence**: New `--trending` flag integrates real-time data from Perplexity API into the creative process.
- **Agent Specialization**: Refactored `ArtistAgent`, `MusicAgent`, and `LyricsAgent` to have distinct research responsibilities (Persona, Technical, Theme).
- **Poetry Mode**: New `--poetic` flag enables a high-level lyric generation mode based on Hollis Robbins' principles, focusing on concrete imagery and structural tension.
- **Virtual Band Persistence**: New `--band` flag allows loading a `band_profile.json` to re-use an artist's persona, seed, and visual style across multiple albums.
- **Smart Caching**: Implemented a local JSON cache for Perplexity and LightRAG API calls to reduce costs and latency.
- **Artist Variety**: Automated random selection of reference artists from `genres.json` when no specific artist is provided.

### Changed
- Refactored `app.py` workflow nodes to support specialized research steps.
- Updated `state.py` to include `artist_research`, `music_research`, and `lyrics_research` fields.
- Updated `AGENTS.md` to reflect the new specialized roles of each agent.

### Fixed
- Addressed potential duplicate key errors in state initialization.
