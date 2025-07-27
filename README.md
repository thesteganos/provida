# Provida Project

## Overview
Provida is a comprehensive application designed to manage and orchestrate various tasks efficiently. It leverages environment variables for configuration and includes robust logging and error handling.

## Architecture
The application is structured around a set of agents that perform specific tasks, such as planning, research, analysis, and synthesis. The agents are orchestrated by a central component that uses a graph-based approach to manage the flow of information. The application also includes a set of tools for interacting with external services, such as web search and knowledge graphs.

### Agents
- **Planning Agent:** Generates a research plan based on a user's query.
- **Research Agent:** Executes the research plan, collecting data from various sources.
- **Analysis Agent:** Classifies the evidence and extracts relevant information from the collected data.
- **Synthesis Agent:** Generates a final report based on the analyzed information.
- **Verification Agent:** Fact-checks the final report against the knowledge graph.

### Tools
- **Web Search:** A tool for searching the web for information.
- **Knowledge Graph:** A tool for interacting with a knowledge graph.

## Installation

### Prerequisites
- Python 3.13 or higher
- pip (Python package installer)

### Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/provida.git
   cd provida
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Setup

### Environment Variables
Create a `.env` file in the root directory and add the following environment variables:
```plaintext
EMAIL_HOST=your-email-host
EMAIL_PORT=your-email-port
EMAIL_USER=your-email-user
EMAIL_PASSWORD=your-email-password
API_KEY=your-api-key
```

## Usage

### Running the Application
To run the application, use the following command:
```bash
python src/main.py
```

### Example Usage
Here is an example of how to use the application:
```bash
# Example command to run a specific feature
python src/app/scheduler.py --schedule daily
```

## Dependencies
- `requests` - For making HTTP requests.
- `biopython` - For handling biological data.
- `loguru` - For logging.

You can find the complete list of dependencies in the `requirements.txt` file.

## Contributing
Contributions are welcome! Please read the [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines on how to contribute to the project.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
