# UniFi Network Analyzer

This project is an automated tool for analyzing and optimizing UniFi networks using AI-powered recommendations.

## Features

- Collects data from UniFi controllers
- Analyzes WiFi performance, including RF environment, device configurations, and client data
- Provides AI-generated recommendations for network optimization
- Supports interactive follow-up questions

## Prerequisites

- Python 3.7+
- UniFi Controller (tested with version 8.4.62)
- Access to an AI provider (OpenAI, Google AI, or Anthropic)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/gabeosx/unifi-assistant.git
   cd unifi-assistant
   ```

2. Install required packages:
   ```
   pip install -r requirements.txt
   ```

3. Copy `config.yaml_example` to `config.yaml` and update it with your settings:
   ```
   cp config.yaml_example config.yaml
   ```

## Configuration

Edit `config.yaml` to set up your UniFi controller access and AI provider:
