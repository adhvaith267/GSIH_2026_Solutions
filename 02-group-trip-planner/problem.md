# Group Trip Planner

## Difficulty

Medium

## Problem Statement

You are given a group of `N` travellers going on a `D`-day trip with `H` usable hours per day.

Each traveller has:

- a daily budget
- an energy level
- a non-empty set of liked interest tags

Each activity has:

- a positive cost per person
- an integer duration in hours
- an integer energy cost
- exactly one interest tag

A chronological list of real-world events can alter the trip while it is in progress.

The planner must:

1. pick the best joint itinerary
2. re-plan the remaining trip whenever the state changes
3. make every decision deterministic and auditable

## Interest Tags

The fixed tag set is:

```text
ADVENTURE
CULTURE
FOOD
NATURE
SHOPPING
NIGHTLIFE
```

## Activity Eligibility

An activity is eligible on day `d` when:

1. it was not chosen on a previous day
2. its tag is not weather-blocked on day `d`

## Fairness Constraints

The feasibility limits are determined by the most restricted active traveller.

### Financial Fairness

```text
sum(cost of selected activities)
    <=
minimum active-traveller budget
```

### Stamina Fairness

```text
sum(energy cost of selected activities)
    <=
minimum active-traveller energy
```

### Time

```text
sum(duration)
    <=
H
```

All three conditions must hold.

## Satisfaction Score

For each selected activity, count the active travellers whose interests contain the activity tag.

```text
satisfaction(S)
=
sum over activities in S of
number of active travellers interested in activity.tag
```

Example:

If three active travellers like `FOOD`, every selected `FOOD` activity contributes `3`.

## Deterministic Decision Rule

Candidate subsets are compared using:

```text
(-satisfaction, total_cost, sorted_activity_ids)
```

The selected subset therefore:

1. maximizes satisfaction
2. minimizes cost when satisfaction ties
3. uses the lexicographically smaller sorted activity-ID list when both satisfaction and cost tie

## Rest Days

A day is:

```text
REST
```

when no valid non-empty subset can be selected, or when the best valid subset is empty.

## State Persistence

Once an activity is selected for a day, it is unavailable on every future day.

## Replanning

When an event occurs, the planner recomputes the affected day and all remaining days.

Previous completed days stay fixed.

## Input Format

```text
N D H
<userLine>          × N
A
<activityLine>      × A
E
<eventLine>        × E
```

### User Line

```text
Alice 100 80 2 ADVENTURE FOOD
```

Fields:

```text
name budget energy k tags...
```

### Activity Line

```text
1 Museum 30 3 20 CULTURE
```

Fields:

```text
id name cost duration energy tag
```

### Event Lines

Supported examples:

```text
WEATHER 2 ADVENTURE
DROP 3 Bob
FATIGUE 2 Alice 50
BUDGET 4 Cara 60
```

Semantics:

- `WEATHER day tag` blocks that tag on the specified day.
- `DROP day name` removes the traveller starting from the specified day.
- `FATIGUE day name energy` sets that traveller's energy starting from the specified day.
- `BUDGET day name budget` changes that traveller's budget starting from the specified day.

## Constraints

```text
3 ≤ N ≤ 10
1 ≤ D ≤ 7
1 ≤ H ≤ 24
1 ≤ A ≤ 20
0 ≤ E ≤ 20
1 ≤ cost, duration, energy, budget ≤ 10000
0 ≤ user.energy ≤ 100
```

Names are alphanumeric strings without spaces.

## Output Format

Initial plan:

```text
=== PLAN ===
Day 1: <ids ...> | cost=<c> satisfaction=<s>
Day 2: ...
```

Then each event:

```text
=== EVENT <i>: <original event line verbatim> ===
Day <day>: ...
...
Day D: ...
```

Activity IDs on each day are printed in ascending order.

An empty plan is:

```text
Day d: REST | cost=0 satisfaction=0
```

There is no trailing whitespace and the entire output ends with one newline.

## Example

Input:

```text
3 2 8
Alice 100 80 2 ADVENTURE FOOD
Bob 80 60 2 CULTURE FOOD
Cara 120 70 2 NATURE FOOD
4
1 Museum 30 3 20 CULTURE
2 Hike 40 5 50 ADVENTURE
3 Cafe 20 2 10 FOOD
4 Park 25 3 15 NATURE
1
WEATHER 2 ADVENTURE
```

One valid initial planning sequence is evaluated using the fairness limits:

```text
budget limit = min(100, 80, 120) = 80
energy limit = min(80, 60, 70) = 60
time limit   = 8
```

The actual selected plan depends on the deterministic optimization rule and remaining activity state.

## Important Requirement

This is not simply a per-day independent knapsack.

The state of earlier days affects the activity pool of later days, and events can alter the optimization state for the remainder of the trip.
