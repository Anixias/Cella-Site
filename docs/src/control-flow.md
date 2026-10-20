# Control flow

Cella's control flow is close to C's: `if` and `else`, `while`, `do ... while`, an endless `loop`, and `for` over ranges and arrays, with `break` and `cont` to leave or restart a loop. Conditions need no parentheses, and a body is a single statement or a block. This chapter covers each form, labels, jumps used as expressions, and blocks.

## `if` and `else`

`if` takes a condition and a body. The condition is any `bool` expression, written without parentheses. The body is the next statement: one statement, usually on the next line and indented, or a block in braces. `else` adds a statement that runs when the condition is false:

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
	val temperature = 31
	if temperature > 30
		printf("hot\n")

	if temperature < 10
	{
		printf("cold\n")
		printf("take a coat\n")
	}
	else
	{
		printf("not cold\n")
	}
}
```

```output
hot
not cold
```

When one branch needs braces, the usual style gives every branch braces, as above.

### `else if`

There is no separate `elif` keyword. `else if` is an `else` whose statement is another `if`, so chains read as they do in C:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
classify: fun(n: i32)
{
	if n < 0
		printf("%d is negative\n", n)
	else if n == 0
		printf("%d is zero\n", n)
	else if n < 10
		printf("%d is small\n", n)
	else
		printf("%d is large\n", n)
}

main: fun
{
	classify(-4)
	classify(0)
	classify(7)
	classify(300)
}
```

```output
-4 is negative
0 is zero
7 is small
300 is large
```

### Conditions

A condition must be a `bool`. Numbers and pointers don't count as true or false on their own, so compare them explicitly:

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
	val count = 3
	if count
		printf("some\n")

	while 1
		printf("forever\n")
}
```

```errors
Cannot convert type 'i32' to 'bool'
Cannot convert type 'integer literal' to 'bool'
```

`&&` and `||` combine conditions, and the right side runs only when it's needed; [Bool, char and strings](text.md) covers them. An `is` test, as in `if shape is circle(val r)`, checks an enum's case and can bind its payload; [Pattern matching](pattern-matching.md) covers it.

### `if` is a statement

`if` doesn't produce a value, and Cella has no `?:` operator. For a value that depends on a condition, use a `match` on the condition:

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
	val a = 4
	val b = 9
	val larger = match a > b { true => a, else => b }
	printf("%d\n", larger)
}
```

```output
9
```

A body that is a single statement can't be a declaration, since the name would end with the body. Use a block instead:

```cella error
~ mod example
~
main: fun
{
	val ready = true
	if ready
		val message = "go"
}
```

```errors
Cannot use declarations as whole bodies
```

## `while`

`while` runs its body as long as its condition is true. The condition is checked before each pass, so the body may not run at all:

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
	var n = 27
	var steps = 0
	while n != 1
	{
		if n % 2 == 0
			n /= 2
		else
			n = 3 * n + 1

		steps += 1
	}

	printf("%d steps\n", steps)
}
```

```output
111 steps
```

## `do ... while`

`do` runs its body first and checks the condition after each pass, so the body always runs at least once. `while` and the condition follow the body:

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
	var n = 10
	do
	{
		printf("%d\n", n)
		n += 1
	} while n < 3

	var total = 0
	do
		total += 4
	while total < 10

	printf("%d\n", total)
}
```

```output
10
12
```

After a block, the usual style puts `while` on the closing brace's line. After a single statement, it goes on its own line.

## `loop`

`loop` repeats its body forever. A `break` leaves it, and a `ret` leaves the whole function:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
firstPositive: fun(values: array[i32, 4]) -> i32
{
	var i: usize = 0
	loop
	{
		if values[i] > 0
			ret values[i]

		i += 1
	}
}

main: fun
{
	var tries = 0
	loop
	{
		tries += 1
		if tries == 3
			break
	}

	printf("%d %d\n", tries, firstPositive([0, -2, 5, 8]))
}
```

```output
3 5
```

A `loop` with no `break` never finishes, so the compiler knows the end of `firstPositive` can't be reached, and the function needs no `ret` after it. The same holds for `while true`.

## `for` over ranges

`for` with a range runs its body once for each integer in the range. `a..b` counts from `a` up to but not including `b`, and `a..=b` includes `b`:

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
	for i in 0..4
		printf("%d ", i)

	printf("| ")
	for i in 1..=3
		printf("%d ", i)

	printf("| ")
	for i in 5..2
		printf("%d ", i)

	printf("|\n")
}
```

```output
0 1 2 3 | 1 2 3 | |
```

A range whose start is past its end, like `5..2`, is empty, and the body doesn't run. Ranges only count up, one at a time.

Both bounds run once, before the first pass. Changing a variable used as a bound doesn't change how many times the loop runs:

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
	var limit = 3
	for i in 0..limit
	{
		limit += 1
		printf("%d ", i)
	}

	printf("| %d\n", limit)
}
```

```output
0 1 2 | 6
```

### The loop variable

The loop variable is new on each pass and only exists inside the body. Its type comes from the bounds, as the type of `a + b` would: `0..count` with a `usize` count counts in `usize`. `..=` can count up to the largest value of its type without overflowing:

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
	val count: usize = 3
	for i in 0..count
		printf("%zu ", i)

	printf("|")
	for b in 253u8..=255u8
		printf(" %d", b)

	printf("\n")
}
```

