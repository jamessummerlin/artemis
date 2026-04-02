# Artemis II Mission Update Agent

This agent collects and summarizes scientific updates related to NASA's Artemis II mission.

## Purpose
Automatically gather the latest scientific and technical updates about Artemis II from authoritative sources and compile them into markdown reports.

## Priority Sources (in order)
1. NASA.gov — official Artemis program pages, press releases, blogs
2. NASA Technical Reports Server (NTRS)
3. arXiv preprints related to Artemis II science objectives
4. ESA and CSA (Canadian Space Agency) Artemis-related updates
5. Peer-reviewed journals (e.g., Space Science Reviews, Journal of Spacecraft and Rockets)
6. NASA Space Launch System (SLS) and Orion program updates

## Report Format
Each report is saved to `reports/` as `YYYY-MM-DD_HH.md` and follows the structure defined in `report_template.md`.

## Key Topics to Track
- Mission timeline, launch date, and schedule changes
- Crew updates (Reid Wiseman, Victor Glover, Christina Koch, Jeremy Hansen)
- SLS rocket and Orion spacecraft technical status
- Lunar flyby trajectory and mission profile
- Science instruments and experiments
- Ground systems and launch infrastructure
- Safety reviews and flight readiness
- Related Artemis program milestones (Gateway, Artemis III)
