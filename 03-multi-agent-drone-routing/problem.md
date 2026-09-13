# Multi-Agent Drone Routing in a Temporal Urban Grid

## Difficulty

Advanced

## 1. Background

Urban logistics have transitioned to autonomous drone fleets.

The city contains dynamic No-Fly Zones (NFZs) that activate and deactivate at specific times due to events such as stadium activity, VIP convoys, or construction.

The objective is to build a routing engine that manages a fleet of drones while navigating these temporal constraints and limited battery resources.

## 2. Problem Statement

You are provided with a 2D coordinate grid representing a city.

Develop a system that assigns and routes a fleet of `N` drones from a central warehouse to complete `M` deliveries.

### Warehouse

Drones start at:

```text
(map_size[0] / 2, map_size[1] / 2)
```

### Drones

A drone can carry multiple packages in one trip if total package weight does not exceed `max_payload`.

### Movement

- All distances are Euclidean.
- Drones fly in straight lines between consecutive path points.
- Speed is 1 distance unit per timestep.
- Drones do not collide with one another.
- Multiple drones may occupy the same coordinates simultaneously.

### Trip Completion

After deliveries, a drone must return to the warehouse or a charging station.

Mid-air stops are prohibited.

## 3. Fixed Constants

```text
Drone speed     = 1 distance unit / timestep
Battery         = 500 energy units
Charge rate     = 2 energy units / timestep
```

## Input Format

The input is a JSON object:

```json
{
  "map_size": [Width, Height],
  "drones": [
    {"id": "drone_1", "max_payload": 1.0},
    {"id": "drone_2", "max_payload": 0.8}
  ],
  "deliveries": [
    {"id": "d1", "x": 20, "y": 30, "weight": 0.3, "deadline": 200}
  ],
  "charging_stations": [
    {"x": 50, "y": 50, "slots": 2}
  ],
  "no_fly_zones": [
    {
      "shape": "circle",
      "center": [80, 80],
      "radius": 15,
      "T_start": 0,
      "T_end": 150
    },
    {
      "shape": "rectangle",
      "corners": [[120, 120], [140, 160]],
      "T_start": 50,
      "T_end": 300
    }
  ]
}
```

## Field Definitions

### `map_size`

```text
[Width, Height]
```

The warehouse is:

```text
(Width / 2, Height / 2)
```

### `drones`

Each drone has:

```text
id
max_payload
```

### `deliveries`

Each delivery has:

```text
id
x
y
weight
deadline
```

### `charging_stations`

Each station has:

```text
x
y
slots
```

`slots` is the number of drones that can charge simultaneously.

### `no_fly_zones`

Two shapes are supported.

Circle:

```json
{
  "shape": "circle",
  "center": [x, y],
  "radius": 15,
  "T_start": 0,
  "T_end": 150
}
```

Rectangle:

```json
{
  "shape": "rectangle",
  "corners": [[x_min, y_min], [x_max, y_max]],
  "T_start": 50,
  "T_end": 300
}
```

## 4. No-Fly Zones

An NFZ is active during its specified time window.

A drone cannot enter or pass through an active NFZ.

NFZs are known in advance.

A previously blocked region can be traversed once the relevant NFZ is inactive.

### Transit Timing

For a segment from `A` to `B`:

```text
d = dist(A, B)
```

A point `P` along the path is reached at:

```text
t0 + dist(A, P)
```

because the drone speed is 1.

If the NFZ is active at that instant, the path is blocked.

If the drone can delay departure until the NFZ is inactive for the corresponding segment interval, it may wait.

### Waiting

Waiting:

- occurs at the current location
- consumes no battery
- allows the drone to resume later when safe

## 5. Energy Model

Energy consumption for each leg is:

```text
E_leg = distance × (1 + current_payload_weight)
```

Payload decreases after each delivery, reducing the energy cost of later legs.

Battery must never become negative.

A trip that cannot safely complete should not be attempted.

## 6. Charging Stations

Charging stations have a limited number of concurrent slots.

If every slot is occupied, a drone must wait.

Charging rate:

```text
2 energy units / timestep
```

A drone only needs enough charge to safely continue; it does not need to return to full capacity.

Whenever a drone returns to the warehouse, it is fully recharged to 500.

## 7. Deliveries and Deadlines

Every delivery has a strict deadline.

A delivery counts only if the drone reaches its exact coordinates at or before the deadline.

A delivery is delivered at most once.

Missed deadlines result in failure for that delivery.

## 8. Multi-Package Trips

The total carried weight must satisfy:

```text
sum(package weights) <= max_payload
```

An example trip is:

```text
Warehouse
   ↓
Delivery A
   ↓
Delivery B
   ↓
Warehouse / Charging Station
```

Delivery order affects battery use because the current payload changes after every drop.

## Output Format

The program produces a JSON flight manifest:

```json
{
  "flight_manifest": [
    {
      "drone_id": "drone_1",
      "path": [
        {
          "x": 50,
          "y": 50,
          "t": 0.0,
          "action": "PICKUP",
          "delivery_ids": ["d1", "d3"]
        },
        {
          "x": 20,
          "y": 30,
          "t": 42.4,
          "action": "DELIVER",
          "delivery_id": "d1"
        },
        {
          "x": 35,
          "y": 60,
          "t": 75.1,
          "action": "DELIVER",
          "delivery_id": "d3"
        },
        {
          "x": 50,
          "y": 50,
          "t": 92.0,
          "action": "RETURN"
        }
      ]
    }
  ]
}
```

## Action Types

```text
PICKUP
DELIVER
CHARGE
CHARGE_COMPLETE
WAIT
WAYPOINT
RETURN
```

- `PICKUP`: package pickup at the warehouse, with `delivery_ids`.
- `DELIVER`: arrival at a delivery coordinate, with `delivery_id`.
- `CHARGE`: arrival at a charging station.
- `CHARGE_COMPLETE`: charging has finished.
- `WAIT`: temporary wait at the current position.
- `WAYPOINT`: intermediate navigation point.
- `RETURN`: return to warehouse or charging station.

## Scoring

The score is:

```text
raw_score =
    (successful_deliveries × 100)
    - (total_energy × 0.1)
    - (makespan × 0.05)
```

Where:

- `successful_deliveries` is the number of deliveries completed on time without violations.
- `total_energy` is the sum of energy consumed over all drone legs.
- `makespan` is the latest timestamp in the entire manifest.

Higher is better.

Invalid solutions score zero.

## Validation Rules

A valid solution must satisfy all of the following:

- each drone path starts with `PICKUP`
- each drone path ends with `RETURN`
- timestamps are monotonically non-decreasing
- flight time equals Euclidean distance because speed is 1
- battery never becomes negative
- payload never exceeds drone capacity
- no segment passes through an active NFZ
- a delivery is counted only at its exact coordinates
- delivery arrival time must be at or before its deadline
- every delivery is delivered at most once
