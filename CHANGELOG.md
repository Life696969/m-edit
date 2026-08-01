# Changelog

## 1.0.0-rc.1

- added direct source-media and instruction-file integrity checks
- added atomic state writes and project locking
- added approval receipts with exact user evidence
- added hash-locked Remotion render recipes
- added preview verification and final-to-preview SSIM checks
- added local transcription-provider adapters and canonical caption utilities
- hardened FFmpeg execution with local protocol restrictions and timeouts
- added safe instruction-discovery policy and symlink boundary checks
- added versioned, atomic manual installers with project scope and uninstallers
- added Claude plugin component declarations
- expanded generic content modes, caption guidance, threat model, quality bar, and documentation
- added CI, release packaging, trigger tests, security tests, and model-eval harness
- added a neutral, prop-driven Remotion starter with configurable dimensions, FPS, fitting, and caption styling
- added safe Remotion scaffolding without automatic dependency installation
- added canonical caption chunking using real word timestamps when available
- added standard WebVTT timestamp support
- blocked implicit Whisper model downloads unless local models or explicit network authorization are present
- added a complete generated-video state-machine integration test
- removed creator-specific denylist strings from the public repository; private release phrases are now supplied externally

## 0.1.0

- initial public beta with transcript, preview, final, and merge gates
