# Changelog — D-SIG Stress Test

## [S1-corrected] - 2026-03-31
### Fixed
- pipeline_dsig.py : cap score à 60 si dimension critique (internet/dns/hub) < 30
- pipeline_otel_dsig.py : même correction appliquée au pipeline hybride
