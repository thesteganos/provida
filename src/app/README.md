# src/app Directory

This directory contains the core application logic for the Provida project. Each subdirectory represents a specific component or module of the application.

## Subdirectories

### agents/
Contains specialized AI agents responsible for different tasks such as planning, analysis, synthesis, memory management, etc.

### cli.py
The main Command Line Interface entry point for interacting with the application.

### core/
Core infrastructure services including LLM provider, MinIO, ChromaDB, and other essential utilities.

### orchestrator_graph.py
Defines the deep research workflow using LangGraph.

### orchestrator.py
Executes the deep research mode and returns the final state of the research graph.

### rag.py
Implementation of the Retrieval-Augmented Generation (RAG) logic.

### scheduler_service.py
Handles scheduling and execution of background tasks such as daily updates and quarterly reviews.

### tools/
External integrations with third-party services (e.g., Brave Search, PubMed) and utility functions.

## Usage

### Running the CLI
To run the CLI, navigate to the project root and execute:
```bash
python -m src.app.cli
```

### Rapid Query Mode (`rapida`)
Get quick, evidence-based answers from the existing knowledge base.
```bash
python -m src.app.cli rapida "qual a dose recomendada de vitamina D para adultos?"
```

### Deep Research Mode (`profunda`)
Initiate a comprehensive, multi-step research process on a given topic.
```bash
python -m src.app.cli profunda "novas abordagens cirúrgicas para obesidade mórbida"
```

## Dependencies
All dependencies for this module are listed in `requirements.txt`.