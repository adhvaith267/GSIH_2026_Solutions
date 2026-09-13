import sys
from collections import defaultdict


TAG_INDEX = {
    "ADVENTURE": 0,
    "CULTURE": 1,
    "FOOD": 2,
    "NATURE": 3,
    "SHOPPING": 4,
    "NIGHTLIFE": 5,
}


def better(a, b):
    """
    Compare two candidate plans.

    Priority:
    1. Higher satisfaction
    2. Lower cost
    3. Lexicographically smaller sorted activity-ID tuple
    """
    if a is None:
        return b

    if b is None:
        return a

    if a[0] != b[0]:
        return a if a[0] > b[0] else b

    if a[1] != b[1]:
        return a if a[1] < b[1] else b

    if a[2] != b[2]:
        return a if a[2] < b[2] else b

    return a


def fmt_day(day, ids, cost, sat):
    """Format one day exactly as required by the output specification."""
    if not ids:
        return f"Day {day}: REST | cost=0 satisfaction=0"

    return (
        f"Day {day}: "
        f"{' '.join(map(str, ids))} | "
        f"cost={cost} satisfaction={sat}"
    )


def read_input():
    """Read and parse the entire trip instance."""
    lines = sys.stdin.read().splitlines()

    p = 0

    N, D, H = map(int, lines[p].split())
    p += 1

    users = []

    for _ in range(N):
        parts = lines[p].split()
        p += 1

        name = parts[0]
        budget = int(parts[1])
        energy = int(parts[2])
        k = int(parts[3])

        tags = set(parts[4:4 + k])

        users.append({
            "name": name,
            "budget": budget,
            "energy": energy,
            "tags": tags,
            "active": True,
        })

    A = int(lines[p])
    p += 1

    activities = []

    for _ in range(A):
        parts = lines[p].split()
        p += 1

        activities.append({
            "id": int(parts[0]),
            "name": parts[1],
            "cost": int(parts[2]),
            "duration": int(parts[3]),
            "energy": int(parts[4]),
            "tag": parts[5],
        })

    E = int(lines[p])
    p += 1

    events = lines[p:p + E]

    return N, D, H, users, activities, events


def precompute_half(items):
    """
    Precompute aggregate information for every subset of one activity half.
    """
    m = len(items)
    total = 1 << m

    cost = [0] * total
    energy = [0] * total
    duration = [0] * total
    ids = [()] * total

    # Six interest-tag counts per subset.
    tag_counts = [[0] * 6 for _ in range(total)]

    for mask in range(1, total):
        # Extract the least-significant set bit.
        lb = mask & -mask
        i = lb.bit_length() - 1
        prev = mask ^ lb

        cost[mask] = cost[prev] + items[i]["cost"]
        energy[mask] = energy[prev] + items[i]["energy"]
        duration[mask] = duration[prev] + items[i]["duration"]

        ids[mask] = tuple(sorted(
            ids[prev] + (items[i]["id"],)
        ))

        tag_counts[mask] = tag_counts[prev][:]

        tag_counts[mask][
            TAG_INDEX[items[i]["tag"]]
        ] += 1

    return {
        "items": items,
        "cost": cost,
        "energy": energy,
        "duration": duration,
        "ids": ids,
        "tag_counts": tag_counts,
        "total": total,
    }


def subset_satisfaction(counts, weights):
    """Convert a subset's tag counts into its total group satisfaction."""
    return sum(counts[i] * weights[i] for i in range(6))


