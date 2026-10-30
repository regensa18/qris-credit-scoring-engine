import argparse, datetime, sys
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
    p = argparse.ArgumentParser()
    p.add_argument("path")
    p.add_argument("--as-of", type=datetime.date.fromisoformat, default=None,
                   help="Assessment date YYYY-MM-DD (default: today)")
    args = p.parse_args()
    print(assess_merchant(args.path, as_of=args.as_of or datetime.date.today(), **build_pipeline()))

if __name__ == "__main__":
    main()
