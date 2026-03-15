"""
runner.py — Orchestrates a single full debate run.

One run = one topic + one bias type + one intensity level.
Calls agents in sequence: biased -> unbiased -> critic x2 -> judge.
Returns a result dict ready to be saved as JSON.
"""

import time
import anthropic

from agents.biased_agent import get_biased_argument
from agents.unbiased_agent import get_unbiased_argument
from agents.critic_agent import critique_argument
from agents.judge_agent import judge_debate
from debate.topics import TOPICS


def run_debate(
    client: anthropic.Anthropic,
    topic_key: str,
    bias_type: str,
    intensity: str,
    blind: bool = False,
    verbose: bool = True,
) -> dict:
    """
    Runs a full debate and returns the complete result dict.

    Args:
        client: Anthropic client instance
        topic_key: Key into TOPICS dict e.g. "social_media"
        bias_type: One of the bias types in BIAS_PROMPTS
        intensity: "mild", "strong", or "none"
        blind: If True, judge sees only arguments (no critic analyses)
        verbose: Print progress to stdout

    Returns:
        Result dict containing all arguments, critiques, verdict, and metadata
    """
    topic = TOPICS[topic_key]
    judge_mode = "blind" if blind else "informed"

    if verbose:
        print(f"\n{'='*60}")
        print(f"Topic:      {topic['name']}")
        print(f"Bias type:  {bias_type}")
        print(f"Intensity:  {intensity}")
        print(f"Judge mode: {judge_mode}")
        print(f"{'='*60}")

    # Step 1: Biased debater argues pro position
    if verbose:
        print("  [1/4] Biased debater generating argument...")
    argument_a = get_biased_argument(client, topic["pro_position"], bias_type, intensity)
    time.sleep(1)  # Respect rate limits

    # Step 2: Unbiased debater argues con position
    if verbose:
        print("  [2/4] Unbiased debater generating argument...")
    argument_b = get_unbiased_argument(client, topic["con_position"])
    time.sleep(1)

    # Step 3: Critic analyses both arguments (always run, even in blind mode,
    # so we can compare critic detection rate across conditions)
    if verbose:
        print("  [3/4] Critic analysing both arguments...")
    critique_a = critique_argument(client, argument_a, "Debater A")
    time.sleep(1)
    critique_b = critique_argument(client, argument_b, "Debater B")
    time.sleep(1)

    # Step 4: Judge evaluates the debate (blind or informed)
    if verbose:
        print(f"  [4/4] Judge evaluating debate ({judge_mode})...")
    verdict = judge_debate(
        client,
        topic_name=topic["name"],
        argument_a=argument_a,
        argument_b=argument_b,
        critique_a=critique_a,
        critique_b=critique_b,
        blind=blind,
    )

    # Ground truth: debater_A is always the biased one (except when bias_type=="none")
    ground_truth_winner = "debater_B" if bias_type != "none" else None
    judge_correct = (verdict.get("winner") == ground_truth_winner) if ground_truth_winner else None

    result = {
        "metadata": {
            "topic_key": topic_key,
            "topic_name": topic["name"],
            "motion": topic["motion"],
            "bias_type": bias_type,
            "intensity": intensity,
            "judge_mode": judge_mode,
            "ground_truth_winner": ground_truth_winner,
            "judge_correct": judge_correct,
        },
        "arguments": {
            "debater_a": argument_a,
            "debater_b": argument_b,
        },
        "critiques": {
            "debater_a": critique_a,
            "debater_b": critique_b,
        },
        "verdict": verdict,
    }

    if verbose:
        winner = verdict.get("winner", "unknown")
        correct = "CORRECT" if judge_correct else ("WRONG" if judge_correct is False else "N/A")
        print(f"\n  Judge picked: {winner} | Ground truth: {ground_truth_winner} | {correct}")
        print(f"  Confidence: {verdict.get('confidence', '?')}/10")

    return result
