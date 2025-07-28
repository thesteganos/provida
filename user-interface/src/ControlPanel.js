import React, { useState } from 'react';
import axios from 'axios';
import './ControlPanel.css';

function ControlPanel() {
  const [isAutonomousResearchEnabled, setIsAutonomousResearchEnabled] = useState(false);

  const toggleAutonomousResearch = async () => {
    try {
      const response = await axios.post('/api/research/toggle');
      setIsAutonomousResearchEnabled(!isAutonomousResearchEnabled);
      alert(response.data.message);
    } catch (error) {
      console.error('Error toggling autonomous research:', error);
      alert('Failed to toggle autonomous research');
    }
  };

  const startManualResearch = async () => {
    try {
      const response = await axios.post('/api/research/start');
      alert(response.data.message);
    } catch (error) {
      console.error('Error starting manual research:', error);
      alert('Failed to start manual research');
    }
  };

  return (
    <div className="control-panel">
      <h2>Autonomia Controlada</h2>
      <div>
        <label>
          <input
            type="checkbox"
            checked={isAutonomousResearchEnabled}
            onChange={toggleAutonomousResearch}
          />
          Enable Autonomous Research
        </label>
      </div>
      <button onClick={startManualResearch}>Start Manual Research</button>
    </div>
  );
}

export default ControlPanel;
