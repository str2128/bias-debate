import json
import anthropic
from prompts.prompts import JUDGE_PROMPT, JUDGE_PROMPT_BLIND


def judge_debate(
    client: anthropic.Anthropic,
    topic_name: str,
    argument_a: str,
    argument_b: str,
    critique_a: str = None,
    critique_b: str = None,
    blind: bool = False,
    max_retries: int = 3,
) -> dict:
    """
    Judges the debate and returns a structured verdict as a dict.

    Args:
        client: Anthropic client instance
        topic_name: Human-readable topic name for context
        argument_a: Biased debater's argument
        argument_b: Unbiased debater's argument
        critique_a: Critic's analysis of debater A (unused when blind=True)
        critique_b: Critic's analysis of debater B (unused when blind=True)
        blind: If True, judge sees only arguments — no critic analyses
        max_retries: Number of times to retry on JSON parse failure

    Returns:
        Parsed JSON verdict as a Python dict
    """
    if blind:
        system_prompt = JUDGE_PROMPT_BLIND
        user_message = (
            f"Topic: {topic_name}\n\n"
            f"--- DEBATER A'S ARGUMENT ---\n{argument_a}\n\n"
            f"--- DEBATER B'S ARGUMENT ---\n{argument_b}\n\n"
            "Now provide your verdict as JSON."
        )
    else:
        system_prompt = JUDGE_PROMPT
        user_message = (
            f"Topic: {topic_name}\n\n"
            f"--- DEBATER A'S ARGUMENT ---\n{argument_a}\n\n"
            f"--- DEBATER B'S ARGUMENT ---\n{argument_b}\n\n"
            f"--- CRITIC'S ANALYSIS OF DEBATER A ---\n{critique_a}\n\n"
            f"--- CRITIC'S ANALYSIS OF DEBATER B ---\n{critique_b}\n\n"
            "Now provide your verdict as JSON."
        )

    for attempt in range(max_retries):
        message = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=500,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        raw = message.content[0].text.strip()

        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        try:
            verdict = json.loads(raw)
            return verdict
        except json.JSONDecodeError as e:
            if attempt < max_retries - 1:
                print(f"  [judge] JSON parse failed (attempt {attempt + 1}), retrying... Error: {e}")
                user_message += f"\n\nYour previous response could not be parsed as JSON. Please respond with ONLY a valid JSON object."
            else:
                print(f"  [judge] JSON parse failed after {max_retries} attempts. Saving raw response.")
                return {"error": "json_parse_failed", "raw": raw}
