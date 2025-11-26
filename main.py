import os
import sys
from datetime import datetime
from pathlib import Path

from src.utils import utils
from src.utils import logger_util
from src.preprocessor import DataPreprocessor
from src.data_validator import DataValidator
from src.visualiser import Visualizer
from src.llm_engine import LLMEngine
from src.report_builder import ReportBuilder

SYSARG = sys.argv[-1]

def main():
    """
    Main pipeline for automated report generation.
    
    Pipeline stages:
    1. Load configuration
    2. Load and validate data
    3. Generate visualizations
    4. Generate narrative with LLM
    5. Build final report
    """
    # Setup logging
    log_dir = Path("output/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logger_util.setup_logger(
        __name__, 
        log_file=log_dir / f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )
    
    logger.info("=" * 80)
    logger.info("Starting Automated Report Generation Pipeline")
    logger.info("=" * 80)
    
    # STAGE 1: LOAD CONFIGURATION
    logger.info("STAGE 1: Loading configuration")
    try:
        config = utils.load_config(os.path.join("config", "config.yml"))
        # llm_config = utils.load_config(os.path.join("config", "llm_config.yml"))
        logger.info("Configuration loaded successfully")
    except Exception as e:
        logger.critical(f"Configuration loading failed: {e}", exc_info=True)
        sys.exit(1)
    
    # STAGE 2: DATA LOADING & VALIDATION
    logger.info("STAGE 2: Loading and validating data")
    try:
        processor = DataPreprocessor(
            filepath=config['data']['input_path'],
            expected_columns=config['data']['columns']
        )
        df = processor.get_clean_df()
        logger.info(f"Data loaded: {len(df)} rows, {len(df.columns)} columns")
        
        # Validate data quality
        validator = DataValidator(logger)
        validation_report = validator.validate_dataframe(df, config)
        
        if not validation_report['passed']:
            logger.error("Data validation failed with errors:")
            for error in validation_report['errors']:
                logger.error(f"  - {error}")
            sys.exit(1)
        
        if validation_report['warnings']:
            logger.warning("Data validation warnings:")
            for warning in validation_report['warnings']:
                logger.warning(f"  - {warning}")
        
        # Apply business rules
        df = validator.enforce_business_rules(df)
        
        # Extract context for LLM
        data_summary = processor.extract_llm_context(df)
        # print(data_summary)
        logger.info("Data context extracted for LLM")
        logger.debug(f"Data summary:\n{data_summary}")
        
    except Exception as e:
        logger.error(f"Data processing failed: {e}", exc_info=True)
        sys.exit(1)
    
    # STAGE 3: VISUALIZATION GENERATION
    logger.info("STAGE 3: Generating visualizations")
    try:
        viz = Visualizer(df)
        plots_dict = viz.generate_plots()
        logger.info(f"Generated {len(plots_dict)} visualizations")
    except Exception as e:
        logger.error(f"Visualization generation failed: {e}", exc_info=True)
        sys.exit(1)
    
    if SYSARG == 'test':
        print(data_summary)
        print('Not generating report')
    else:
        # STAGE 4: LLM NARRATIVE GENERATION
        logger.info("STAGE 4: Generating narrative with LLM")
        try:
            llm = LLMEngine(config_path="config/llm_config.yml")
            report_narrative = llm.generate_report_narrative(data_summary)
            # print(report_narrative)
            logger.info(f"Generated narrative: {len(report_narrative)} characters")
            logger.debug(f"Narrative preview: {report_narrative[:200]}...")
        except Exception as e:
            logger.error(f"LLM generation failed: {e}", exc_info=True)
            sys.exit(1)
        
        # STAGE 5: REPORT ASSEMBLY
        logger.info("STAGE 5: Building final report")
        try:
            report_builder = ReportBuilder(output_dir="output")
            
            # Prepare metadata
            metadata = {
                'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'model': llm.model,
                'data_source': config['data']['input_path'],
                'total_records': len(df),
                'validation_status': 'Passed' if validation_report['passed'] else 'Failed with warnings'
            }
            
            # Build HTML report
            html_path = report_builder.build_html_report(
                narrative=report_narrative,
                plots=plots_dict,
                metadata=metadata,
                output_filename=Path(config['data']['output_path']).name
            )
            logger.info(f"HTML report saved to: {html_path}")
            
            # Also save raw markdown for version control
            md_path = report_builder.save_markdown(
                narrative=report_narrative,
                output_filename="report.md"
            )
            logger.info(f"Markdown report saved to: {md_path}")
            
        except Exception as e:
            logger.error(f"Report building failed: {e}", exc_info=True)
            sys.exit(1)
        
        # COMPLETION
        logger.info("=" * 80)
        logger.info("Pipeline completed successfully!")
        logger.info(f"Final report: {html_path}")
        logger.info("=" * 80)
        
        return html_path


if __name__ == "__main__":
    try:
        output_path = main()
        print(f"\nReport generated successfully: {output_path}\n")
    except KeyboardInterrupt:
        print("\nPipeline interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\nPipeline failed: {e}")
        sys.exit(1)