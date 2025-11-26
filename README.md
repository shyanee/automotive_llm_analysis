# Automotive LLM analysis

- [Automotive LLM analysis](#automotive-llm-analysis)
  - [Executive Summary](#executive-summary)
    - [Approach \& Design Choice](#approach--design-choice)
    - [Considerations](#considerations)
  - [Quick Start](#quick-start)

## Executive Summary

### Approach & Design Choice

### Considerations


## Quick Start

1. **Installation of Dependencies**

    Execute this command to install all necessary Python packages and other dependencies defined in the project configuration.

    ```bash
    make install
    ```

2. **Set up API key**

    Input Google API Key in `.env` file

    ```env
    GOOGLE_API_KEY=YOUR_ACTUAL_KEY_GOES_HERE
    ```

3. **Configuration**

    Configuration files located in `./config`

   - General file configuration: `config.yml`
   - LLM Specific configurations: `llm_config.yml`
     - Gemini model configuration
     - Prompt engineering

4. **Generate Report**

    Run the analysis pipeline to generate the final report (`html`, `md`).
    Ensure venv is activated. If not activated run

    ```bash
    . venv/bin/activate 
    ```
  
    Generate report:

    ```bash
    make run
    ```
