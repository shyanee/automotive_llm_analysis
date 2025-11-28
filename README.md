# Automotive LLM analysis

- [Automotive LLM analysis](#automotive-llm-analysis)
  - [Executive Summary](#executive-summary)
    - [Architecture \& Design Choice](#architecture--design-choice)
      - [Key Design Constraints and Rationale](#key-design-constraints-and-rationale)
      - [System Architecture](#system-architecture)
    - [Considerations](#considerations)
    - [Architecture considerations](#architecture-considerations)
  - [Quick Start](#quick-start)

## Executive Summary

### Architecture & Design Choice

  The design of the system was primarily guided by the capabilities and limitations of the Google Gemini API.

#### Key Design Constraints and Rationale

- Data Ingestion:
  - Limitation of the Google Gemini API: No native support for native ingestion of data (`csv/xls/xlsx`) directly.
  - API Formatting: textual input (string)
  
  As a result, the system needs to preprocess data, converting structured formats (e.g., `csv` files) into a text-based format that can be processed by the LLM.
  
  **Solution**: The approach adopted involves transforming structured data into a context string, which is then parsed into Markdown (`md`) format before being fed into the model. This transformation allows the data, originally in formats like `csv`, to be represented as human-readable text that the LLM can easily process. While `JSON` is a more machine-readable format, `Markdown` provides a balanced compromise. It is easier for users to read and modify the prompts, enabling quick updates without requiring deep technical knowledge. Markdown also offers the flexibility to format the data in a way that’s more intuitive for human users, which is particularly useful when iterating on the model’s inputs.

- Visualisation
  - Limitation: LLM model is not designed to generate visual outputs (e.g., charts or graphs)
  
  **Solution**: The system includes a Visualization module/class, which transforms the model's output or preprocessed data into visual formats (such as bar charts, line graphs, etc.) to facilitate better understanding and presentation of results.

#### System Architecture

Per the constraints, the system architecture is divided into the following key components:

1. Data Validation
   - Basic dataframe validation (column/row checks)
   - Enforcement of business rules
2. Data Ingestion and Transformation
   - Convert raw data (`csv` or other structured formats) into a format that can be interpreted by the LLM
   - Transformation of structured (raw) data into a context string in Markdown format that can be passed to the LLM for processing
      - Imputation/removal of erronous/missing data
      - Data binning
3. Visualiser
   - Generation of charts for visual representation of data in report
4. LLM Engine
   - Consolidates basic prompts and system role prompts (`/config`) together with context string from the transformation step as a machine-readable Markdown (`md`) format
   - Handles interaction with model including error management
5. Testing & Governance
   - Unit-testing: Unit-tests designed for each class/module using the pytest framework following the Arrange-Act-Assert (AAA) pattern
   - TODO: Evaluation Framework (Optional)
     - Assess performance of model
   - TODO: Guardrails (Optional)

### Considerations

- Scalability
- Flexibility (Modularity)
- Security
- Performance

### Architecture considerations

Retrieval-augemented generation (RAG) with DIFY/n8n for orchestration, requires significant fine tuning and setup which is not feasible in the timeline. However, I believe this is a more robust approach.

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

    Outputs:
      - Reports:
        - `output/report.html`
        - `output/report.md`
      - Individual plots: `output/plots/`
      - Logs: `output/logs/`

5. Test (for DEVS)

    Test pipelines

    ```bash
    make test
    ```
