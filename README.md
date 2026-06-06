# NFR Requirements Classifier

A desktop application for classifying software requirements into 7 categories using the Groq API and Llama 3.3 70B.

## Quick Start

```bash
cd classifier_app
pip install -r requirements.txt
python main.py
```

## Setup Requirements

- Python 3.9+
- Groq API key in `.env` or `../.env` file
- Internet connection

## Supported Categories

| Label | Category               | Description                                                        |
|:------|:-----------------------|:-------------------------------------------------------------------|
| F     | Functional             | Specific behaviour, feature, or capability                         |
| LF    | Look & Feel            | Appearance, visual design, or branding                             |
| O     | Operability            | Operational environment, platform support, deployment constraints  |
| PE    | Performance            | Speed, response time, throughput, capacity                         |
| SE    | Security               | Encryption, authentication, authorization, access control          |
| US    | Usability              | Ease of use, learnability, accessibility                           |
| Other | Other NFR              | Availability, scalability, maintainability, legal, etc.            |

## Features

- Classify single requirements or run batch classifications from CSV/TXT files
- Compare different prompt strategies (Zero-Shot, Few-Shot)
- View classification statistics and distribution charts
- Session-based classification history with CSV export
- Keyboard shortcut: `Ctrl+Enter` to classify
