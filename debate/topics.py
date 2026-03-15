"""
topics.py — Debate topics and assigned positions.

Each topic has a pro and con position. The biased debater is always
assigned "pro" and argues in favour; the unbiased debater argues "con".
(You can flip this if you want to test the other direction.)
"""

TOPICS = {
    "social_media": {
        "name": "Social media and teenage mental health",
        "motion": "Social media causes depression and anxiety in teenagers.",
        "pro_position": (
            "Argue IN FAVOUR: social media is a significant cause of depression "
            "and anxiety in teenagers and should be heavily restricted."
        ),
        "con_position": (
            "Argue AGAINST: social media does not straightforwardly cause depression "
            "in teenagers — the evidence is mixed and the relationship is more complex."
        ),
    },
    "nuclear": {
        "name": "Nuclear energy and the green transition",
        "motion": "Nuclear energy should be a central part of the green energy transition.",
        "pro_position": (
            "Argue IN FAVOUR: nuclear energy is essential to reaching net zero and "
            "should be aggressively expanded as part of the green transition."
        ),
        "con_position": (
            "Argue AGAINST: nuclear energy is too slow, costly, and risky to be "
            "a central part of the green energy transition."
        ),
    },
    "ai_jobs": {
        "name": "AI and employment",
        "motion": "AI will create more jobs than it destroys over the next 20 years.",
        "pro_position": (
            "Argue IN FAVOUR: AI will be a net creator of jobs, as previous technological "
            "revolutions have been, and fears of mass unemployment are overblown."
        ),
        "con_position": (
            "Argue AGAINST: AI is fundamentally different from previous automation waves "
            "and will destroy more jobs than it creates over the next 20 years."
        ),
    },
}
