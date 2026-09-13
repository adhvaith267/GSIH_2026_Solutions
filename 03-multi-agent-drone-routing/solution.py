import json
import sys
import math
import heapq


BATTERY_CAPACITY = 500.0
CHARGE_RATE = 2.0
EPS = 1e-9

# Bounds used by the deterministic greedy batching strategy.
MAX_SCAN = 80
MAX_PER_TRIP = 8
MAX_STATIONS_CHECK = 5


def dist(a, b):
    """Euclidean distance between two points."""
    return math.hypot(
        a[0] - b[0],
        a[1] - b[1],
    )


# ============================================================
# Geometry
# ============================================================

def rect_segment_interval(a, b, rect):
    """
    Return the parameter interval [u1, u2] for which the
    segment A + u(B-A) lies inside the rectangle.

    Returns None if the segment does not intersect the rectangle.
    """
    (xmin, ymin), (xmax, ymax) = rect

    x1, y1 = a
    x2, y2 = b

    dx = x2 - x1
    dy = y2 - y1

    p = [-dx, dx, -dy, dy]
    q = [
        x1 - xmin,
        xmax - x1,
        y1 - ymin,
        ymax - y1,
    ]

    u1, u2 = 0.0, 1.0

    for i in range(4):
        if abs(p[i]) < EPS:
            if q[i] < 0:
                return None
        else:
            t = q[i] / p[i]

            if p[i] < 0:
                u1 = max(u1, t)
            else:
                u2 = min(u2, t)

    if u1 > u2 + EPS:
        return None

    return max(0.0, u1), min(1.0, u2)


def circle_segment_interval(a, b, center, radius):
    """
    Return the segment parameter interval that lies inside a circle.
    """
    ax, ay = a
    bx, by = b
    cx, cy = center

    dx = bx - ax
    dy = by - ay

    A = dx * dx + dy * dy

    if A < EPS:
        if math.hypot(ax - cx, ay - cy) <= radius + EPS:
            return (0.0, 0.0)

        return None

    fx = ax - cx
    fy = ay - cy

    B = 2.0 * (fx * dx + fy * dy)
    C = fx * fx + fy * fy - radius * radius

    disc = B * B - 4.0 * A * C

    if disc < -EPS:
        return None

    disc = math.sqrt(
        max(0.0, disc)
    )

    t1 = (-B - disc) / (2.0 * A)
    t2 = (-B + disc) / (2.0 * A)

    lo = max(
        0.0,
        min(t1, t2),
    )

    hi = min(
        1.0,
        max(t1, t2),
    )

    if lo <= hi + EPS:
        return lo, hi

    return None


def nfz_interval(a, b, nfz):
    """Return the geometric intersection interval for an NFZ."""
    if nfz["shape"] == "circle":
        return circle_segment_interval(
            a,
            b,
            nfz["center"],
            nfz["radius"],
        )

    return rect_segment_interval(
        a,
        b,
        nfz["corners"],
    )


def merge_intervals(intervals):
    """Merge overlapping time intervals."""
    if not intervals:
        return []

    intervals.sort()

    out = [
        list(intervals[0])
    ]

    for s, e in intervals[1:]:
        if s <= out[-1][1] + EPS:
            out[-1][1] = max(
                out[-1][1],
                e,
            )
        else:
            out.append([s, e])

    return [
        (s, e)
        for s, e in out
    ]


# ============================================================
# Temporal NFZ helpers
# ============================================================

def safe_depart_time(a, b, start_t, nfzs):
    """
    Find the earliest departure time such that traversing the
    straight segment A -> B does not intersect an active NFZ.

    Waiting itself consumes no battery.
    """
    if not nfzs:
        return start_t

    d = dist(a, b)

    if d < EPS:
        return start_t

    forbidden = []

    for z in nfzs:
        # NFZ has already expired before the current time.
        if float(z["T_end"]) < start_t - EPS:
            continue

        inter = nfz_interval(
            a,
            b,
            z,
        )

        if inter is None:
            continue

        u1, u2 = inter

        # The drone reaches the segment positions at times:
        # start_t + u*d.
        s = float(z["T_start"]) - u2 * d
        e = float(z["T_end"]) - u1 * d

        if e >= s - EPS:
            forbidden.append(
                (s, e)
            )

    if not forbidden:
        return start_t

    forbidden = merge_intervals(
        forbidden
    )

    t = float(start_t)

    for s, e in forbidden:
        if t < s - EPS:
            break

        if t <= e + EPS:
            # Small epsilon moves the departure safely beyond
            # the forbidden interval.
            t = e + 1e-6

    return t


