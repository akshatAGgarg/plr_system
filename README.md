# Proactive Locator Remediation (PLR) System

## Overview
This system detects DOM changes in web applications and automatically updates test locators.

## Architecture
- **Ingest**: Playwright + CDP (Capture AXTree/Shadow DOM)
- **Analyze**: RTED (APTED) + MarkupLM (Semantic Recovery)
- **Generate**: ROBULA+ (Robust XPath)
- **Integrate**: GitOps (Auto-PR/Commit)

## Installation
```bash
pip install -r requirements.txt
```

## Usage
Start the PostgreSQL database:
```bash
docker-compose up -d
```

Run the pipeline:
```bash
python main.py --url http://example.com --build $BUILD_ID
```
