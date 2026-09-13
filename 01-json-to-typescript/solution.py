import sys
import json


class N:
    """Merged representation of an object in the inferred type tree."""

    def __init__(self):
        self.c = 0          # Number of parent objects containing this node/field.
        self.f = {}         # Child fields.
        self.t = set()      # Primitive/category types observed.

        self.o = None       # Merged nested object.
        self.a = None       # Merged array-element information.


def tp(x):
    """Map a JSON primitive to its TypeScript type."""
    if x is None:
        return "null"

    if type(x) == bool:
        return "boolean"

    if type(x) in (int, float):
        return "number"

    return "string"


def go(cur, obj):
    """
    Merge one JSON object into the current type-tree node.
    """
    cur.c += 1

    for k in obj:
        v = obj[k]

        if k not in cur.f:
            cur.f[k] = N()

        ch = cur.f[k]
        ch.c += 1

        if type(v) == dict:
            ch.t.add("object")

            if ch.o is None:
                ch.o = N()

            go(ch.o, v)

        elif type(v) == list:
            ch.t.add("array")

            if ch.a is None:
                ch.a = N()

            arr = ch.a

            for z in v:
                if type(z) == dict:
                    arr.t.add("object")

                    if arr.o is None:
                        arr.o = N()

                    go(arr.o, z)
                else:
                    arr.t.add(tp(z))

        else:
            ch.t.add(tp(v))


def solve(name, raw):
    """
    Build the merged tree and generate the deterministic TypeScript output.
    """
    data = json.loads(raw)

    root = N()

    # Merge every top-level object into the same root node.
    for x in data:
        go(root, x)

    # Interface names used so far. The supplied root name is reserved first.
    used = set([name])

    # Maps the identity of each object node to its generated interface name.
    mp = {}

    # All generated interfaces.
    allv = []

    mp[id(root)] = name
    allv.append((name, root))

    def nxt(s):
        """
        Generate a deterministic interface name from a field name.
        """
        s = s[0].upper() + s[1:]

        if s not in used:
            used.add(s)
            return s

        i = 2

        while s + str(i) in used:
            i += 1

        val = s + str(i)
        used.add(val)
        return val

    def dfs(node):
        """
        Assign names using depth-first traversal with sorted keys.
        """
        ks = sorted(node.f)

        for k in ks:
            ch = node.f[k]

            # Direct nested object.
            if ch.o is not None:
                nm = nxt(k)

                mp[id(ch.o)] = nm
                allv.append((nm, ch.o))

                dfs(ch.o)

            # Object elements inside an array.
            if ch.a is not None and ch.a.o is not None:
                nm = nxt(k)

                mp[id(ch.a.o)] = nm
                allv.append((nm, ch.a.o))

                dfs(ch.a.o)

    # Assign all interface names before emitting any interface body.
    dfs(root)

    # Interfaces are emitted in case-sensitive ASCII order by name.
    allv.sort(key=lambda x: x[0])

    out = []

    for nm, node in allv:
        keys = sorted(node.f)

        if not keys:
            out.append(f"export interface {nm} {{}}")
            continue

        cur = [f"export interface {nm} {{"]

        for k in keys:
            ch = node.f[k]
            vals = []

            # Direct object type.
            if ch.o is not None:
                vals.append(mp[id(ch.o)])

            # Array type.
            if ch.a is not None:
                arr = []

                if ch.a.o is not None:
                    arr.append(mp[id(ch.a.o)])

                for q in ch.a.t:
                    if q != "object":
                        arr.append(q)

                arr = sorted(set(arr))

                if not arr:
                    vals.append("unknown[]")

                elif len(arr) == 1:
                    vals.append(arr[0] + "[]")

                else:
                    vals.append("(" + " | ".join(arr) + ")[]")

            # Primitive/null types observed directly on the field.
            for q in ch.t:
                if q != "object" and q != "array":
                    vals.append(q)

            vals = sorted(set(vals))
            typ = " | ".join(vals)

            # A property is optional if it was absent from at least one
            # object merged into the current parent node.
            opt = ""

            if ch.c != node.c:
                opt = "?"

            cur.append(f"  {k}{opt}: {typ};")

        cur.append("}")
        out.append("\n".join(cur))

    return "\n\n".join(out)


def main():
    s = sys.stdin.read().splitlines()

    t = int(s[0])
    p = 1

    ans = []

    for _ in range(t):
        nm = s[p]
        p += 1

        raw = s[p]
        p += 1

        ans.append(solve(nm, raw))

    print("\n---\n".join(ans))


main()
