# Autonomous Financial Research Agent (ARA-1)

## Overview
The Autonomous Financial Research Agent (ARA-1) is a Python-based tool designed to generate institutional-grade financial reports for publicly traded companies. It leverages advanced AI models and financial data sources to provide insights, recommendations, and detailed analyses.

## Features
- **Ticker Analysis**: Generate financial reports for specific stock tickers.
- **Interactive Mode**: Run the agent interactively to analyze multiple tickers.
- **Data Sources**: Integrates with financial APIs like Yahoo Finance and SEC EDGAR.
- **Customizable Tools**: Modular design for adding new financial tools and data sources.
- **Report Generation**: Outputs reports in JSON format and renders summaries in the terminal.

## Installation

### Prerequisites
- Python 3.8 or higher
- Virtual environment (recommended)

### Steps
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd AutonomousFinancialResearchAgent
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   & .\venv\Scripts\Activate.ps1  # For Windows
   source venv/bin/activate         # For macOS/Linux
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Command-Line Interface (CLI)
Run the agent with a specific stock ticker:
```bash
python main.py NVDA
```

Run the agent in interactive mode:
```bash
python main.py
```

### Output
- Reports are saved in the `docs/reports/` directory as JSON files.
- Terminal displays a summary of the analysis.

## Project Structure
```
AutonomousFinancialResearchAgent/
├── agent/                 # Core agent logic
├── docs/                  # Documentation and generated reports
├── evaluation/            # Metrics and evaluation tools
├── memory/                # Vector store and memory management
├── synthesis/             # Data validation and decision-making
├── tools/                 # Financial data and analysis tools
├── main.py                # CLI entry point
├── requirements.txt       # Python dependencies
└── README.md              # Project documentation
```

## Dependencies
The project uses the following Python libraries:
- [LangChain](https://github.com/hwchase17/langchain)
- [OpenAI](https://github.com/openai/openai-python)
- [ChromaDB](https://github.com/chroma-core/chroma)
- [Yahoo Finance](https://github.com/ranaroussi/yfinance)
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)
- [Rich](https://github.com/Textualize/rich)

## Contributing
Contributions are welcome! Please fork the repository and submit a pull request.

## License
This project is licensed under the MIT License. See the LICENSE file for details.