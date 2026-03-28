# Lab 2: pandas Filtering and Aggregation

Objectives:
- Filter event data for high-latency interactions.
- Group by event type and compute counts.
- Compute average latency.

Task:
1. Open `datasets/events.csv`.
2. In `assessments/task2/solution.py`, inspect `mean` and `count_by_key`.
3. Add a helper function called `high_latency(rows, threshold)` that returns rows above threshold.
4. Run `opencourse test test-task2` until all checks pass.

Discussion:
- Why is filtering before aggregation useful for scale?
