import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import axios from 'axios';
import App from './App';

// Mock axios to control API responses
jest.mock('axios');

describe('App Component', () => {
  test('renders main title', () => {
    render(<App />);
    expect(screen.getByText(/Pró-Vida Control Panel/i)).toBeInTheDocument();
  });

  test('ControlPanel renders and interacts', async () => {
    axios.post.mockResolvedValueOnce({ data: { message: 'Autonomous research toggled' } });
    axios.post.mockResolvedValueOnce({ data: { message: 'Manual research started' } });

    render(<App />);

    // Test toggle autonomous research
    const checkbox = screen.getByLabelText(/Enable Autonomous Research/i);
    expect(checkbox).not.toBeChecked();
    fireEvent.click(checkbox);
    await waitFor(() => expect(checkbox).toBeChecked());
    expect(axios.post).toHaveBeenCalledWith('/api/research/toggle');

    // Test start manual research
    const startButton = screen.getByRole('button', { name: /Start Manual Research/i });
    fireEvent.click(startButton);
    await waitFor(() => expect(axios.post).toHaveBeenCalledWith('/api/research/start'));
  });

  test('GraphView renders and fetches data', async () => {
    axios.get.mockResolvedValueOnce({
      data: {
        nodes: [{ id: '1', labels: ['Person'], properties: { name: 'Alice' } }],
        links: [{ source: '1', target: '2', type: 'KNOWS' }],
      },
    });

    render(<App />);

    expect(screen.getByText(/Loading graph data.../i)).toBeInTheDocument();

    await waitFor(() => expect(screen.getByText(/Knowledge Graph/i)).toBeInTheDocument());
    expect(screen.getByText(/Nodes:/i)).toBeInTheDocument();
    expect(screen.getByText(/Person: Alice/i)).toBeInTheDocument();
    expect(screen.getByText(/Relationships:/i)).toBeInTheDocument();
    expect(screen.getByText(/1 -[KNOWS]-> 2/i)).toBeInTheDocument();
    expect(axios.get).toHaveBeenCalledWith('/api/graph');
  });

  test('GraphView handles fetch error', async () => {
    axios.get.mockRejectedValueOnce(new Error('Network Error'));

    render(<App />);

    expect(screen.getByText(/Loading graph data.../i)).toBeInTheDocument();

    await waitFor(() => expect(screen.getByText(/Error: Network Error/i)).toBeInTheDocument());
    expect(axios.get).toHaveBeenCalledWith('/api/graph');
  });
});