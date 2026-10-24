import sys
import json

from domain.pipeline import ScoringPipeline
from adapters.input.csv_input import CsvInput
from adapters.validation.basic_validator import BasicValidator
from adapters.features.statistical_features import StatisticalFeatureExtractor
from adapters.reasoning.rule_based_engine import RuleBasedEngine
from adapters.output.json_output import JsonOutput
from config.loader import load_config

def build_pipeline(config_path: str = "config.json") -> ScoringPipeline:
    config = load_config(config_path)
    return ScoringPipeline(
        input_adapter=CsvInput(),
        validator=BasicValidator(config),
        feature_extractor=StatisticalFeatureExtractor(),
        reasoning_engine=RuleBasedEngine(config),
        output_adapter=JsonOutput(config),
    )

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <path-to-merchant-csv>")
        sys.exit(1)

    pipeline = build_pipeline()
    result = pipeline.run(sys.argv[1])
    print(json.dumps(result, indent=2, ensure_ascii=False))

