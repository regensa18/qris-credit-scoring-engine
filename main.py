import sys
from config.loader import load_config
from adapters.input.csv_input import CsvInput
from adapters.validation.basic_validator import BasicValidator      # your class name
from adapters.features.statistical_features import StatisticalFeatureExtractor
from adapters.reasoning.rule_based_engine import RuleBasedEngine
from adapters.output.json_output import JsonOutput
from domain.assess import assess_merchant

def build_pipeline(config_path="config.json") -> dict:
    config = load_config(config_path)
    return dict(
        input_port=CsvInput(),
        validator=BasicValidator(config),
        extractor=StatisticalFeatureExtractor(),
        engine=RuleBasedEngine(config["rules"]),
        output=JsonOutput(),
        scoring_cfg=config["scoring"],
    )

def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python main.py <path-to-merchant-csv>")
        sys.exit(1)
    print(assess_merchant(sys.argv[1], **build_pipeline()))

if __name__ == "__main__":
    main()