def point_in_nfz(pt, z):
    """Check whether a point lies inside an NFZ."""
    x, y = pt

    if z["shape"] == "circle":
        cx, cy = z["center"]
        r = z["radius"]

        return (
            (x - cx) ** 2
            + (y - cy) ** 2
            <= r * r + EPS
        )

    (xmin, ymin), (xmax, ymax) = z["corners"]

    return (
        xmin - EPS <= x <= xmax + EPS
        and ymin - EPS <= y <= ymax + EPS
    )


def point_safe_at_time(pt, t, nfzs):
    """Check whether a point is safe at the specified time."""
    if not nfzs:
        return True

    t_f = float(t)

    for z in nfzs:
        if (
            float(z["T_start"]) - EPS
            <= t_f
            <= float(z["T_end"]) + EPS
        ):
            if point_in_nfz(pt, z):
                return False

    return True


# ============================================================
# Charging station scheduling
# ============================================================

def can_fit_booking(bookings, slots, s, e):
    """
    Check whether the interval [s, e) can be added without
    exceeding station capacity.
    """
    if not bookings:
        return True

    points = [s, e]

    for a, b in bookings:
        if b <= s + EPS or a >= e - EPS:
            continue

        points.append(
            max(s, a)
        )
        points.append(
            min(e, b)
        )

    points = sorted(
        set(points)
    )

    for i in range(len(points) - 1):
        mid = (
            points[i]
            + points[i + 1]
        ) / 2.0

        active = 0

        for a, b in bookings:
            if a <= mid < b:
                active += 1

        if s <= mid < e:
            active += 1

        if active > slots:
            return False

    return True


def earliest_station_start(
    bookings,
    slots,
    arrival,
    duration,
):
    """Find the earliest station charging start time."""
    if duration <= EPS:
        return arrival

    if not bookings:
        return arrival

    # Every existing booking end is a candidate point at which
    # capacity may become available.
    candidates = sorted(
        {arrival}
        | {
            max(arrival, e)
            for _, e in bookings
            if e >= arrival - EPS
        }
    )

    for t in candidates:
        if can_fit_booking(
            bookings,
            slots,
            t,
            t + duration,
        ):
            return t

    # Fallback: move beyond the latest existing booking.
    t = max(
        arrival,
        max(e for _, e in bookings),
    )

    while not can_fit_booking(
        bookings,
        slots,
        t,
        t + duration,
    ):
        t += 1e-6

    return t


# ============================================================
# Greedy delivery batching
# ============================================================

def choose_batch(remaining, cap):
    """
    Greedily choose a bounded batch of deliveries whose total
    weight is within drone capacity.
    """
    pool = remaining[:MAX_SCAN]

    batch = []
    w = 0.0

    for d in pool:
        if len(batch) >= MAX_PER_TRIP:
            break

        if w + d["weight"] <= cap + EPS:
            batch.append(d)
            w += d["weight"]

    return batch


# ============================================================
# Trip simulation
# ============================================================

