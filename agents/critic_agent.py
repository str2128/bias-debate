import anthropic
from prompts.prompts import CRITIC_PROMPT


def critique_argument(client: anthropic.Anthropic, argument: str, debater_label: str) -> str:
    """
    Analyses an argument for bias and logical fallacies.

    Args:
        client: Anthropic client instance
        argument: The argument text to critique
        debater_label: Human-readable label e.g. "Debater A" for logging

    Returns:
        Structured critique as plain text
    """
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=400,
        system=CRITIC_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Please analyse the following argument from {debater_label}:\n\n{argument}",
            }
        ],
    )
    return message.content[0].text
