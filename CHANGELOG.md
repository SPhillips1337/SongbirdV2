# Changelog

All notable changes to the Songbird project will be documented in this file.

## [2.1.0] - 2026-02-17

### Added
- **Centralized Band Manager**: Persistent virtual bands stored in `Output/Bands/` with complete discography tracking
  - Band profiles include master seed, biography, visual style, and creation date
  - Automatic discography updates after album generation
  - Profile snapshots saved to album directories
- **Suggestion Engine**: AI-powered song idea generator based on user history (`--suggest`)
- **Trending Intelligence**: Real-time trend injection via Perplexity API (`--trending`)
- **Poetry Mode**: Elevated lyricism with concrete imagery and structural tension (`--poetic`)
- **Smart Caching**: Local JSON cache for Perplexity API responses to reduce costs
- **Artist Variety**: Random artist selection from genre-specific lists when not specified

### Changed
- Refactored `tools/band.py` with new centralized architecture
- Updated `app.py` to support band creation, loading, and discography management
- Simplified agent implementations for better maintainability

### Fixed
- Band profile persistence across multiple album generations
- Consistent artist persona and seed enforcement for bands

### Tests
- Added `tests/test_band_manager.py` with 5 comprehensive tests
- All existing tests updated and passing (10/10)

## [2.0.0] - 2026-02-06

### Added
- Initial LangGraph-based implementation
- Multi-agent orchestration (Artist, Music, Lyrics)
- ComfyUI integration for audio generation
- Album mode with thematic consistency
- Vocal control options
- LightRAG integration for research