```output
0 1 2 | 253 254 255
```

Name the variable `_` when the body doesn't use it:

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
	for _ in 0..3
		printf("hello\n")
}
```

```output
hello
hello
hello
```

Bounds can also be `char` values, which step through the characters in order:

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
	for c in 'a'..='e'
		printf("%c", u32(c))

	printf("\n")
}
```

```output
abcde
```

The loop variable is read-only:

```cella error
~ mod example
~
main: fun
{
	for i in 0..3
		i = 2
}
```

```errors
Cannot reassign read-only loop variables
```

Floats can't be range bounds, and the variable of a range loop can't take a mode such as `mut`:

```cella error
~ mod example
~
main: fun
{
	for f in 0.0..1.5
	{
	}

	for mut i in 0..3
	{
	}
}
```

```errors
Cannot use 'f64' as a range bound
Cannot iterate over ranges with 'mut'
```

## `for` over arrays

`for` over an array walks its elements in order:

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
	val primes = [2, 3, 5, 7]
	var sum = 0
	for p in primes
		sum += p

	printf("%d\n", sum)
}
```

```output
17
```

[Arrays](arrays.md) covers the rest: borrowing elements with `for imm x` and `for mut x`, and taking them with `for own x`. Types can also define their own `for` loops; [Operators](operators.md) shows how.

## `break` and `cont`

`break` leaves a loop at once. `cont` skips the rest of the body and goes on with the next pass: in a `for` loop, to the next value; in `while` and `do ... while`, to the condition. Both act on the innermost loop around them:

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
	for i in 0..10
	{
		if i % 2 == 0
			cont

		if i > 7
			break

		printf("%d ", i)
	}

	printf("done\n")
}
```

```output
1 3 5 7 done
```

`break` and `cont` outside a loop are errors:

```cella error
~ mod example
~
main: fun
{
	break
}
```

```errors
Cannot use 'break' outside loops
```

## Labels

A label names a loop, so that `break` and `cont` can act on a loop further out than the innermost one. It's written before the loop keyword, with a colon, and the jump names it:

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
	val target = 12
	search: for a in 1..10
	{
		for b in 1..10
		{
			if a * b == target
			{
				printf("%d x %d\n", a, b)
				break search
			}
		}
	}

	val grid = [[1, 2, 3], [4, -1, 6], [7, 8, 9]]
	rows: for row in grid
	{
		var sum = 0
		for value in row
		{
			if value < 0
				cont rows

			sum += value
		}

		printf("row sum %d\n", sum)
	}
}
```

```output
2 x 6
row sum 6
row sum 24
```

`break search` leaves both loops as soon as a pair is found. `cont rows` leaves the inner loop and goes on with the next row, so a row with a negative value prints nothing.

Every loop form takes a label: `for`, `while`, `do` and `loop`. Labels can't go on other statements, and a jump must name a label:

```cella error
~ mod example
~
main: fun
{
	var x = 0
	outer: while x < 10
	{
		x += 1
		if x == 1
			break 5

		if x == 3
			break x

		if x == 4
			cont outr

		break outer
	}

	start: if x > 0
	{
	}
}
```

```errors
Expected a label
'x' is not a label
Symbol 'outr' not found in this scope
Expected a loop
```

Labels have their own names, apart from variables, so a label can share a name with a variable without hiding it.

## Jumps as expressions

`ret`, `break` and `cont` are expressions as well as statements. They never produce a value, since control leaves before one is needed, so they fit anywhere a value of any type is expected. This makes them useful in `match` arms and on the right of `&&` and `||`:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
check: fun(ok: bool) -> i32
{
	val checked = ok || ret 7
	ret i32(checked)
}

main: fun
{
	for x in 1..10
	{
		val odd = match x % 2 { 0 => cont, else => x }
		val small = match odd > 6 { true => break, else => odd }
		printf("%d ", small)
	}

	printf("| %d %d\n", check(true), check(false))
}
```

```output
1 3 5 | 1 7
```

In `check`, `ok || ret 7` returns 7 from the function when `ok` is false. In the loop, each `match` either gives a value or leaves the pass.

## Blocks and scopes

A block is a list of statements in braces. Function bodies and loop bodies are blocks, and a block can also stand on its own as a statement. Each block is a scope: names declared in it exist from their declaration to the closing brace, and a loop variable belongs to its loop's body in the same way. [Variables and constants](variables.md#scopes) covers scopes and shadowing, and [Ownership and destructors](ownership.md) covers when values with destructors are destroyed.

## `match` and `when`

`match` picks one of several arms by comparing a value against patterns, as a statement or as an expression; [Pattern matching](pattern-matching.md) covers it. `when` keeps or removes code depending on build flags; [Conditional compilation](conditional-compilation.md) covers it.
