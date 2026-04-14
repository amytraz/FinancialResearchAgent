# 🤖 Autonomous Financial Research Agent (ARA-1)

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A highly advanced, deterministic Python-based autonomous agent designed to run an OODA (Observe, Orient, Decide, Act) loop to generate institutional-grade financial equity research reports. ARA-1 leverages advanced LLMs, parallel tool execution, and real-time financial data sources to deliver actionable, robust investment theses.

---

## ✨ Key Features

- **🧠 Deterministic OODA Loop**: Enforces rigorous reasoning steps for objective, data-driven investment recommendations (Margin of Safety, fundamental cross-checks).
- **⚡ Parallel Tool Execution**: Fetches data from multiple sources simultaneously to significantly reduce analysis time.
- **🛡️ Robust Error Handling**: Implements tenacity back-off and retry strategies for resilient API interactions and data fetching.
- **📊 Multi-Format Reporting**: Generates interactive terminal summaries, structured JSON data, and professional PDF reports.
- **📉 Token-Aware Summary Buffering**: Intelligently summarizes context to prevent rate limits and optimize LLM context usage.
- **🔌 Extensible Architecture**: Modular design for easily integrating new financial tools, vector databases, and data sources (Yahoo Finance, SEC EDGAR, etc.).

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8+
- [Git](https://git-scm.com/)
- An OpenAI API Key (or equivalent LLM provider API key)

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd AutonomousFinancialResearchAgent
   ```

2. **Set up the virtual environment:**
   ```bash
   python -m venv venv
   
   # For Windows:
   .\venv\Scripts\Activate.ps1
   
   # For macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration:**
   Create a `.env` file in the root directory and add your API credentials:
   ```env
   OPENAI_API_KEY=your_api_key_here
   # Add other required API keys here
   ```

---

## 💻 Usage

### Command-Line Interface (CLI)

**Single Ticker Analysis:**
Run the agent focusing on a specific stock ticker directly from the terminal.
```bash
python main.py NVDA
```

**Interactive Mode:**
Launch the agent interactively to sequentially analyze multiple tickers or query specific financial metrics.
```bash
python main.py
```

### Generated Output
- **Reports**: Complete structured analyses are saved as `JSON` and `PDF` files in the `docs/reports/` directory.
- **Logs**: Review real-time reasoning and agent logs in the terminal.
- **Data Stores**: Vectorized memory data is stored in `memory/chroma_data/`.

---

## 🏗️ Project Architecture

```plaintext
AutonomousFinancialResearchAgent/
├── agent/                 # Core OODA loop and agent orchestration
├── docs/                  # Generated reports and project documentation
├── evaluation/            # Performance metrics and evaluation utilities
├── memory/                # Vector store (ChromaDB) and conversation memory management
├── synthesis/             # Data validation, summary buffering, and decision-making logic
├── tools/                 # Financial data fetching and parallel analysis tools
├── main.py                # Command-line entry point
├── requirements.txt       # Project dependencies
└── .env                   # Environment variables (Ignored by Git)
```

---

## 🛠️ Tech Stack & Dependencies

- **[LangChain](https://github.com/hwchase17/langchain)** - Agent framework and tooling orchestration.
- **[OpenAI](https://platform.openai.com/docs/)** - Core LLM reasoning engine.
- **[ChromaDB](https://docs.trychroma.com/)** - Local vector database for context retrieval.
- **[yfinance](https://github.com/ranaroussi/yfinance)** - Real-time market data retrieval.
- **[Rich](https://github.com/Textualize/rich)** - Beautiful terminal formatting and interactive displays.
- **[Tenacity](https://github.com/jd/tenacity)** - Retry behavior for robust API requests.

---

## 🤝 Contributing

Contributions are welcome! Please fork the repository and submit a pull request.

---

## 📜 License

This project is licensed under the MIT License. See the LICENSE file for details. 