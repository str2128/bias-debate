import anthropic
from prompts.prompts import BIAS_PROMPTS


def get_biased_argument(client: anthropic.Anthropic, position: str, bias_type: str, intensity: str) -> str:
    """
    Returns a biased argument for the given position.

    Args:
        client: Anthropic client instance
        position: The debate position to argue (e.g. topic["pro_position"])
        bias_type: One of: confirmation, authority, emotional, statistics, false_balance, none
        intensity: One of: mild, strong (or "none" if bias_type is "none")
    """
    system_prompt = BIAS_PROMPTS[bias_type][intensity]

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=600,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Here is your debate position:\n\n{position}\n\n"
                    "Make your argument in 3-4 paragraphs. Be direct and assertive."
                ),
            }
        ],
    )
    return message.content[0].text
