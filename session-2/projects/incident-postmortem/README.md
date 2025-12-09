# Incident PostMortem Generator

An AI-powered system that automatically generates comprehensive incident postmortem reports by analyzing logs, identifying root causes, and producing high-quality documentation using **LangGraph v1** and **LangChain v1**.

## 🎯 Features

- **Multi-Agent Collaboration**: 4 specialized agents working together
- **Self-Reflection Pattern**: Automatic quality improvement loop
- **LLM-as-Judge**: Structured evaluation with scoring rubric
- **Human-in-the-Loop**: Optional human approval for critical (SEV1) incidents
- **Streaming Output**: Real-time progress updates
- **Dual Provider Support**: Works with both DIAL (EPAM) and OpenAI

## 🏗️ Architecture

```
                    ┌─────────────────────────────────────────────────────┐
                    │           INCIDENT POSTMORTEM SYSTEM                │
                    ├─────────────────────────────────────────────────────┤
                    │                                                     │
                    │   Incident Logs                                     │
                    │        │                                            │
                    │        ▼                                            │
                    │   ┌───────────────┐                                 │
                    │   │ Log Analyzer  │ ← Parses and summarizes logs    │
                    │   └───────┬───────┘                                 │
                    │           │                                         │
                    │           ▼                                         │
                    │   ┌───────────────┐                                 │
                    │   │ Root Cause    │ ← Identifies failure chain      │
                    │   │ Analyzer      │                                 │
                    │   └───────┬───────┘                                 │
                    │           │                                         │
                    │           ▼                                         │
                    │   ┌───────────────┐                                 │
                    │   │ Writer        │ ← Drafts postmortem report      │
                    │   └───────┬───────┘                                 │
                    │           │                                         │
                    │           ▼                                         │
                    │   ┌───────────────┐                                 │
                    │   │ Reviewer      │ ← LLM-as-Judge evaluation       │
                    │   │ (LLM-Judge)   │                                 │
                    │   └───────┬───────┘                                 │
                    │           │                                         │
                    │     ┌─────┴─────┐                                   │
                    │     ▼           ▼                                   │
                    │   [Pass]     [Revise] ──→ Back to Writer            │
                    │     │                                               │
                    │     ▼                                               │
                    │   Final PostMortem Report                           │
                    └─────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### One-Command Setup and Run

```bash
# Complete setup and run demo
make setup && make demo
```

### Manual Setup

```bash
# 1. Install dependencies
make install

# 2. Copy environment file and add your API key
cp .env.example .env
# Edit .env and set DIAL_API_KEY or OPENAI_API_KEY

# 3. Run demo
make demo
```

## 📋 Prerequisites

- **Python 3.11+** required
- **API Key**: Either DIAL (for EPAM employees) or OpenAI

## 🔍 Observability & Evaluation

### Langfuse Integration (Observability)

Track all LLM calls, view traces, and debug agent behavior:

```bash
# 1. Set Langfuse credentials
export LANGFUSE_PUBLIC_KEY="pk-lf-..."
export LANGFUSE_SECRET_KEY="sk-lf-..."

# 2. Run with tracing enabled
python main.py --demo --trace

# 3. Check setup
python observability.py
```

View traces at: https://cloud.langfuse.com

### DeepEval Integration (Testing)

Evaluate output quality using LLM-as-Judge metrics:

```bash
# Run evaluation tests
pytest test_eval.py -v

# Run integration tests (requires API key)
pytest test_eval.py -v -m integration

# Generate detailed DeepEval report
deepeval test run test_eval.py
```

## 🎮 Usage

### Available Commands

```bash
make help              # Show all available commands

# Setup
make setup             # Complete setup (install + create .env)
make install           # Install dependencies only

# Run Demos
make demo              # Run synthetic demo (batch mode)
make demo-stream       # Run demo with streaming output
make database          # Run database outage sample
make api               # Run API timeout sample
make memory            # Run memory leak sample
make interactive       # Run in interactive mode

# Maintenance
make test              # Run tests
make clean             # Clean cache files
```

### Manual Execution

```bash
# Run with demo incident
python main.py --demo

# Run with sample incident file (streaming)
python main.py --file sample_incidents/database_outage.json --stream

# Run with custom max iterations
python main.py --demo --max-iterations 5

