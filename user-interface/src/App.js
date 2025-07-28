import React from 'react';
import ControlPanel from './ControlPanel';
import GraphView from './GraphView';
import './App.css';

function App() {
  return (
    <div className="App">
      <h1>Pró-Vida Control Panel</h1>
      <div className="main-content">
        <ControlPanel />
        <GraphView />
      </div>
    </div>
  );
}

export default App;