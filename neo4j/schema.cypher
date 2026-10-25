// Create constraints and indexes
CREATE CONSTRAINT entity_id IF NOT EXISTS
FOR (e:Entity) REQUIRE e.id IS UNIQUE;

CREATE CONSTRAINT content_id IF NOT EXISTS
FOR (c:Content) REQUIRE c.id IS UNIQUE;

CREATE INDEX entity_type_idx IF NOT EXISTS
FOR (e:Entity) ON (e.type);

CREATE INDEX content_timestamp_idx IF NOT EXISTS
FOR (c:Content) ON (c.timestamp);

// Node types:
// :Entity (Person, Organization, Location, Event)
// :Content (Post, Article, Comment, Image)
// :Cluster (Detected coordination cluster)
// :Narrative (Identified narrative)

// Relationship types:
// POSTED_BEFORE, SIMILAR_TO, MENTIONS, MUTATES, 
// AMPLIFIES, CO_OCCURS_WITH, PART_OF