# Interactive mode
python main.py --interactive
```

## ⚙️ Configuration

Configuration is managed via `.env` file. Key settings:

| Variable | Default | Description |
|----------|---------|-------------|
| `DIAL_API_KEY` | - | DIAL API key (for EPAM employees) |
| `OPENAI_API_KEY` | - | OpenAI API key (alternative) |
| `MODEL_NAME` | `gpt-4o` | Model name |
| `TEMPERATURE` | `0.3` | Model temperature |
| `QUALITY_THRESHOLD` | `0.75` | Minimum quality score (0-1) |
| `MAX_REVISIONS` | `3` | Max writer-reviewer iterations |
| `HIGH_SEV_THRESHOLD` | `SEV1` | Severity requiring human review |
| `REQUIRE_HUMAN_REVIEW` | `true` | Enable HITL for high severity |

## 🤖 Agents

| Agent | Role | Specialty |
|-------|------|-----------|
| **Log Analyzer** | Parse and summarize incident logs | Pattern recognition, timeline reconstruction |
| **Root Cause** | Identify failure chain and contributing factors | Causal reasoning, 5-whys analysis |
| **Writer** | Draft comprehensive postmortem report | Technical writing, blameless culture |
| **Reviewer** | Evaluate report quality (LLM-as-Judge) | Quality assessment, actionable feedback |

## 📊 Quality Evaluation

The Reviewer agent scores reports on 5 dimensions (1-10 each):

- **Completeness**: All required sections covered?
- **Clarity**: Clear and understandable writing?
- **Accuracy**: Root cause analysis accurate?
- **Actionability**: Specific, actionable items with owners?
- **Blamelessness**: Follows blameless postmortem principles?

If overall score is below threshold (default 75%), the report loops back to Writer for revision.

## 🛡️ Human-in-the-Loop (HITL)

For SEV1 (critical) incidents, the workflow pauses for human review:

1. Workflow interrupts and displays incident details
2. Human reviews the draft report
3. Human approves or rejects with feedback
4. If approved, report is finalized
5. If rejected, goes back to Writer for revision

## 📁 Project Structure

```
incident-postmortem/
├── README.md                 # This file
├── Makefile                  # Build commands
├── .env                      # Environment configuration (create from .env.example)
├── .env.example              # Example environment file
├── requirements.txt          # Python dependencies
├── config.py                 # Configuration management
├── main.py                   # Main entry point
├── agents/                   # Agent implementations
│   ├── __init__.py
│   ├── log_analyzer.py       # Log analysis agent
│   ├── root_cause.py         # Root cause analysis agent
│   ├── writer.py             # Report writer agent
│   └── reviewer.py           # Report reviewer agent (LLM-as-Judge)
├── graph/                    # LangGraph workflow
│   ├── __init__.py
│   ├── state.py              # State definitions
│   └── workflow.py           # Workflow graph
└── sample_incidents/         # Sample incident data
    ├── database_outage.json
    ├── api_timeout.json
    └── memory_leak.json
```

## 🔧 Advanced Usage

### Custom Incident JSON

Create a JSON file with the following structure:

```json
{
  "incident_id": "INC-12345",
  "title": "API Gateway Timeout",
  "severity": "SEV2",
  "description": "Users experiencing 500 errors",
  "logs": "...",
  "metrics": {},
  "timeline": [
    {"time": "14:30", "event": "First alerts"},
    {"time": "15:00", "event": "Issue resolved"}
  ]
}
```

Then run:
```bash
python main.py --file your_incident.json --stream
```

### Programmatic Usage

```python
from config import config
from main import get_llm
from graph.workflow import create_postmortem_graph

# Initialize
model = get_llm()
graph = create_postmortem_graph(model, enable_hitl=True)

# Define incident
initial_state = {
    "incident_id": "INC-12345",
    "severity": "SEV2",
    "title": "API Gateway Timeout",
    # ... other fields
}

# Run
config = {"configurable": {"thread_id": "INC-12345"}}
result = graph.invoke(initial_state, config)

# Access report
print(result["final_report"])
```

## 🔄 Latest Updates (December 2024)

- ✅ **LangGraph v1.0+**: Modern StateGraph, Command API, interrupt patterns
- ✅ **LangChain v1.0+**: Latest model interfaces and message formats
- ✅ **Dual Provider**: DIAL and OpenAI support
- ✅ **Makefile**: One-command execution
- ✅ **Enhanced Config**: Environment-based configuration

## 🧪 Testing

Run the test suite:
```bash
make test
```

Or manually:
```bash
pytest test_postmortem.py -v
```

## 🐛 Troubleshooting

### "No API key configured"
**Solution**: Edit `.env` and set `DIAL_API_KEY` or `OPENAI_API_KEY`

### "ModuleNotFoundError"
**Solution**: Run `make install` or `pip install -r requirements.txt`

### Quality scores too low
**Solution**: 
- Lower `QUALITY_THRESHOLD` in `.env` (e.g., 0.6)
- Increase `MAX_REVISIONS` to allow more iterations
- Improve incident data quality

## 📚 Sample Output

```
✅ Using DIAL (Azure OpenAI)
   Deployment: gpt-4
   Temperature: 0.3
   Max iterations: 3

============================================================
🚀 Starting Incident PostMortem Generation (Batch)
============================================================

======================================================================
📊 LOG ANALYZER - Parsing Incident Logs
======================================================================
📋 Log Summary:
   The logs reveal a database connection pool exhaustion...
🔴 Error Patterns (3):
   • Connection pool exhausted
   • Request timeouts
   • Slow query detected
...

[Complete postmortem report generated]
```

## 🤝 Contributing

This is a workshop project demonstrating LangGraph and LangChain capabilities. Feel free to:
- Customize agents for your use case
- Add new sample incidents
- Adjust quality thresholds
- Integrate with your incident management system

## 📄 License

This project is part of the Agentic AI Workshop materials.

## 🙋 Support

For questions or issues:
1. Check this README
2. Review code comments in the project
3. Examine sample incidents
4. Consult LangGraph/LangChain documentation

---

**Built with LangGraph v1 & LangChain v1** 🚀
