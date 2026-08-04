# Dashboard Architecture Decisions (2026-07-28)

## Context
Adding an interactive web dashboard to business-rule-graph (roam-code based), inspired by understand-anything's dashboard but keeping roam's "100% local, zero deps" philosophy.

## Decisions

### Frontend: Single-file HTML+JS (not React/Vite)
- **Chosen**: Single HTML file + vis.js CDN, served by Python HTTP server
- **Rejected**: React/Vite app (like understand-anything) — needs Node.js, npm build, breaks roam's zero-dependency model
- **Trade-off**: Less feature-rich UI, but zero build step, zero external deps at runtime (vis.js loaded from CDN only when browser opens)

### Graph JSON schema: Roam's own format (not understand-anything compatible)
- **Chosen**: Custom schema matching roam's SQLite data model (symbol IDs, file paths, pagerank, complexity, health_score)
- **Rejected**: understand-anything's knowledge-graph.json schema — would require mapping roam's data model to a foreign schema
- **Implication**: Cannot use understand-anything's dashboard to visualize roam data (acceptable, since we built our own)

### Onboarding: Extend `roam tour` (not new command)
- **Chosen**: Add `--onboard` and `--write` flags to existing `roam tour` command
- **Rejected**: New `roam onboard` command — adds CLI surface area for marginal benefit
- **Status**: Planned, not yet implemented

### Non-code knowledge graph: Removed from scope
- **Rejected**: `roam knowledge scan` for markdown/wiki analysis
- **Reason**: User's focus is Java/Spring Boot code analysis; non-code is a different domain entirely
- **Status**: Scoped out

## Key Metrics
- API response: ~8MB for 2000 symbols + 2000 file nodes + edges (from 40K+ total symbols)
- Frontend caps: 500 nodes (symbol mode), 800 nodes (both mode)
- vis.js layout: forceAtlas2Based for force layout, hierarchical LR for tree view
