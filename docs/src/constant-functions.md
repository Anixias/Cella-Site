# Constant functions

A constant function is a function the compiler can also run while compiling. Called where a value must be known at compile time, such as a constant's initial value or the length of an array type, it runs then and its result becomes a constant. Called anywhere else, it's an ordinary function call.

## Declaring a constant function

`const` before `fun` makes a function constant:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
square: const fun(x: i32) -> i32 => x * x

side: const i32 = square(4)
cells: val array[u8, usize(square(2))] = [1, 2, 3, 4]

main: fun
{
	const area = square(side)
	val n = 5
	printf("%d %d %zu %d\n", side, area, cells.length, square(n))
}
```

```output
16 256 4 25
```

`side` and `area` are worked out while compiling, and the type of `cells` uses `square(2)` as its length. `square(n)` in `main` runs when the program does, like any call.

A constant function's arguments must be constants where a constant is needed:

```cella error
~ mod example
~
square: const fun(x: i32) -> i32 => x * x

counter: var i32 = 3
total: const i32 = square(counter)

main: fun
{
}
```

```errors
The initial value of 'total' must be a constant
```

## What a body can do

A constant function's body is an ordinary function body. It can declare `val`, `var` and `const` locals, assign to them, branch, loop, match, take `mut` and `imm` parameters and call other constant functions:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
crcTable: const fun -> array[u32, 8]
{
	var table = array[u32, 8]()
	for i in 0..8
	{
		var c = u32(i)
		for _ in 0..8
		{
			if c & 1 == 1
				c = 0xEDB88320 ^ (c >> 1)
			else
				c = c >> 1
		}

		table[i] = c
	}

	ret table
}

bump: const fun(mut value: i32, by: i32 = 1)
{
	value += by
}

countTo: const fun(limit: i32) -> i32
{
	var n = 0
	while true
	{
		bump(mut n)
		if n == limit
			break
	}

	ret n
}

table: const array[u32, 8] = crcTable()

main: fun
{
	printf("%u %u %d\n", table[1], table[7], countTo(6))
}
```

```output
1996959894 2657392035 6
```

The body may only call constant functions and operators. Built-in operators and conversions are always constant. It can't call other functions, including `ext` functions and the standard library's `panic`, read or write module and static values that aren't constants, use pointers, take addresses, call function values or use values with destructors:

```cella error
~ mod example
~
~ ext
~ {
~ 	puts: fun(text: cstr) -> i32
~ }
~
counter: var i32 = 0

plain: fun(x: i32) -> i32 => x

busy: const fun(x: i32) -> i32
{
	counter += 1
	puts("hi")
	ret plain(x)
}

stop: const fun -> never
{
	loop
	{
	}
}

main: fun
{
}
```

```errors
Cannot use module values in constant functions
Cannot call 'puts' in constant functions
Cannot call 'plain' in constant functions
Cannot return 'never' from constant functions
```

These rules are checked once, where the function is declared, whether or not anything calls it.

## Operators, constructors and methods

Operators, constructors, conversions and methods are constant the same way, with `const` before `op` or `fun`:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Point: rec
{
	x: i32
	y: i32

	new: const op(x: i32, y: i32)
	{
		self.x = x
		self.y = y
	}

	sum: const fun(self) -> i32 => self.x + self.y

	shift: const fun(mut self, by: i32)
	{
		self.x += by
		self.y += by
	}

	+: const op(a: Point, b: Point) -> Point => Point(a.x + b.x, a.y + b.y)
}

moved: const fun -> Point
{
	var p = Point(1, 2) + Point(3, 4)
	p.shift(10)
	ret p
}

corner: const Point = moved()
total: const i32 = corner.sum()

main: fun
{
	printf("%d %d %d\n", corner.x, corner.y, total)
}
```

```output
14 16 30
```

A constructor declared `new: op() = default` is always constant, and so is building a record field by field. Destructors can't be constant.

## Functions without parameters

A constant function that takes no parameters and isn't generic works like a constant. The compiler runs it once, where it's declared, and every call to it is that value. Its errors are reported where it's declared, even if nothing calls it:

```cella error
~ mod example
~
largest: const fun -> i32
{
	val top: i32 = 2147483647
	ret top + 1
}

