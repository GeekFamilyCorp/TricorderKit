---
name: skill-creator
description: Create new skills, modify and improve existing skills, and measure skill performance. Use when users want to create a skill from scratch, edit, or optimize an existing skill, run evals to test a skill, benchmark skill performance with variance analysis, or optimize a skill's description for better triggering accuracy.
---

# Skill Creator

A skill for creating new skills and iteratively improving them.

At a high level, the process of creating a skill goes like this:

- Decide what you want the skill to do and roughly how it should do it
- Write a draft of the skill
- Create a few test prompts and run claude-with-access-to-the-skill on them
- Help the user evaluate the results both qualitatively and quantitatively
  - While the runs happen in the background, draft some quantitative evals if there aren't any. Then explain them to the user.
  - Use the `eval-viewer/generate_review.py` script to show the user the results, and also let them look at the quantitative metrics
- Rewrite the skill based on feedback from the user's evaluation of the results
- Repeat until you're satisfied
- Expand the test set and try again at larger scale

Your job when using this skill is to figure out where the user is in this process and then jump in and help them progress through these stages.

Of course, you should always be flexible and if the user is like "I don't need to run a bunch of evaluations, just vibe with me", you can do that instead.

Then after the skill is done, you can also run the skill description improver, which we have a whole separate script for, to optimize the triggering of the skill.

---

## Communicating with the user

The skill creator is liable to be used by people across a wide range of familiarity with coding jargon. Pay attention to context cues to understand how to phrase your communication. In the default case:

- "evaluation" and "benchmark" are borderline, but OK
- for "JSON" and "assertion" you want to see serious cues from the user that they know what those things are before using them without explaining them

It's OK to briefly explain terms if you're in doubt.

---

## Creating a skill

### Capture Intent

Start by understanding the user's intent. The current conversation might already contain a workflow the user wants to capture (e.g., they say "turn this into a skill"). If so, extract answers from the conversation history first. The user may need to fill the gaps, and should confirm before proceeding.

1. What should this skill enable Claude to do?
2. When should this skill trigger? (what user phrases/contexts)
3. What's the expected output format?
4. Should we set up test cases to verify the skill works?

### Interview and Research

Proactively ask questions about edge cases, input/output formats, example files, success criteria, and dependencies. Wait to write test prompts until you've got this part ironed out.

### Write the SKILL.md

Based on the user interview, fill in these components:

- **name**: Skill identifier
- **description**: When to trigger, what it does. Include both what the skill does AND specific contexts for when to use it. Make descriptions a little "pushy" to combat undertriggering — e.g., "Make sure to use this skill whenever the user mentions X, even if they don't explicitly ask for it."
- **compatibility**: Required tools, dependencies (optional, rarely needed)
- **the rest of the skill**

### Skill Writing Guide

#### Anatomy of a Skill

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter (name, description required)
│   └── Markdown instructions
└── Bundled Resources (optional)
    ├── scripts/    - Executable code for deterministic/repetitive tasks
    ├── references/ - Docs loaded into context as needed
    └── assets/     - Files used in output (templates, icons, fonts)
```

#### Progressive Disclosure

Skills use a three-level loading system:
1. **Metadata** (name + description) - Always in context (~100 words)
2. **SKILL.md body** - In context whenever skill triggers (<500 lines ideal)
3. **Bundled resources** - As needed (unlimited, scripts can execute without loading)

**Key patterns:**
- Keep SKILL.md under 500 lines
- Reference files clearly from SKILL.md with guidance on when to read them
- For large reference files (>300 lines), include a table of contents

---

## Running Evaluations

### Test Prompt Structure

Each test case needs:
- **input**: The user message that should trigger the skill
- **expected_behavior**: What the skill should do (not exact wording)
- **success_criteria**: Measurable checks (contains X, length Y, structure Z)

### Quantitative Evals

For skills with verifiable outputs:
1. Define 5-10 test prompts covering happy path + edge cases
2. Run each through Claude with the skill active
3. Check against success criteria programmatically where possible
4. Track pass rate across iterations

### Qualitative Review

For subjective outputs (writing style, tone, creativity):
1. Show the user 3-5 examples side by side
2. Ask them to rate or rank
3. Identify patterns in what they prefer
4. Update the skill accordingly

---

## Skill Description Optimizer

After the skill body is stable, run the description optimizer to improve triggering accuracy:

1. Generate 20 prompts that SHOULD trigger the skill
2. Generate 20 prompts that should NOT trigger it
3. Test triggering rate on both sets
4. Iterate on the description until you hit >90% correct trigger rate

Focus on:
- Specificity: broad descriptions cause false positives
- Completeness: missing triggers cause false negatives
- Exclusions: "Ne pas activer si" clauses prevent conflicts

---

## Iterating on Existing Skills

When the user provides an existing skill to improve:

1. Read the current SKILL.md
2. Identify the main failure mode(s): undertriggering, overtriggering, wrong output, missing edge cases
3. Propose targeted fixes — don't rewrite everything at once
4. Run evals on the specific failure modes
5. Validate the fix didn't break existing passing cases
6. Update the changelog section
