# OpenCourse Student Guide

This guide walks you through your first Big Data Analytics class using OpenCourse.

## 1. Install OpenCourse

Use one of these:

### Option A: Install from GitHub

```bash
python3 -m pip install "git+https://github.com/steliosot/opencourse.git"
```

### Option B: Update if already installed

```bash
python3 -m pip install --upgrade "git+https://github.com/steliosot/opencourse.git"
```

## 2. Start OpenCourse

In your terminal:

```bash
opencourse
```

You should see:
- OpenCourse banner
- available modules
- current module/session info

## 3. Select the module

Set Big Data Processing as your active module:

```bash
opencourse set module big-data-processing
```

Check it:

```bash
opencourse module current
```

## 4. See your current week

```bash
opencourse learn
```

This shows your Week 1 skills and completion status.

## 5. Run your first class (Week 1)

Follow this order:

### Step 5.1: Intro quiz

```bash
opencourse quiz quiz-intro-data
```

### Step 5.2: Lab 1 (Python + CSV basics)

```bash
opencourse lab lab-csv-basics
```

### Step 5.3: Explore dataset

```bash
opencourse continue
```

This will launch the next pending skill (usually dataset explorer/hint/review depending on progress).

### Step 5.4: Run deterministic checks (Task 1)

```bash
opencourse test test-task1
```

## 6. Get help while working

### Ask concept questions

```bash
opencourse ask "What is the difference between CSV and Parquet?"
```

### Use hints/review via normal progression

```bash
opencourse continue
```

### Check your progress any time

```bash
opencourse progress
```

## 7. Move to next class content (Week 2 / Task 2)

When Week 1 is complete:

```bash
opencourse week start 2
opencourse learn
```

Then do:

```bash
opencourse quiz quiz-pandas-core
opencourse lab lab-pandas-aggregation
opencourse test test-task2
```

## 8. Continue from where you stopped

```bash
opencourse continue
```

This opens your last skill or next pending skill.

## 9. Weekly update routine

At the beginning of each teaching week:

```bash
python3 -m pip install --upgrade "git+https://github.com/steliosot/opencourse.git"
opencourse
opencourse learn
```

## 10. Quick troubleshooting

### Command not found: opencourse

Try:

```bash
python3 -m pip install --upgrade "git+https://github.com/steliosot/opencourse.git"
```

Then restart terminal.

### See all modules

```bash
opencourse module list
```

### Switch module again

```bash
opencourse set module big-data-processing
```

---

You are ready for Class 1.
Start with:

```bash
opencourse
opencourse set module big-data-processing
opencourse learn
```
