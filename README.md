# Provida Project

## Overview
Provida is a comprehensive application designed to manage and orchestrate various tasks efficiently. It leverages environment variables for configuration and includes robust logging and error handling.

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