def simulate_trip(
    start_time,
    batch,
    drone_cap,
    nfzs,
    stations,
    station_bookings,
    warehouse,
):
    """
    Simulate one complete candidate trip.

    The global solver only commits the trip if this function
    returns a successful simulation object.
    """
    wx, wy = warehouse

    t = float(start_time)
    pos = (wx, wy)

    total_w = sum(
        d["weight"]
        for d in batch
    )

    if total_w > drone_cap + EPS:
        return None

    path = [
        {
            "x": wx,
            "y": wy,
            "t": round(t, 6),
            "action": "PICKUP",
            "delivery_ids": [
                d["id"]
                for d in batch
            ],
        }
    ]

    battery = BATTERY_CAPACITY
    payload = total_w

    energy_used = 0.0
    delivered = []

    for d in batch:
        nxt = (
            d["x"],
            d["y"],
        )

        # Delay departure until the straight segment is temporally safe.
        depart = safe_depart_time(
            pos,
            nxt,
            t,
            nfzs,
        )

        if depart > t + EPS:
            path.append(
                {
                    "x": pos[0],
                    "y": pos[1],
                    "t": round(depart, 6),
                    "action": "WAIT",
                }
            )

        leg = dist(
            pos,
            nxt,
        )

        # Energy depends on the payload carried over this leg.
        need = leg * (
            1.0 + payload
        )

        if need > battery + EPS:
            return None

        battery -= need
        energy_used += need

        t = depart + leg

        if t > float(d["deadline"]) + EPS:
            return None

        path.append(
            {
                "x": nxt[0],
                "y": nxt[1],
                "t": round(t, 6),
                "action": "DELIVER",
                "delivery_id": d["id"],
            }
        )

        delivered.append(d)

        # Payload decreases after the package is delivered.
        payload -= d["weight"]
        pos = nxt

    # First attempt a direct return to the warehouse.
    ret_dist = dist(
        pos,
        warehouse,
    )

    if ret_dist <= battery + EPS:
        dd = safe_depart_time(
            pos,
            warehouse,
            t,
            nfzs,
        )

        arr = dd + ret_dist

        if point_safe_at_time(
            warehouse,
            arr,
            nfzs,
        ):
            if dd > t + EPS:
                path.append(
                    {
                        "x": pos[0],
                        "y": pos[1],
                        "t": round(dd, 6),
                        "action": "WAIT",
                    }
                )

            path.append(
                {
                    "x": wx,
                    "y": wy,
                    "t": round(arr, 6),
                    "action": "RETURN",
                }
            )

            return {
                "path": path,
                "end_time": arr,
                "energy": energy_used + ret_dist,
                "station_use": None,
                "delivered_ids": [
                    d["id"]
                    for d in delivered
                ],
            }

    # If direct return is impossible, evaluate charging stations.
    if not stations:
        return None

    sorted_si = sorted(
        range(len(stations)),
        key=lambda i: dist(
            pos,
            (
                stations[i]["x"],
                stations[i]["y"],
            ),
        ),
    )

    best = None

    for si in sorted_si[:MAX_STATIONS_CHECK]:
        st = stations[si]

        sx, sy = (
            st["x"],
            st["y"],
        )

        slots = int(
            st.get("slots", 1)
        )

        to_st = dist(
            pos,
            (sx, sy),
        )

        if to_st > battery + EPS:
            continue

        dep1 = safe_depart_time(
            pos,
            (sx, sy),
            t,
            nfzs,
        )

        arr1 = dep1 + to_st

        if not point_safe_at_time(
            (sx, sy),
            arr1,
            nfzs,
        ):
            continue

        back = dist(
            (sx, sy),
            warehouse,
        )

        bat_after = (
            battery - to_st
        )

        if bat_after < -EPS:
            continue

        # Charge only enough to safely return to the warehouse.
        charge_time = max(
            0.0,
            back - bat_after,
        ) / CHARGE_RATE

        cstart = earliest_station_start(
            station_bookings[si],
            slots,
            arr1,
            charge_time,
        )

        cend = cstart + charge_time

        dep_back = safe_depart_time(
            (sx, sy),
            warehouse,
            cend,
            nfzs,
        )

        arr_back = (
            dep_back + back
        )

        if not point_safe_at_time(
            warehouse,
            arr_back,
            nfzs,
        ):
            continue

        # Deterministic station tie-breaking:
        # earliest return time, then shorter station distance,
        # then lower station index.
        cand = (
            arr_back,
            to_st + back,
            si,
            dep1,
            arr1,
            cstart,
            cend,
            dep_back,
            back,
            sx,
            sy,
        )

        if best is None or cand < best:
            best = cand

    if best is None:
        return None

    (
        arr_back,
        _,
        si,
        dep1,
        arr1,
        cstart,
        cend,
        dep_back,
        back,
        sx,
        sy,
    ) = best

    if dep1 > t + EPS:
        path.append(
            {
                "x": pos[0],
                "y": pos[1],
                "t": round(dep1, 6),
                "action": "WAIT",
            }
        )

    path.append(
        {
            "x": sx,
            "y": sy,
            "t": round(arr1, 6),
            "action": "CHARGE",
        }
    )

    path.append(
        {
            "x": sx,
            "y": sy,
            "t": round(cstart, 6),
            "action": "WAIT",
        }
    )

    path.append(
        {
            "x": sx,
            "y": sy,
            "t": round(cend, 6),
            "action": "CHARGE_COMPLETE",
        }
    )

    if dep_back > cend + EPS:
        path.append(
            {
                "x": sx,
                "y": sy,
                "t": round(dep_back, 6),
                "action": "WAIT",
            }
        )

    path.append(
        {
            "x": wx,
            "y": wy,
            "t": round(arr_back, 6),
            "action": "RETURN",
        }
    )

    return {
        "path": path,
        "end_time": arr_back,
        "energy": energy_used + to_st + back,
        "station_use": (
            si,
            cstart,
            cend,
        ),
        "delivered_ids": [
            d["id"]
            for d in delivered
        ],
    }


