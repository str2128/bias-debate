"""
main.py — CLI entry point for running experiments.

Usage:
    # Single run
    python main.py --topic social_media --bias confirmation --intensity strong

    # All experiments
    python main.py --run-all

    # List available options
    python main.py --list
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import anthropic
from dotenv import load_dotenv

from debate.runner import run_debate
from debate.topics import TOPICS
from prompts.prompts import BIAS_PROMPTS

load_dotenv()

RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)


def get_client() -> anthropic.Anthropic:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set. Copy .env.example to .env and add your key.")
        sys.exit(1)
    return anthropic.Anthropic(api_key=api_key)


def save_result(result: dict, topic_key: str, bias_type: str, intensity: str, blind: bool = False) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    mode_tag = "blind" if blind else "informed"
    filename = RESULTS_DIR / f"{topic_key}_{bias_type}_{intensity}_{mode_tag}_{timestamp}.json"
    with open(filename, "w") as f:
        json.dump(result, f, indent=2)
    print(f"  Saved: {filename}")
    return filename


def run_all_experiments(client: anthropic.Anthropic):
    """Run all topic × bias_type × intensity × judge_mode combinations."""
    experiments = []

    # Biased conditions: all topics × all bias types × both intensities × both judge modes
    for topic_key in TOPICS:
        for bias_type in BIAS_PROMPTS:
            if bias_type == "none":
                continue
            for intensity in ["mild", "strong"]:
                for blind in [False, True]:
                    experiments.append((topic_key, bias_type, intensity, blind))

    # Baseline (no bias) conditions: both judge modes
    for topic_key in TOPICS:
        for blind in [False, True]:
            experiments.append((topic_key, "none", "none", blind))

    total = len(experiments)
    print(f"\nRunning {total} experiments (informed + blind judge conditions)...\n")

    for i, (topic_key, bias_type, intensity, blind) in enumerate(experiments, 1):
        mode = "blind" if blind else "informed"
        print(f"[{i}/{total}] ({mode})", end="")
        result = run_debate(client, topic_key, bias_type, intensity, blind=blind)
        save_result(result, topic_key, bias_type, intensity, blind=blind)

    print(f"\n\nAll {total} experiments complete. Results in: {RESULTS_DIR}/")
    print("Run: python analysis/analyze.py")


def list_options():
    print("\nAvailable topics:")
    for key, topic in TOPICS.items():
        print(f"  {key:15} — {topic['name']}")

    print("\nAvailable bias types:")
    for key in BIAS_PROMPTS:
        print(f"  {key}")

    print("\nIntensities: mild, strong (use 'none' for bias_type=none)\n")


def main():
    parser = argparse.ArgumentParser(description="Bias Debate Experiment Runner")
    parser.add_argument("--topic", choices=list(TOPICS.keys()), help="Debate topic key")
    parser.add_argument("--bias", choices=list(BIAS_PROMPTS.keys()), help="Bias type")
    parser.add_argument("--intensity", choices=["mild", "strong", "none"], help="Bias intensity")
    parser.add_argument("--blind", action="store_true", help="Judge sees only arguments, no critic analyses")
    parser.add_argument("--run-all", action="store_true", help="Run all experiments (both judge modes)")
    parser.add_argument("--list", action="store_true", help="List available options")

    args = parser.parse_args()

    if args.list:
        list_options()
        return

    client = get_client()

    if args.run_all:
        run_all_experiments(client)
    elif args.topic and args.bias and args.intensity:
        result = run_debate(client, args.topic, args.bias, args.intensity, blind=args.blind)
        save_result(result, args.topic, args.bias, args.intensity, blind=args.blind)
    else:
        print("Provide --topic, --bias, --intensity for a single run, or use --run-all")
        print("Try: python main.py --list")
        parser.print_help()


if __name__ == "__main__":
    main()
