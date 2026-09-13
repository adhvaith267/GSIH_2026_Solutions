# JSON → TypeScript Type Generator

## Difficulty

Medium

## Problem Statement

Given a JSON array of objects on `stdin`, output a deterministic TypeScript type declaration to `stdout`.

The output must match the expected answer **character-for-character**, including whitespace, ordering, and newlines.

Use LF (`\n`) line endings.

## Input Format

The input consists of several test cases.

```text
T

RootType
<JSON array>

RootType
<JSON array>

...
```

For each test case:

- The first line is the root interface name.
- The next line is a valid JSON array of objects.
- The JSON array is always on a single line.

### Constraints

- `1 ≤ T ≤ 50`
- `0 ≤ number of objects ≤ 10,000`
- Maximum nesting depth: 10
- Maximum total keys across all objects: 100,000
- JSON is valid.
- The top-level value is always an array.
- Every top-level element is an object.
- Array elements are never arrays themselves.
- Key names start with a lowercase letter and do not naturally generate numeric-suffix collisions.
- The root type name starts with an uppercase letter.
- There are no circular references.

## Output Format

For each test case, output the generated TypeScript declaration.

Consecutive test cases are separated by exactly:

```text
---
```

There is no separator before the first test case or after the last test case.

The entire output ends with exactly one newline.

## Formatting Rules

### Interfaces

Every non-empty interface is emitted as:

```typescript
export interface Name {
  ...
}
```

An empty interface is:

```typescript
export interface Name {}
```

The closing brace is not indented.

### Properties

Each property:

- is on its own line
- is indented by 2 spaces
- ends with `;`
- has `?` when optional
- has exactly one space after `:`

Example:

```typescript
export interface RootType {
  email?: null | string;
  id: number;
  name: string;
}
```

Properties are sorted in case-sensitive ASCII order.

### Primitive Types

```text
string
number
boolean
null
```

### Arrays

A homogeneous array is written as:

```text
string[]
```

A mixed array is written as:

```text
(number | string)[]
```

An empty array with no type information is:

```text
unknown[]
```

### Objects

Nested objects are represented using generated interface names.

### Unions

Union components are sorted using case-sensitive ASCII ordering and joined by:

```text
 | 
```

For example:

```text
number | string
```

and:

```text
Address | null
```

## Interface Naming

The root interface uses the exact supplied root type name.

Every nested interface is named from the immediate parent key:

```text
address    → Address
userProfile → UserProfile
posts      → Posts
```

The transformation is only:

```text
key[0].upper() + key[1:]
```

It is not a full PascalCase conversion.

Nested interfaces are encountered using a depth-first traversal in alphabetical-key order.

### Name Collisions

A global set of used names is maintained.

If a generated name already exists:

```text
Address
Address2
Address3
...
```

The root type name is reserved first.

## Type Inference

Each value maps independently:

| JSON value | TypeScript |
|---|---|
| String | `string` |
| Number | `number` |
| Boolean | `boolean` |
| Null | `null` |
| Object | Named interface |
| Array | Inferred array type |

## Merging

Objects at the same structural path are merged into a single interface.

For example:

```json
[
  {"id": 1, "name": "Alice"},
  {"id": 2},
  {"id": 3, "name": null}
]
```

produces:

```typescript
export interface RootType {
  id: number;
  name?: null | string;
}
```

A key is optional when it is absent from at least one object in the merged set.

A present `null` is not considered absent.

## Mixed Types

A field can contain mixed observed categories.

For example:

```json
[
  {"data": [1, 2, 3]},
  {"data": "raw"}
]
```

produces:

```typescript
export interface RootType {
  data: number[] | string;
}
```

If an array mixes objects and primitives, all object elements at that field are merged into one interface.

Example:

```json
[
  {
    "items": [
      1,
      {"label": "x"},
      "hello"
    ]
  }
]
```

produces a type equivalent to:

```typescript
export interface Items {
  label: string;
}

export interface RootType {
  items: (Items | number | string)[];
}
```

## Interface Ordering

All generated interfaces are sorted by case-sensitive ASCII order.

Exactly one blank line separates adjacent interfaces.

## Important Requirement

The judge performs strict string comparison.

Therefore:

- formatting
- ordering
- optional-property detection
- union ordering
- interface naming
- collision resolution

are all part of the algorithm.
