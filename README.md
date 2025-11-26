# Automotive LLM analysis

## Quick Start

1. **Prerequisites**

    Input Google API Key in `.env` file
    
    ```env
    GOOGLE_API_KEY=OUR_ACTUAL_KEY_GOES_HERE
    ```

2. **Installation of Dependencies**

    Execute this command to install all necessary Python packages and other dependencies defined in the project configuration.

    ```bash
    make install
    ```

3. **Generate Report**

    Run the analysis pipeline to generate the final report artifacts (e.g., HTML, Markdown).

    ```bash
    make run
    ```
