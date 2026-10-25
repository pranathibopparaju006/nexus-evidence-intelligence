# NEXUS Entity Extraction Fix

This version fixes the human-readable analysis output.

## Changes

- Filters document headings and generic metadata from entity extraction.
- Classifies extracted entities as Person, Organization, Location, or System.
- Detects multi-word locations such as hubs, campuses, facilities, centers, rooms and annexes.
- Detects technical systems such as Core, Flow, Registry, Monitor, Link and Mesh names.
- Keeps the Neo4j graph and Narrative DNA extraction rules consistent.
- Updates the Overview and Narrative screens to display entity names correctly.
- Prevents object values from rendering as `[object Object]`.
- Fixes the `CircleHelp` frontend icon error by using `HelpCircle`.
- Re-running analysis replaces the project's old findings with the current analysis results.

The extraction remains evidence-based and does not invent entities that are not present in the source text.