def choose_day(
    day,
    users,
    weather,
    used_ids,
    H,
    left_half,
    right_half,
):
    """
    Find the deterministic best feasible subset for one day.

    Meet-in-the-middle is used because there can be up to 20 activities.
    """
    active = [u for u in users if u["active"]]

    if not active:
        return (0, 0, ())

    # The weakest traveller determines the daily fairness limits.
    budget_limit = min(u["budget"] for u in active)
    energy_limit = min(u["energy"] for u in active)

    # Precompute the satisfaction contribution of each interest tag.
    weights = [0] * 6

    for u in active:
        for t in u["tags"]:
            weights[TAG_INDEX[t]] += 1

    blocked = weather.get(day, set())

    # Mark unusable activities in each half.
    left_forbidden = 0

    for i, it in enumerate(left_half["items"]):
        if it["id"] in used_ids or it["tag"] in blocked:
            left_forbidden |= 1 << i

    right_forbidden = 0

    for i, it in enumerate(right_half["items"]):
        if it["id"] in used_ids or it["tag"] in blocked:
            right_forbidden |= 1 << i

    # Collect valid left-half subsets.
    left_valid = []

    for mask in range(left_half["total"]):
        if mask & left_forbidden:
            continue

        d = left_half["duration"][mask]

        if d > H:
            continue

        cL = left_half["cost"][mask]
        eL = left_half["energy"][mask]

        if cL > budget_limit or eL > energy_limit:
            continue

        sat = subset_satisfaction(
            left_half["tag_counts"][mask],
            weights,
        )

        left_valid.append((
            cL,
            eL,
            d,
            sat,
            left_half["ids"][mask],
        ))

    # Collect valid right-half subsets.
    right_valid = []

    for mask in range(right_half["total"]):
        if mask & right_forbidden:
            continue

        d = right_half["duration"][mask]

        if d > H:
            continue

        cR = right_half["cost"][mask]
        eR = right_half["energy"][mask]

        if cR > budget_limit or eR > energy_limit:
            continue

        sat = subset_satisfaction(
            right_half["tag_counts"][mask],
            weights,
        )

        right_valid.append((
            cR,
            eR,
            d,
            sat,
            right_half["ids"][mask],
        ))

    # The empty subset is always a valid baseline candidate.
    best = (0, 0, ())

    # Combine the two halves.
    for cL, eL, dL, sL, idsL in left_valid:
        rem_cost = budget_limit - cL
        rem_energy = energy_limit - eL
        rem_dur = H - dL

        # Left-only candidate.
        cand = (sL, cL, idsL)
        best = better(best, cand)

        # Left + right candidates.
        for cR, eR, dR, sR, idsR in right_valid:
            if cR > rem_cost:
                continue

            if eR > rem_energy:
                continue

            if dR > rem_dur:
                continue

            cand = (
                sL + sR,
                cL + cR,
                tuple(sorted(idsL + idsR)),
            )

            best = better(best, cand)

    return best


def plan_trip(N, D, H, users, activities, events):
    """Compute the initial plan and all event-triggered replans."""
    # Stable activity ordering makes all later decisions deterministic.
    activities = sorted(
        activities,
        key=lambda x: x["id"],
    )

    split = len(activities) // 2

    left_half = precompute_half(
        activities[:split]
    )

    right_half = precompute_half(
        activities[split:]
    )

    weather = defaultdict(set)
    plan = [None] * (D + 1)

    def recompute_from(start_day):
        """
        Keep all days before start_day fixed and replan the suffix.
        """
        if start_day > D:
            return

        used = set()

        # Activities already consumed by fixed earlier days remain unavailable.
        for d in range(1, start_day):
            if plan[d] is not None:
                used.update(plan[d][2])

        # Recompute the affected suffix sequentially.
        for d in range(start_day, D + 1):
            plan[d] = choose_day(
                d,
                users,
                weather,
                used,
                H,
                left_half,
                right_half,
            )

            used.update(plan[d][2])

    out = []

    out.append("=== PLAN ===")

    # Build the initial schedule from day 1.
    recompute_from(1)

    for d in range(1, D + 1):
        sat, cost, ids = plan[d]
        out.append(
            fmt_day(d, ids, cost, sat)
        )

    # Apply events chronologically.
    for i, ev in enumerate(events, 1):
        parts = ev.split()

        etype = parts[0]
        day = int(parts[1])

        if etype == "WEATHER":
            weather[day].add(parts[2])

        elif etype == "DROP":
            name = parts[2]

            for u in users:
                if u["name"] == name:
                    u["active"] = False
                    break

        elif etype == "FATIGUE":
            name = parts[2]
            val = int(parts[3])

            for u in users:
                if u["name"] == name:
                    u["energy"] = val
                    break

        elif etype == "BUDGET":
            name = parts[2]
            val = int(parts[3])

            for u in users:
                if u["name"] == name:
                    u["budget"] = val
                    break

        # The event can only alter the current/future suffix.
        recompute_from(day)

        out.append(
            f"=== EVENT {i}: {ev} ==="
        )

        for d in range(day, D + 1):
            sat, cost, ids = plan[d]
            out.append(
                fmt_day(d, ids, cost, sat)
            )

    return "\n".join(out) + "\n"


if __name__ == "__main__":
    N, D, H, users, activities, events = read_input()
    sys.stdout.write(
        plan_trip(
            N,
            D,
            H,
            users,
            activities,
            events,
        )
    )
