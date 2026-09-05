# Trainer

**A gym and diet plan that gets reviewed before it reaches you.**

Most plans are written once and handed over. This one gets written, then checked from four different angles — what a doctor would refuse to allow, what a dietitian would insist on, what a coach would notice, and what a person actually eating it would say. Anything that fails gets fixed and re-checked.

You only see the version that survived.

Runs on your laptop. No account, no subscription, no internet needed.

---

## Why this exists

AI chats are good at writing plans that look right. They are not built to check them.

| AI chats tell you | What they cannot know |
|---|---|
| "Eat 2,200 calories a day" | They did not ask your height, your job, or how much you walk, so the number is a starting guess rather than yours. |
| "Here is your personalised plan" | Your name is on top. Underneath is the plan everyone gets. |
| "Breakfast: 2 roti, 3 boiled eggs, salad" | The calories and protein are right. But people don't eat roti with just boiled eggs — there is nothing to eat it with. Nothing told the model that, so it could not know. |
| "12 week programme" | There is no rest week in it. Recovery is not something a text model tracks across twelve weeks. |
| "6 exercises for your calves" | Four need machines your gym may not have. It never asked what is in your gym. |
| "This food helps burn belly fat" | No food does this. It repeated something common on the internet. |

None of this is carelessness. A chat has no way to test its own answer. **So you find out in month three.**

---

## What it checks, and who it checks like

Four review layers run over every plan. They look at different things and they disagree, which is the point.

### 1. What a doctor would stop

| | |
|---|---|
| Refuses to plan at all | Under 18 · pregnant · under 12 weeks after giving birth · over 65 without a doctor's clearance |
| Removes movements | 8 injury patterns mapped to 23 specific exercises, each with the reason it would aggravate |
| Sends you to a clinician | For things a diet genuinely cannot fix, instead of planning around them |
| Flags an injury it does not recognise | Rather than staying silent about it |

### 2. What a dietitian would insist on

| | |
|---|---|
| Protein | A floor that rises with age, and again when you are dieting |
| Protein per meal | There is a point past which more in one sitting stops helping |
| Fat, fibre, water | Minimums, not suggestions |
| Weight loss speed | Capped, because faster costs you muscle |
| Missing nutrients | 5 checks on what your food pattern does not supply, with a food fix before a supplement |
| Food safety | Whether what you carry will still be safe by the time you eat it, based on your weather and storage |

### 3. What a coach would notice

| | |
|---|---|
| Sets per muscle per week | A floor and a ceiling, both moving with your training experience |
| Priority muscles | Get a higher floor, or they were never really a priority |
| Session length | Sets multiplied by how long a set takes in *your* gym, against the time you have |
| Exercise order | Two heavy lifts back to back means the second one is done tired |
| Equipment | An exercise needing a machine you do not have is removed, not suggested |
| Rest weeks | Required, spaced by your age and sleep |

### 4. What you would say

| | |
|---|---|
| Is this a meal | Roti with nothing to eat it with is not breakfast, whatever the numbers say |
| Would you eat it | A day of boiled eggs and plain salad does not survive 24 weeks |
| Is it the same every day | Boredom ends more plans than physiology does |
| Do the foods go together | Correct macros from three unrelated cuisines is not dinner |

### And two rules over the top

**Nothing gets sold to you.** 12 phrases can never appear in a plan — "spot reduce", "boosts testosterone", "burns belly fat", "detox" and others. 19 common claims ship with a straight answer and how strong the evidence is.

**Nothing is left out quietly.** 23 sections are required. If the supplements or the warm-up go missing, the plan is rejected rather than delivered short.

---

## How it runs

```
   You answer 20 questions
            │
            ▼
   A rough plan is written
            │
            ▼
   ┌──▶ All four layers review it
   │        │
   │        ├── nothing wrong ──▶ your document
   │        │
   │        ├── it should refuse ──▶ told to see a doctor, no plan
   │        │
   │        └── problems found
   │                 │
   └────── fixed in severity order
```

There are 8 severity levels. A problem lower down can never be fixed by causing one higher up.

```
1  Refuse             you are pregnant, or your gym has no leg press
2  Food safety        the chicken will spoil before lunch
3  Minimums           not enough protein, not enough sets, losing weight too fast
4  Time and maths     the session does not fit in an hour
5  Is it a meal       roti with nothing to eat it with
6  Spreading protein  all of it in one sitting
7  Boredom            the same food every single day
8  Do you like it     you will not eat this for 24 weeks
```

It will not fix "this is boring" by telling you to carry food that spoils.

---

## What it catches

Real numbers from real plans, and what each one would have done to you.

