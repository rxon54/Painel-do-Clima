# Copilot Instructions: Painel do Clima

## Project Context
This project fetches and summarizes climate risk data for Brazilian municipalities using the AdaptaBrasil API. The main workflow is: **API call → data parsing → summary generation → output**.

## Coding Guidelines
- Use Python 3.x.
- Organize code into modules: API client, data processing, summarization, and output.
- Write clear docstrings and comments.
- Use `requests` for HTTP calls and `pandas` for data manipulation (if needed).

## Tasks for Copilot
- Implement functions to:
  - Build and send API requests for a given city, year, and scenario.
  - Parse and structure the API response.
  - Extract and rank key indices and influencing factors.
  - Generate a concise, human-readable summary of the results.
  - Output results in both text and structured formats.
- Ensure code is modular and easy to test.
- Provide example usage for fetching and summarizing data for a sample city.

## Notes
- Summaries should be clear and actionable, highlighting the most influential risk factors.
- Follow the conceptual framework described in the AdaptaBrasil and Painel do Clima briefings.
- Ask for clarification if API endpoints or data fields are ambiguous.