# ============================================================
# Main scheduler
# ============================================================

def solve(
    warehouse,
    drones,
    deliveries,
    nfzs,
    stations,
):
    """
    Schedule deterministic greedy drone trips until either all
    deliveries are completed or no progress is possible.
    """
    # Earlier deadlines get priority; secondary ordering is deterministic.
    remaining = sorted(
        deliveries,
        key=lambda d: (
            d["deadline"],
            -d["weight"],
            d["x"],
            d["y"],
        ),
    )

    drone_states = [
        {
            "id": d["id"],
            "cap": float(
                d["max_payload"]
            ),
            "time": 0.0,
            "path": [],
        }
        for d in drones
    ]

    # (available_time, drone_index)
    heap = [
        (0.0, i)
        for i in range(
            len(drone_states)
        )
    ]

    heapq.heapify(heap)

    # Charging bookings are tracked separately per station.
    station_bookings = [
        []
        for _ in stations
    ]

    max_stall = (
        len(remaining) * 2
        + len(drones)
    )

    stall = 0

    while remaining and heap:
        t_avail, di = heapq.heappop(heap)

        drone = drone_states[di]

        batch = choose_batch(
            remaining,
            drone["cap"],
        )

        if not batch:
            stall += 1

            if stall > max_stall:
                break

            heapq.heappush(
                heap,
                (t_avail, di),
            )

            continue

        success = None

        # If the entire candidate batch fails, retry with smaller
        # prefixes until a feasible trip is found.
        for k in range(
            len(batch),
            0,
            -1,
        ):
            sim = simulate_trip(
                drone["time"],
                batch[:k],
                drone["cap"],
                nfzs,
                stations,
                station_bookings,
                warehouse,
            )

            if sim is not None:
                success = sim
                batch = batch[:k]
                break

        if success is None:
            # Rotate the first undeliverable candidate so another
            # delivery may get a chance to be scheduled.
            remaining.append(
                remaining.pop(0)
            )

            stall += 1

            if stall > max_stall:
                break

            heapq.heappush(
                heap,
                (t_avail, di),
            )

            continue

        stall = 0

        drone["path"].extend(
            success["path"]
        )

        drone["time"] = (
            success["end_time"]
        )

        used = set(
            success["delivered_ids"]
        )

        remaining = [
            d
            for d in remaining
            if d["id"] not in used
        ]

        if success["station_use"] is not None:
            si, cstart, cend = (
                success["station_use"]
            )

            station_bookings[si].append(
                (cstart, cend)
            )

            station_bookings[si].sort()

        heapq.heappush(
            heap,
            (
                success["end_time"],
                di,
            ),
        )

    return [
        {
            "drone_id": ds["id"],
            "path": ds["path"],
        }
        for ds in drone_states
        if ds["path"]
    ]


def main():
    data = json.loads(
        sys.stdin.read()
    )

    ms = data["map_size"]

    warehouse = (
        ms[0] / 2.0,
        ms[1] / 2.0,
    )

    result = solve(
        warehouse,
        data["drones"],
        data["deliveries"],
        data.get(
            "no_fly_zones",
            [],
        ),
        data.get(
            "charging_stations",
            [],
        ),
    )

    print(
        json.dumps(
            {
                "flight_manifest": result
            }
        )
    )


if __name__ == "__main__":
    main()
