import anthropic
from prompts.prompts import UNBIASED_PROMPT


def get_unbiased_argument(client: anthropic.Anthropic, position: str) -> str:
    """
    Returns a clean, unbiased argument for the given position.

    Args:
        client: Anthropic client instance
        position: The debate position to argue (e.g. topic["con_position"])
    """
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=600,
        system=UNBIASED_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Here is your debate position:\n\n{position}\n\n"
                    "Make your argument in 3-4 paragraphs. Be clear and balanced."
                ),
            }
        ],
    )
    return message.content[0].text
