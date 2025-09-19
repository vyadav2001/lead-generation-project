# Lead Generation Project

## Overview
This is a Python-based lead generation automation script designed for a hardware store specializing in custom PCs and servers. The project fetches potential client companies, enriches them with insights, generates personalized outreach emails, scores leads, and outputs the results in JSON, CSV, and HTML formats. It uses the Apollo.io API for lead sourcing, web scraping for insights, and a local Ollama model for email generation.

## Features
- **Lead Sourcing:** Retrieves companies with 50-200 employees in the software industry (e.g., Zomato, Swiggy) via Apollo.io, with mock data as a fallback.
- **Insight Enrichment:** Scrapes website content to identify business insights (e.g., software development focus).
- **Email Generation:** Creates custom B2B outreach emails using a local Ollama LLM.
- **Lead Scoring:** Assigns scores (0-100) based on employee count, insights, and randomness.
- **Output Formats:** Saves data to `leads.json`, `leads.csv`, and a `dashboard.html` file for visualization.

## Prerequisites
- Python 3.x
- Required libraries: `requests`, `beautifulsoup4`, `openai`, `pandas`
- Apollo.io API key (replace placeholder in code)
- Local Ollama server running with `llama3.2` model
