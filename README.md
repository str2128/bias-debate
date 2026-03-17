# Can LLMs Detect Biased Arguments?

A controlled multi-agent experiment testing whether a judge LLM can reliably detect rhetorical bias in structured debates, and whether providing it with an LLM critic's analysis helps or hinders its judgement.

---

## Research Question

When two LLMs debate a topic — one arguing with injected rhetorical bias, one arguing neutrally — can a third LLM acting as judge correctly identify which debater was biased? And does giving the judge access to a critic's analysis improve or degrade its accuracy?

---

## Built With
This project was designed and developed using [Claude Code](https://claude.ai/code) 
and [Claude Cowork](https://claude.ai) as core development tools, iterating on 
experiment design, debugging, and analysis in real time.

---

## Experimental Design

**Agents:**
- **Biased Debater (A):** Argues a position using one of 5 injected bias types at mild or strong intensity
- **Unbiased Debater (B):** Argues the opposing position using neutral, evidence-based reasoning
- **Critic:** Independently analyzes both arguments for logical flaws and rhetorical tactics
- **Judge:** Evaluates the debate and identifies which debater was biased and what type of bias was used
- **Note** All agents are Claude Opus 4.5 with different system prompts.

**Two judge conditions:**
- **Informed judge:** Receives both arguments + the critic's analysis before deciding
- **Blind judge:** Receives only the raw arguments, no critic input

**Bias types tested:**
| Type | Description |
|---|---|
| Confirmation | Selectively cites supporting evidence, dismisses counterevidence |
| Authority | Over-relies on expert quotes and credentials |
| Emotional | Uses emotionally charged language and appeals to fear/hope |
| Statistics | Misuses or cherry-picks numerical data |
| False balance | Presents fringe positions as equivalent to scientific consensus |

Each bias type was tested at **mild** and **strong** intensity across 3 debate topics, with a no-bias control condition — **66 trials total**.

**Topics:**
- Should social media platforms be regulated by governments?
- Is nuclear energy a viable solution to climate change?
- Does AI create more jobs than it destroys?

---

## Key Findings

### 1. Judge accuracy was high overall,  but for the wrong reasons
The judge correctly identified the biased debater in **93% of trials**. However, failure cases clustered almost exclusively on the nuclear energy topic, where the unbiased debater independently developed a pro-nuclear lean without any prompting, invalidating the unbiased control for that topic. High accuracy reflects **topic-argument alignment** (some positions are empirically easier to defend) as much as genuine bias detection.

### 2. Critic analysis dramatically inflated false positives
The informed judge flagged the unbiased debater as biased in **80% of trials** (24/30). The blind judge flagged the same debater in only **7%** (2/30). The critic pipeline, designed to help the judge, instead over-sensitised it, causing it to interpret minor rhetorical imperfections in the unbiased argument as evidence of bias.

### 3. Verdict accuracy far outpaces explanation accuracy
The judge made the correct verdict 93% of the time but correctly identified the *type* of bias in only **43% of trials**. It is making right decisions for partially wrong reasons — a meaningful limitation for any application requiring interpretable bias detection.

### 4. Critic analysis degrades severity accuracy
The blind judge correctly estimated bias severity in **70%** of cases vs **57%** for the informed judge. The critic's own severity labels introduced noise rather than signal.

### 5. Safety training overrode the statistics/strong bias prompt
For 7 trials, when instructed to fabricate or cherry-pick statistics at strong intensity, the model refused and argued honestly instead. The refusals occurred consistently across all three topics in the statistics/strong condition, and also triggered twice in the ai_jobs/false_balance/strong condition using slightly different wording. The judge correctly awarded the win to the honest arguer in 6 out of 7 cases. This suggests the safety boundary is not a one-off edge case but a reliable limit on strong-intensity fabrication prompts. This is an unintended finding about the limits of bias injection via system prompts, inducing bias rather than having it occur naturally (like with the cases of con arguing models developing pro-nuclear stances).

---

## Project Structure

```
bias-debate/
├── agents/
│   ├── biased_agent.py       # Generates arguments with injected bias (Pro)
│   ├── unbiased_agent.py     # Generates neutral arguments (Con)
│   ├── critic_agent.py       # Critiques both arguments independently
│   └── judge_agent.py        # Evaluates debate (blind or informed)
├── debate/
│   ├── runner.py             # Orchestrates full debate pipeline
│   └── topics.py             # Debate topics and positions
├── prompts/
│   └── prompts.py            # All system prompts (bias types, judge, critic)
├── analysis/
│   ├── analyze.py            # Generates charts and summary statistics
│   └── conclusions.pdf       # Full written conclusions
├── results/                  # JSON output for each trial
├── main.py                   # CLI entrypoint
└── requirements.txt
```

---

## Setup & Usage

```bash
# Clone and install
git clone https://github.com/str2128/bias-debate.git
cd bias-debate
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Add your Anthropic API key
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY=your_key_here

# Run a single debate
python main.py --topic social_media --bias confirmation --intensity strong

# Run the full experiment (66 trials)
python main.py --run-all

# Generate analysis charts and summary
python analysis/analyze.py
```

---

## Requirements

- Python 3.9+
- Anthropic API key (uses `claude-opus-4-5`)
- ~$4–5 in API credits for a full run

---

## Limitations

- Small sample size (n=2–4 per cell) limits statistical power
- Only 3 debate topics; topic-argument alignment confound affects nuclear energy results
- Judge confidence scores clustered in 6–9 range, limiting calibration analysis
- Bias injection via system prompts occassionally has hard limits (safety training overriding strong statistical bias)
