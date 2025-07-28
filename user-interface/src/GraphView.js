import React, { useEffect, useState } from 'react';
import axios from 'axios';
import './GraphView.css';

function GraphView() {
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchGraphData = async () => {
      try {
        const response = await axios.get('/api/graph');
        setGraphData(response.data);
        setLoading(false);
      } catch (err) {
        setError(err);
        setLoading(false);
      }
    };

    fetchGraphData();
  }, []);

  if (loading) return <div className="graph-view">Loading graph data...</div>;
  if (error) return <div className="graph-view">Error: {error.message}</div>;

  return (
    <div className="graph-view">
      <h2>Knowledge Graph</h2>
      {graphData && (
        <div>
          <h3>Nodes:</h3>
          <ul>
            {graphData.nodes.map(node => (
              <li key={node.id}>
                {node.labels.join(', ')}: {node.properties.name || node.id}
              </li>
            ))}
          </ul>
          <h3>Relationships:</h3>
          <ul>
            {graphData.links.map((link, index) => (
              <li key={index}>
                {link.source} -[{link.type}]-> {link.target}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default GraphView;
