# Operators and precedence

This page lists every operator and symbol in Cella, how tightly each one binds, which ones records and enums can declare for their own values, and where each is explained. [Operators](operators.md) covers declaring them.

## Precedence

From tightest to loosest. Operators in one item have the same precedence.

1. Postfix `.`, `()`, `[]` and `?`, left to right.
2. Prefix `-`, `+`, `!`, `~`, `*`, `@`, `own`, `mut`, `imm` and `atomic`, right to left.
3. `*`, `/`, `%` and `*%`, left to right.
4. `+`, `-`, `+%` and `-%`, left to right.
5. `<<`, `>>`, `<<<` and `>>>`, left to right.
6. `&`, left to right.
7. `^`, left to right.
8. `|`, left to right.
9. `<`, `<=`, `>` and `>=`, chained.
10. `is`, which doesn't chain.
11. `==` and `!=`, chained.
12. `&&`, left to right.
13. `||`, left to right.
14. `=` and the compound assignments, right to left.

Unlike C, the bitwise operators `&`, `^` and `|` bind tighter than comparisons, so a mask test needs no parentheses. Shifts bind looser than `+` and `-`, as in C:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
main: fun
{
	val flags = 0b0110
	val mask = 0b0100
	printf("%d\n", flags & mask == mask)
	printf("%d\n", 1 | 2 == 3)
	printf("%d\n", 1 + 2 << 1)
}
```

```output
1
1
6
```

`flags & mask == mask` is `(flags & mask) == mask`, and `1 | 2 == 3` is `(1 | 2) == 3`.

### Chained comparisons

A run of `<`, `<=`, `>` and `>=` is one chained comparison: `a < b <= c` means `a < b && b <= c`, with `b` evaluated once. `==` and `!=` chain the same way among themselves. A chain stops at the first comparison that's false:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
trace: fun(value: i32) -> i32
{
	printf("[%d]", value)
	ret value
}

main: fun
{
	printf(" %d\n", 1 < trace(5) <= 10)
	printf(" %d\n", trace(3) < trace(2) < trace(1))
	printf(" %d\n", 2 == 2 != 3)
}
```

```output
[5] 1
[3][2] 0
 1
```