| The mistake | Why it happened | What it would have cost you |
|---|---|---|
| 1 teaspoon of oil counted in your sabji | A real kitchen uses about 3 | 210 extra calories a day, invisible. Six months of that is losing 5 kg instead of 9. |
| "Glutes are a priority muscle" | Given 10 sets a week; the minimum is 12 | Six months of training glutes and wondering why nothing changed. |
| "60 minute sessions" | Four of five actually needed 71 to 78 minutes | Late for work every day, or quietly skipping the last two exercises. |
| "Diet break in week 12" | Training had its easy weeks at 11 and 18 | Eating more during your hardest week, dieting through your easiest. |
| One calorie formula for everyone | It was the male version | Every woman told to eat 166 calories a day more than she needs. |
| "2 roti, 3 boiled eggs, salad" | Calories and protein both correct | You would have stopped in a week, and blamed yourself. |
| A ranking bug | "This food will spoil" scored as less serious than "this food is boring" | Being told to carry cooked chicken that sits at 30°C for eight hours. |

Every one is now a test. None of them can come back.

---

## What gets personalised

Not a template with your name on it. Nineteen things about you change the numbers:

| About you | What it changes |
|---|---|
| Sex | The calorie formula, healthy body fat range, rest between sets |
| Age | Protein floor, protein per meal, how often you need a rest week, tendon and balance advice |
| Weight and height | Everything downstream of calories |
| Waist measurement | Whether you should be dieting, and the point to stop |
| Hours of sleep | How often you need a rest week, when the diet break comes |
| Years of training | Sets per muscle per week, floor and ceiling |
| Days you can train | The split, and your daily calorie burn |
| Minutes per session | How many exercises actually fit |
| How busy your gym is | How long one set really takes |
| What machines you have | Which exercises are possible at all |
| Injuries | Which movements are removed, and why |
| Muscles you care about | The minimum sets those get |
| Your job | Your calorie burn |
| Daily step count | Your calorie burn |
| Temperature where you keep lunch | What you can safely carry |
| Fridge, cool bag, or nothing | Same |
| Hours before you eat it | Same |
| Which proteins you eat | What the meals are built from |
| How much oil your kitchen uses | Whether your calorie number is real |

### Two people, run through it

| | Man, 30, 80 kg, gym 5 days | Woman, 52, 68 kg, gym 3 days |
|---|---|---|
| Calories a day | 2,695 | 1,795 |
| Protein a day | 152 to 168 g | 129 to 143 g |
| Most protein worth eating in one meal | 32 g | 27 g |
| Sets per muscle per week | 10 to 22 | 6 to 14 |
| Rest week every | 8 weeks | 5 weeks |
| Week to stop dieting | 12 | 8 |
| Fastest safe weight loss | 0.6 kg a week | 0.51 kg a week |
| Exercises removed for injury | 7 | 3 |
| How long one set takes | 200 seconds | 240 seconds |

Same code. No branches for "man" or "woman". Every number comes out of the answers.

---

## Using it in Claude

This is the easiest way. You never open a terminal after the first step.

### Step 1 — get the files onto your computer

**If you have git:**

```bash
git clone https://github.com/rishabhrawat35/diet-workout-plan-as-if-you-were-an-athlete.git
```

**If you don't:** click the green **Code** button at the top of this page, choose **Download ZIP**, and unzip it.

### Step 2 — put it where Claude looks for skills

Claude reads skills from a folder called `.claude/skills` in your home directory. The dot at the front means your computer hides it by default.

**Mac or Linux, in Terminal:**

```bash
mkdir -p ~/.claude/skills
mv diet-workout-plan-as-if-you-were-an-athlete ~/.claude/skills/trainer
```

**Mac, without Terminal:**
1. Open Finder
2. Press **Cmd + Shift + G**
3. Type `~/.claude/skills` and press Enter. If it says the folder does not exist, create a folder called `.claude` in your home folder, and a folder called `skills` inside that.
4. Drag the unzipped folder in
5. Rename it to `trainer`

**Windows:** the folder is `C:\Users\<your name>\.claude\skills\trainer`

### Step 3 — check Claude can see it

Open Claude and type `/` — `trainer` should appear in the list. If it does not, close Claude completely and reopen it.

### Step 4 — ask for a plan

Say any of these:

- "build me a training and diet plan"
- "make me a gym plan, I have 5 days and about an hour"
- "review the diet plan I'm currently following"

### Step 5 — answer the questions

Claude asks 20 things: your measurements, your gym, your injuries, what you eat, where you keep lunch. **Answer honestly rather than aspirationally** — if you will realistically train 4 days, say 4, not 6. Every answer changes the numbers, and "whatever you think" gets you the generic plan you were trying to avoid.

If you do not know one, say so. Claude will ask it a different way rather than guess.

### Step 6 — you get the document

Claude writes the plan, runs all four review layers, fixes what fails, and re-runs until it passes. Then it hands you the finished thing.

**Your answers are saved to a file starting with `private-`, which is set to never upload anywhere.**

