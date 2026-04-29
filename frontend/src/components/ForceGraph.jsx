import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as d3 from 'd3';
import { Card, Button, Select, Tag, Space } from 'antd';
import { ZoomInOutlined, ZoomOutOutlined, ReloadOutlined } from '@ant-design/icons';

const NODE_COLORS = {
  class: '#667eea',
  orphan: '#ffa502',
  leaf: '#2ed573',
  root: '#ff4757',
};

const LINK_COLORS = {
  descendant: '#a4b0be',
  'direct-child': '#5352ed',
  sibling: '#ff6b6b',
  modifier: '#feca57',
};

const ForceGraph = ({ graphData, onNodeClick }) => {
  const svgRef = useRef(null);
  const containerRef = useRef(null);
  const [tooltip, setTooltip] = useState({ visible: false, x: 0, y: 0, content: '' });
  const [selectedNode, setSelectedNode] = useState(null);
  const [filterType, setFilterType] = useState('all');
  const simulationRef = useRef(null);

  const renderGraph = useCallback(() => {
    if (!graphData || !graphData.nodes || !containerRef.current) return;

    const container = containerRef.current;
    const width = container.clientWidth;
    const height = 600;

    d3.select(svgRef.current).selectAll('*').remove();

    const svg = d3.select(svgRef.current)
      .attr('width', width)
      .attr('height', height);

    const g = svg.append('g');

    const zoom = d3.zoom()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });

    svg.call(zoom);

    const nodes = graphData.nodes.map(d => ({ ...d }));
    const edges = graphData.edges.map(d => ({ ...d }));

    const filteredNodes = filterType === 'all' ? nodes : nodes.filter(n => {
      if (filterType === 'orphan') return n.parent_classes?.length === 0;
      if (filterType === 'leaf') return n.child_classes?.length === 0;
      if (filterType === 'connected') return n.parent_classes?.length > 0 || n.child_classes?.length > 0;
      return true;
    });

    const nodeIds = new Set(filteredNodes.map(n => n.id));
    const filteredEdges = edges.filter(e => nodeIds.has(e.source) && nodeIds.has(e.target));

    const simulation = d3.forceSimulation(filteredNodes)
      .force('link', d3.forceLink(filteredEdges).id(d => d.id).distance(100).strength(0.3))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(35));

    simulationRef.current = simulation;

    const link = g.append('g')
      .selectAll('line')
      .data(filteredEdges)
      .enter()
      .append('line')
      .attr('class', 'link')
      .attr('stroke', d => LINK_COLORS[d.type] || '#999')
      .attr('stroke-width', 1.5)
      .attr('stroke-dasharray', d => d.type === 'descendant' ? '5,5' : 'none');

    const arrowheads = g.append('defs')
      .selectAll('marker')
      .data(['descendant', 'direct-child', 'sibling', 'modifier'])
      .enter()
      .append('marker')
      .attr('id', d => `arrowhead-${d}`)
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 25)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', d => LINK_COLORS[d] || '#999');

    link.attr('marker-end', d => `url(#arrowhead-${d.type})`);

    const node = g.append('g')
      .selectAll('g')
      .data(filteredNodes)
      .enter()
      .append('g')
      .attr('class', 'node')
      .call(d3.drag()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended));

    node.append('circle')
      .attr('r', d => {
        const baseRadius = 20;
        const relationCount = (d.parent_classes?.length || 0) + (d.child_classes?.length || 0);
        return baseRadius + Math.min(relationCount * 2, 15);
      })
      .attr('fill', d => {
        if (d.parent_classes?.length === 0 && d.child_classes?.length === 0) return NODE_COLORS.orphan;
        if (d.parent_classes?.length === 0) return NODE_COLORS.root;
        if (d.child_classes?.length === 0) return NODE_COLORS.leaf;
        return NODE_COLORS.class;
      })
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .on('mouseover', (event, d) => {
        d3.select(event.target).attr('stroke', '#333').attr('stroke-width', 3);
        const content = `
          <div><strong>${d.name}</strong></div>
          <div>Type: ${d.type}</div>
          <div>Specificity: ${d.specificity.toFixed(3)}</div>
          <div>Rules: ${d.rules?.length || 0}</div>
          <div>Parents: ${d.parent_classes?.length || 0}</div>
          <div>Children: ${d.child_classes?.length || 0}</div>
        `;
        setTooltip({
          visible: true,
          x: event.pageX + 10,
          y: event.pageY - 10,
          content
        });
      })
      .on('mouseout', (event) => {
        d3.select(event.target).attr('stroke', '#fff').attr('stroke-width', 2);
        setTooltip({ ...tooltip, visible: false });
      })
      .on('click', (event, d) => {
        setSelectedNode(d);
        if (onNodeClick) onNodeClick(d);
      });

    node.append('text')
      .text(d => d.name.length > 15 ? d.name.substring(0, 12) + '...' : d.name)
      .attr('text-anchor', 'middle')
      .attr('dy', 4)
      .attr('font-size', '10px')
      .attr('fill', '#fff')
      .attr('pointer-events', 'none')
      .style('text-shadow', '0 0 2px rgba(0,0,0,0.5)');

    simulation.on('tick', () => {
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);

      node.attr('transform', d => `translate(${d.x},${d.y})`);
    });

    function dragstarted(event, d) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event, d) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragended(event, d) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }

  }, [graphData, filterType, onNodeClick]);

  useEffect(() => {
    renderGraph();
    const handleResize = () => renderGraph();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [renderGraph]);

  const handleZoomIn = () => {
    d3.select(svgRef.current).transition().call(d3.zoom().scaleBy, 1.3);
  };

  const handleZoomOut = () => {
    d3.select(svgRef.current).transition().call(d3.zoom().scaleBy, 0.7);
  };

  const handleReset = () => {
    renderGraph();
  };

  return (
    <Card
      title={
        <Space>
          <span>CSS Class Relationship Graph</span>
          {selectedNode && <Tag color="blue">Selected: {selectedNode.name}</Tag>}
        </Space>
      }
      extra={
        <Space>
          <Select
            value={filterType}
            onChange={setFilterType}
            style={{ width: 150 }}
            options={[
              { value: 'all', label: 'All Nodes' },
              { value: 'orphan', label: 'Orphans' },
              { value: 'leaf', label: 'Leaves' },
              { value: 'connected', label: 'Connected' },
            ]}
          />
          <Button icon={<ZoomInOutlined />} onClick={handleZoomIn} />
          <Button icon={<ZoomOutOutlined />} onClick={handleZoomOut} />
          <Button icon={<ReloadOutlined />} onClick={handleReset} />
        </Space>
      }
    >
      <div ref={containerRef} className="force-graph-container">
        <svg ref={svgRef} />
        {tooltip.visible && (
          <div
            className="force-graph-tooltip"
            style={{ left: tooltip.x, top: tooltip.y }}
            dangerouslySetInnerHTML={{ __html: tooltip.content }}
          />
        )}
      </div>
      <div className="graph-legend">
        <div className="legend-item">
          <span className="legend-circle" style={{ backgroundColor: NODE_COLORS.root }} />
          <span>Root Nodes</span>
        </div>
        <div className="legend-item">
          <span className="legend-circle" style={{ backgroundColor: NODE_COLORS.class }} />
          <span>Connected Classes</span>
        </div>
        <div className="legend-item">
          <span className="legend-circle" style={{ backgroundColor: NODE_COLORS.leaf }} />
          <span>Leaf Nodes</span>
        </div>
        <div className="legend-item">
          <span className="legend-circle" style={{ backgroundColor: NODE_COLORS.orphan }} />
          <span>Orphan Nodes</span>
        </div>
      </div>
    </Card>
  );
};

export default ForceGraph;