main: fun
{
}
```

```errors
Panic in 'largest': addition overflow
```

It's still compiled as a function when something needs one: when it's `pub`, when it's used as a function value, or when it meets a trait's requirement. Otherwise only its value is kept.

## Errors while running

A constant function that fails while compiling stops the build. The error points at the call, and its note shows where in the function it happened:

```cella error
~ mod example
~
square: const fun(x: i32) -> i32 => x * x
halve: const fun(x: i32, by: i32) -> i32 => x / by
pick: const fun(values: array[i32, 3], at: usize) -> i32 => values[at]

big: const i32 = square(100000)
divided: const i32 = halve(1, 0)
picked: const i32 = pick([1, 2, 3], 5)

main: fun
{
}
```

```errors
Panic in 'square': multiplication overflow
Panic in 'halve': division by zero
Panic in 'pick': index out of bounds
```

A function that runs for too long or recurses too deeply also stops with an error, such as "Evaluating 'spin' takes too many steps". The same function called while the program runs fails the way any call does, with a panic.

## Generic constant functions

A constant function can be generic. Since it can't use values with destructors, a type parameter it stores or copies needs `copy`:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
twice[T: copy]: const fun(x: T) -> array[T, 2] => [x, x]

pair: const array[i64, 2] = twice(7i64)

main: fun
{
	printf("%d %d\n", i32(pair[0]), i32(pair[1]))
}
```

```output
7 7
```

```cella error
~ mod example
~
same[T]: const fun(x: T) -> T => x

main: fun
{
}
```

```errors
'same' requires 'T: copy'
```

## Constant traits

Generic code can call a trait's members at compile time only when every type that meets the bound has constant ones. There are two ways to promise that.

### Constant requirements

A trait member declared `const` is constant for every type that implements the trait. Each implementation must give a constant member, and built-in operators count:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Bits: trait req copy + noref
{
	|: const op(a: Self, b: Self) -> Self
}

u32: impl Bits

combine[T: Bits]: const fun(a: T, b: T) -> T => a | b

mask: const u32 = combine(0x10u32, 0x01u32)

main: fun
{
	printf("%u\n", mask)
}
```

```output
17
```

```cella error
~ mod example
~
Bits: trait req copy + noref
{
	|: const op(a: Self, b: Self) -> Self
}

Mask: rec impl Bits
{
	value: u8

	|: op(a: Mask, b: Mask) -> Mask => Mask(a.value | b.value)
}

main: fun
{
}
```

```errors
'|' must be 'const' to match 'Bits.|'
```

### Constant implementations and bounds

A trait whose members aren't `const` can still be implemented as constant. `impl const` promises that every member of that implementation is constant, and `T: const Trait` accepts only types with such an implementation. Inside the generic function, the trait's members, and those of the traits it requires, can then be called at compile time:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Score: trait
{
	score: fun(self) -> i32
}

Ranked: trait req Score
{
	rank: fun(self) -> i32
}

Gem: rec impl const Ranked
{
	value: i32

	score: const fun(self) -> i32 => self.value * 10
	rank: const fun(self) -> i32 => self.value
}

Rock: rec impl Ranked
{
	value: i32

	score: fun(self) -> i32 => self.value
	rank: fun(self) -> i32 => 0
}

total[T: copy + const Ranked]: const fun(x: T) -> i32 => x.score() + x.rank()

gem: const i32 = total(Gem(3))

main: fun
{
	printf("%d %d\n", gem, Rock(5).score())
}
```

```output
33 5
```

`Gem`'s implementation is constant, so `total` accepts it while compiling. `Rock`'s isn't, so it doesn't meet `const Ranked`. An `impl const` checks its members, a default it would use must itself be `const`, and the traits it requires must be implemented as constant too:

```cella error
~ mod example
~
Score: trait
{
	score: fun(self) -> i32
	bonus: fun(self) -> i32 => 1
}

Ranked: trait req Score
{
	rank: fun(self) -> i32
}

Gem: rec impl const Score
{
	value: i32

	score: fun(self) -> i32 => self.value
}

Rock: rec impl Ranked
{
	value: i32

	score: fun(self) -> i32 => self.value
	rank: fun(self) -> i32 => 0
}

total[T: copy + const Ranked]: const fun(x: T) -> i32 => x.rank()
plain[T: copy + Ranked]: const fun(x: T) -> i32 => x.rank()

rock: const i32 = total(Rock(1))

main: fun
{
}
```

```errors
'Score.bonus' has no 'const' default
'score' must be 'const' in 'impl const Score'
Cannot call 'Ranked.rank' in constant functions
'total' requires 'T: const Ranked'
```

A constant implementation is only ever the written `impl const`: a conformance whose members happen to all be constant doesn't meet `const Trait`.