---

## What you actually get

**Pages 1 and 2 — what to do.**

- Every exercise, sets and reps, for each day
- Every meal with real quantities: 2 roti, 1 katori dal, 250 ml milk
- Supplements, doses, and what time of day
- All 24 weeks and what changes in each
- What to measure, how often, and what to do when the number moves

**Pages 3 and 4 — why.**

- Where every number came from
- How strong the evidence is behind each rule
- 19 things you have heard about training and diet, and whether they are true
- What a plan cannot fix, and what to see a doctor about

Print the first two pages. The rest is for when you want to check something.

---

## Running it without Claude

Python 3.8 or newer. Nothing to install.

```bash
python3 audit.py  --profile profiles/example-a.json --plan plans/example-a.json
python3 render.py --profile profiles/example-a.json --plan plans/example-a.json \
                  --out example-a-plan.md
```

Copy `profiles/example-a.json`, change the values to yours, save it as `profiles/private-you.json`.

---

## Questions

**Is this another AI fitness app?**
No. There is no AI model inside it. It is arithmetic and a list of rules you can read yourself in an afternoon. Claude is only the part that talks to you.

**Is it safe?**
It refuses to write a plan for anyone under 18, pregnant, less than 12 weeks after giving birth, or over 65 without a doctor's clearance. It removes exercises your injuries rule out, and tells you when something needs a doctor rather than a plan.

**Will it just agree with me?**
It cannot. 12 phrases are blocked outright. If you ask it whether carbs at night make you fat, or whether soy affects testosterone, it gives you the answer and how confident that answer is.

**Do I need to know how to code?**
No, if you use it through Claude. Steps are above.

**Where does my information go?**
Nowhere. There is no internet access anywhere in the code. Your personal file never leaves your computer.

**Will it work with the food I eat?**
The code does not know what Indian food is, or Mexican, or anything else. Food and exercises are in separate list files you can swap. Adding a cuisine means writing a food list, not changing the programme.

**What if my gym only has dumbbells?**
Then it plans around dumbbells. Exercises needing machines you do not have are refused outright rather than suggested and ignored.

---

## What it will never tell you

- That any food, supplement, or eating at a certain time removes fat from one part of your body. Nothing does this.
- That a food grows one specific muscle. Food does not work on one muscle.
- That a supplement raises your testosterone when your level is already normal. None of them do.

Where evidence is weak, it says so, and gives it to you as something to test for a set number of weeks with a way to tell whether it worked.

---
---

# For developers

## Why training and diet are one programme

They change each other:

```
eat less → recover slower → need rest weeks sooner
         → calendar changes → what you eat that week changes
```

Built separately they contradict. An earlier version put the diet break in week 12 and training rest weeks at 11 and 18. Neither half could see the problem, because neither half could see the other.

## Files

| File | What is in it |
|---|---|
| `physio.py` | Calories, protein, recovery, volume, injuries, hormones, the 20 required questions |
| `coherence.py` | Whether a meal is a meal and a session can be done |
| `blocks.py` | The 24 week calendar, and making eating follow training |
| `contract.py` | The 23 sections a plan must have |
| `myths.py` | Answers to 19 claims; 12 phrases that can never be printed |
| `resolve.py` | Severity order, and the review loops |
| `audit.py` | Runs every check |
| `render.py` | Writes the document |
| `SKILL.md` | What Claude follows to run all of it |
| `data/` | Food and exercise lists. Swap these, not the code |

## Two kinds of check

Early versions only asked *is this number allowed*. None asked *is this section even here*. Wrong numbers were caught; missing sections were not. Supplements disappeared between two drafts. The warm-up was never written down.

`contract.py` fixes it: 23 required sections, each with a test that removes it and confirms the plan gets rejected.

## Review loops that cannot get stuck

`resolve.py` settles one severity level, locks it, moves down. A later level cannot reopen an earlier one. Every round must measurably improve the plan, so two fixes that undo each other are rejected rather than repeating. Total work is capped regardless of how the reviewers behave.

The loop takes reviewers as arguments — it does not ship named ones. The four layers above are implemented as rule functions in `physio.py` and `coherence.py`, not as separate agents.

## Tests

```bash
python3 -m unittest discover -p 'test_*.py'   # 67 tests
```

Most exist because something was already broken when it shipped.

## What it does not handle

- Body fat is estimated from a measuring tape, so it is rough.
- Alcohol, eating out, and social meals are not in it.
- Medication and medical conditions are not in it. Thyroid problems, insulin resistance and several common drugs change everything here, and it cannot see any of them.
- How much you like a food is a guess until you replace it with your own rating.

---

**This is not medical advice.** Something that checks arithmetic is not a doctor, a dietitian, or a coach. If a number here disagrees with one your doctor gave you, listen to your doctor.
