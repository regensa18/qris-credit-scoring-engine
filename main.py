import sys
import json

from domain.pipeline import ScoringPipeline
from adapters.input.csv_input import CsvInput
from adapters.validation.basic_validator import BasicValidator
from adapters.features.statistical_features import StatisticalFeatureExtractor
from adapters.reasoning.rule_based_engine import RuleBasedEngine
from adapters.output.json_output import JsonOutput
from config.loader import load_config

