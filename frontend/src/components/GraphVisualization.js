
import React, { useEffect, useState } from 'react';
import { useQuery } from 'react-query';
import ReactFlow, {
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
} from 'react-flow-renderer';
import {
  Network,
  X,
  Info,
  GitBranch,
  Search,
} from 'lucide-react';
import api from '../services/api';

const colors = {
  Entity: '#8174ff',
  Content: '#22b894',
  Cluster: '#e7a83e',
  Narrative: '#e879b9',
  Person: '#a78bfa',
  Organization: '#38bdf8',
  Location: '#34d399',
  System: '#f59e0b',
};

const GraphVisualization = ({ projectId }) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selected, setSelected] = useState(null);
  const [search, setSearch] = useState('');

  const { data, isLoading, isError, refetch } = useQuery(
    ['graph', projectId],
    () =>
      api.get(`/projects/${projectId}/graph`).then((res) => res.data)
  );

  useEffect(() => {
    if (!data) return;

    const rawNodes = Array.isArray(data.nodes) ? data.nodes : [];
    const limited = rawNodes.slice(0, 80);
    const visibleIds = new Set(limited.map((node) => String(node.id)));

    const formattedNodes = limited.map((node, index) => {
      const type = node.type || 'Entity';
      const color = colors[type] || colors.Entity;

      return {
        id: String(node.id),
        type: 'default',
        data: {
          label: node.label || 'Unnamed entity',
          properties: node.properties || {},
          entityType: type,
        },
        position: {
          x: Number.isFinite(node.x)
            ? node.x
            : (index % 5) * 230,
          y: Number.isFinite(node.y)
            ? node.y
            : Math.floor(index / 5) * 125,
        },
        style: {
          width: 190,
          padding: '13px 15px',
          borderRadius: 12,
          border: `1px solid ${color}`,
          background: '#151f34',
          color: '#f1f5f9',
          fontSize: 12,
          fontWeight: 600,
          lineHeight: 1.5,
          boxShadow: '0 5px 18px rgba(0,0,0,0.16)',
        },
      };
    });

    const formattedEdges = (data.edges || [])
      .filter(
        (edge) =>
          visibleIds.has(String(edge.source)) &&
          visibleIds.has(String(edge.target))
      )
      .slice(0, 120)
      .map((edge) => ({
        id: String(edge.id || `${edge.source}-${edge.target}-${edge.type}`),
        source: String(edge.source),
        target: String(edge.target),
        label: String(edge.type || '').replaceAll('_', ' '),
        animated: false,
        style: { stroke: '#52617d', strokeWidth: 1.2 },
        labelStyle: { fill: '#aab7cc', fontSize: 9 },
        labelBgStyle: { fill: '#101827', fillOpacity: 0.9 },
      }));

    setNodes(formattedNodes);
    setEdges(formattedEdges);
    setSelected(null);
  }, [data, setNodes, setEdges]);

  const visibleNodes = nodes.filter((node) =>
    String(node.data.label)
      .toLowerCase()
      .includes(search.toLowerCase())
  );

  if (isLoading) {
    return (
      <div className="friendly-error">
        Building your evidence map...
      </div>
    );
  }

  if (isError) {
    return (
      <div className="friendly-error">
        Could not load the evidence map.
        <button onClick={() => refetch()}>Try again</button>
      </div>
    );
  }

  if (!nodes.length) {
    return (
      <div className="clean-panel">
        <div className="page-title">
          <span className="eyebrow">
            <Network size={15} /> RELATIONSHIP MAP
          </span>
          <h2>Evidence Map</h2>
        </div>
        <div className="empty-friendly">
          No entities are available yet. Upload a document and run analysis
          to build the evidence map.
        </div>
      </div>
    );
  }

  return (
    <section className="graph-container clean-panel">
      <header className="graph-title">
        <div>
          <span className="eyebrow">
            <Network size={15} /> RELATIONSHIP MAP
          </span>
          <h2>Evidence Map</h2>
          <p>
            Explore extracted entities and their relationships.
            Select a node to inspect its details.
          </p>
        </div>
      </header>

      <div className="graph-toolbar">
        <label className="graph-search">
          <Search size={16} />
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Find an entity..."
            aria-label="Search entities"
          />
          {search && (
            <button
              type="button"
              onClick={() => setSearch('')}
              aria-label="Clear search"
            >
              <X size={15} />
            </button>
          )}
        </label>

        <div className="graph-counts">
          <span><GitBranch size={15} /> {nodes.length} entities</span>
          <span>{edges.length} relationships</span>
        </div>
      </div>

      <div className="graph-legend">
        {Object.entries(colors).map(([type, color]) => (
          <span key={type}>
            <i style={{ background: color }} />
            {type}
          </span>
        ))}
      </div>

      <div className="graph-layout">
        <div className="graph-visualization">
          <ReactFlow
            nodes={nodes.map((node) => ({
              ...node,
              hidden: !visibleNodes.some((item) => item.id === node.id),
            }))}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={(_, node) => setSelected(node)}
            fitView
            minZoom={0.2}
            maxZoom={1.6}
            proOptions={{ hideAttribution: true }}
          >
            <Controls showInteractive={false} />
            <MiniMap
              nodeColor={(node) =>
                colors[node.data?.entityType] || colors.Entity
              }
              maskColor="rgba(5, 10, 22, 0.7)"
              style={{
                background: '#111a2d',
                border: '1px solid #293650',
                borderRadius: 10,
              }}
            />
            <Background
              variant="dots"
              gap={24}
              size={1}
              color="#293650"
            />
          </ReactFlow>
        </div>

        <aside className="entity-details">
          {selected ? (
            <>
              <div className="entity-details-heading">
                <div>
                  <span className="eyebrow">SELECTED ENTITY</span>
                  <h3>{selected.data.label}</h3>
                </div>
                <button
                  type="button"
                  onClick={() => setSelected(null)}
                  aria-label="Close entity details"
                >
                  <X size={17} />
                </button>
              </div>

              <span className="entity-type-badge">
                {selected.data.entityType}
              </span>

              <h4><Info size={15} /> Entity properties</h4>

              {Object.keys(selected.data.properties).length ? (
                <dl className="entity-properties">
                  {Object.entries(selected.data.properties).map(
                    ([key, value]) => (
                      <div key={key}>
                        <dt>{key.replaceAll('_', ' ')}</dt>
                        <dd>
                          {typeof value === 'object'
                            ? JSON.stringify(value)
                            : String(value ?? '—')}
                        </dd>
                      </div>
                    )
                  )}
                </dl>
              ) : (
                <p className="muted">
                  No additional properties are available.
                </p>
              )}
            </>
          ) : (
            <div className="entity-empty">
              <div className="entity-empty-icon">
                <Network size={22} />
              </div>
              <h3>Entity details</h3>
              <p>
                Select any node in the map to view its type and
                available properties here.
              </p>
            </div>
          )}
        </aside>
      </div>

      {data.nodes?.length > 80 && (
        <p className="graph-note">
          Showing the first 80 of {data.nodes.length} entities.
        </p>
      )}
    </section>
  );
};

export default GraphVisualization;