[Numbers](numbers.md#comparisons) covers comparisons and their typing rules.

### Pattern tests

`is` sits between the comparisons and the equality operators. Its left side can be a comparison or arithmetic, and the result can be compared with `==`:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Shape: enum
{
	circle(radius: f64)
	square(side: f64)
}

main: fun
{
	val a = Shape.circle(1.0)
	val b = Shape.square(2.0)
	val count = 4
	printf("%d\n", a is circle(_) == b is circle(_))
	printf("%d\n", count + 1 is 5)
}
```

```output
0
1
```

### Assignment

Assignment binds loosest and groups right to left, so `a = b = 5` stores 5 in `b` and then in `a`:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
main: fun
{
	var a = 0
	var b = 0
	a = b = 5
	printf("%d %d\n", a, b)
}
```

```output
5 5
```

### Operators and line breaks

A new line ends an expression, so a line can't start with a binary operator, an assignment, `is`, `&&`, `||` or `=>`. Break the line after the operator instead:

```cella error
~ mod example
~
ready: fun(a: bool, b: bool) -> bool
{
	val both = a
		&& b
	ret both
}
~
~ main: fun
~ {
~ }
```

```errors
Cannot start a line with '&&'
```

```cella
~ mod example
~
ready: fun(a: bool, b: bool) -> bool
{
	val both = a &&
		b
	ret both
}
~
~ main: fun
~ {
~ 	val _ = ready(true, false)
~ }
```

`-`, `+`, `*`, `!`, `~` and `@` can start a line, but there they are prefix operators that begin a new statement:

```cella error
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
main: fun
{
	val x = 1
		- 2
	printf("%d\n", x)
}
```

```errors
Cannot use values as statements
```

[Lexical structure](lexical-structure.md) has the full rules for line breaks.

## Arithmetic

[Numbers](numbers.md) covers these and their typing rules. Records and enums can declare all of them.

- `a + b`: addition
- `a - b`: subtraction
- `a * b`: multiplication
- `a / b`: division
- `a % b`: remainder
- `a +% b`, `a -% b`, `a *% b`: wrapping addition, subtraction and multiplication
- `-a`: negation
- `+a`: the value unchanged

## Bitwise and shifts

[Numbers](numbers.md) covers these. Records and enums can declare all of them.

- `a & b`: bitwise and; on `bool`, and without short-circuiting
- `a | b`: bitwise or; on `bool`, or without short-circuiting
- `a ^ b`: bitwise exclusive or; on `bool`, true when the two differ
- `~a`: bitwise not
- `a << b`: shift left
- `a >> b`: shift right; signed types keep the sign bit
- `a <<< b`: rotate left
- `a >>> b`: rotate right

## Comparison and logic

[Numbers](numbers.md#comparisons) covers comparisons, [Bool, char and strings](text.md#bool) the logical operators and [Pattern matching](pattern-matching.md#the-is-operator) `is`. Records and enums can declare the six comparisons, but not `&&`, `||`, `!` or `is`.

- `a == b`, `a != b`: equal, not equal
- `a < b`, `a <= b`, `a > b`, `a >= b`: less than, less than or equal, greater than, greater than or equal
- `a && b`: logical and; `b` runs only when `a` is true
- `a || b`: logical or; `b` runs only when `a` is false
- `!a`: logical not
- `a is p`: tests `a` against the pattern `p`

## Assignment

[Variables](variables.md) covers assignment and [Numbers](numbers.md) the compound forms. Records and enums can declare the compound assignments, but not `=`.

- `a = b`: assignment
- `a += b`, `a -= b`, `a *= b`, `a /= b`, `a %= b`: arithmetic and assign
- `a +%= b`, `a -%= b`, `a *%= b`: wrapping arithmetic and assign
- `a &= b`, `a |= b`, `a ^= b`: bitwise operation and assign
- `a <<= b`, `a >>= b`, `a <<<= b`, `a >>>= b`: shift or rotate and assign

## Memory and access

Records and enums can declare `*` as `*: op(self)` and indexing as `[]: op`, as [Operators](operators.md#indexers) shows, and `?` as `?: op(self)`. The rest can't be declared.

- `@a`: the address of `a` ([Pointers](pointers.md))
- `*a`: the value a pointer points to ([Pointers](pointers.md))
- `a.b`: member access, also through pointers ([Records](records.md))
- `a[i]`: indexing arrays, pointers and strings ([Arrays](arrays.md))
- `f(x)`: a call ([Functions](functions.md))
- `a?`: calls the type's `?: op` member, which gives a value or returns early from the function that uses `a?` ([Operators](operators.md#the-operator))
- `own a`: moves `a` where a plain use wouldn't, such as out of a `mut` parameter or a pointer ([Ownership](ownership.md#moving-values))
- `mut a`, `imm a`: borrows `a` with or without writing ([Parameter modes](parameter-modes.md))
- `atomic ...`: an atomic load, store, update or fence ([Atomics](atomics.md))

## Other symbols

| Symbol | Meaning | Chapter |
| --- | --- | --- |
| `a..b` | The integers from `a` up to but not including `b`, in `for` loops and patterns | [Control flow](control-flow.md), [Pattern matching](pattern-matching.md) |
| `a..=b` | The integers from `a` up to and including `b`, in `for` loops and patterns | [Control flow](control-flow.md), [Pattern matching](pattern-matching.md) |
| `...` | Extra C arguments in an `ext` function, a typed variadic parameter, and spreading arguments | [Variadic functions](variadics.md) |
| `->` | The result type of a function or function type | [Functions](functions.md) |
| `=>` | An expression body, a lambda body or a `match` arm | [Functions](functions.md), [Pattern matching](pattern-matching.md) |
| `:` | Separates a name from what it declares, and a binding from its type | [Lexical structure](lexical-structure.md) |
| `,` | Separates arguments, elements and members on one line | [Lexical structure](lexical-structure.md) |
| `{ }` | A block or body, and a hole in an interpolated string | [Control flow](control-flow.md), [String templates](templates.md) |
| `[ ]` | Array literals, type arguments and indexing | [Arrays](arrays.md), [Generics](generics.md) |

Ranges aren't values: `..` and `..=` appear only in `for` loops and patterns.

## Conditions in `when`

The conditions of `when`, `use when` and `[When."..."]` project tables combine flags with their own small set of operators: `!`, `&&`, `||` and parentheses, with `!` binding tightest and `||` loosest. [Conditional compilation](conditional-compilation.md#conditions) covers them.
