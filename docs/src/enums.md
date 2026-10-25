# Enums

An enum is a type whose values come from a fixed list of cases. A case can be a plain name, like a C enum constant, or it can hold values of its own, called its payload. This chapter covers declaring enums, creating their values, testing which case a value is and converting enums to and from integers. Taking payloads apart is mostly the job of `match`, covered in [Pattern matching](pattern-matching.md).

## Declaring an enum

An enum declaration lists its cases, one per line or separated by commas on one line:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Direction: enum
{
	north
	east
	south
	west
}

Suit: enum { clubs, diamonds, hearts, spades }

main: fun
{
	val heading = Direction.east
	val trump = Suit.hearts
	printf("%d %d\n", i32(heading == Direction.east), i32(trump != Suit.spades))
}
```

```output
1 1
```

A case is written `Type.case`. Two values of a plain enum compare with `==` and `!=`; they have no ordering, so `<` and the other comparisons are errors. Case names are camelCase by convention.

An enum needs at least one case, and each case name can appear only once:

```cella error
~ mod example
~
Direction: enum
{
	north
	south
	north
}

Nothing: enum
{
}

main: fun
{
	val a = Direction.north < Direction.south
}
```

```errors
Case 'north' is declared more than once in 'Direction'
Case 'north' is declared more than once in 'Direction'
'Nothing' needs at least one case
No operation defined for '<' between 'Direction' and 'Direction'
```

## Case values

Every case has an integer value. The first case is 0 and each case after it is one more than the case before. A case can set its own value with `=`, and the cases after it count on from there:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Status: enum
{
	ok
	notReady
	timeout
	lost = -1
	busy = 100
	retry
}

main: fun
{
	printf("%d %d %d %d %d %d\n", i32(Status.ok), i32(Status.notReady), i32(Status.timeout), i32(Status.lost),
		i32(Status.busy), i32(Status.retry))
}
```

```output
0 1 2 -1 100 101
```

A value can be any constant integer expression. It can use constants and earlier cases of the same enum by their bare names, and cases of other enums once they're converted to an integer:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
base: const i32 = 40

Level: enum
{
	none
	low = base / 8
	high = low * 3
	top = i32(Direction.west) + high
}

Direction: enum { north, east, south, west }

main: fun
{
	printf("%d %d %d\n", i32(Level.low), i32(Level.high), i32(Level.top))
}
```

```output
5 15 18
```

The value has to be known when the program is compiled, and it has to be an integer. Two enums whose values depend on each other are an error:

```cella error
~ mod example
~
~ runtime: fun -> i32 => 5
~
Dynamic: enum
{
	zero
	other = runtime()
}

Mixed: enum
{
	zero
	half = 1.5
}

First: enum { zero, a = i32(Second.b) }

Second: enum { zero, b = i32(First.a) }

main: fun
{
}
```

```errors
The value of 'other' must be a constant
The value of 'half' must be an integer
'First' depends on its own values
'Second' depends on its own values
```

Two cases with the same value are two names for the same case. Here `stop` and `halt` are interchangeable:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Signal: enum
{
	go
	stop
	halt = 1
}

main: fun
{
	printf("%d\n", i32(Signal.stop == Signal.halt))
}
```

```output
1
```

## The tag type

An enum is stored as an integer, called its tag. Without a tag type, the compiler picks the smallest integer type that holds every case value. Writing an integer type in parentheses after `enum` sets the tag type yourself:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Small: enum { a, b, c }

Signed: enum { zero, low = -50 }

Wide: enum { zero, big = 70000 }

Code: enum(u16)
{
	none
	first = 100
}

main: fun
{
	printf("%d %d %d %d\n", i32(sizeOf(Small)), i32(sizeOf(Signed)), i32(sizeOf(Wide)), i32(sizeOf(Code)))
}
```

```output
1 1 4 2
```

The tag type can be any integer type. With a tag type, every case value must fit in it, and a typed value must convert to it without loss:

```cella error
~ mod example
~
Byte: enum(u8)
{
	low
	high = 300
}

Counted: enum(u8)
{
	zero
	last = 255
	past
}

Typed: enum(u8)
{
	zero
	wide = 5u16
}

Fraction: enum(f32)
{
	zero
}

main: fun
{
}
```

```errors
'300' doesn't fit in 'u8'
'past' is 256, which doesn't fit in 'u8'
Cannot convert type 'u16' to 'u8'
'f32' isn't an integer type
```

## The default case

The case with the value 0 is the enum's default. A variable declared without a value starts as that case, and so does an enum field of a record built with `T()`:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Mode: enum
{
	active = 1
	idle = 0
	paused = 2
}

Settings: rec
{
	mode: Mode
	level: i32
}

main: fun
{
	var mode: Mode
	val settings = Settings()
	printf("%d %d\n", i32(mode == Mode.idle), i32(settings.mode == Mode.idle))
}
```

```output
1 1
```

A case with the value 0 is required. Only an `ext enum`, covered in [Calling C](calling-c.md), and the [tagless enums](#tagless-enums) at the end of this chapter can do without one:

```cella error
~ mod example
~
Rank: enum
{
	one = 1
	two = 2
}

main: fun
{
}
```

```errors
'Rank' needs a case with the value 0
```

## Payloads

A case can hold values. Its payload is written like a parameter list, with a name and a type for each value. A case with a payload is created by calling it with one argument per value:

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
	empty
	circle(radius: f64)
	rect(width: f64, height: f64)
}

area: fun(shape: Shape) -> f64 => match shape
{
	empty => 0.0
	circle(val r) => 3.0 * r * r
	rect(val w, val h) => w * h
}

main: fun
{
	val shapes = [Shape.circle(2.0), Shape.rect(3.0, 4.0), Shape.empty]
	for shape in shapes
		printf("%.1f\n", area(shape))
}
```

```output
12.0
12.0
0.0
```

The `match` in `area` picks the arm for the case and binds the payload's values to `r`, `w` and `h`. [Pattern matching](pattern-matching.md) covers this in full.

A case must be given exactly the values it holds, and a case without a payload takes no parentheses:

```cella error
~ mod example
~
Shape: enum
{
	empty
	circle(radius: f64)
	rect(width: f64, height: f64)
}

main: fun
{
	val a = Shape.circle
	val b = Shape.rect(1.0)
	val c = Shape.empty()
	val d = Shape.circle(true)
}
```

```errors
'Shape.circle' holds 1 value: radius
'Shape.rect' holds 2 values: width, height
'Shape.empty' holds no values
Cannot convert type 'bool' to 'f64'
```

Each payload value needs a name, and names can't repeat within a case. A case can't hold its own enum directly, since the value would have to contain itself; it can hold a pointer to one instead:

```cella error
~ mod example
~
Effect: enum
{
	none
	hit(i32)
}

Heal: enum
{
	none
	heal(amount: i32, amount: i32)
}

List: enum
{
	end
	link(value: i32, next: List)
}

main: fun
{
}
```

```errors
Expected ':' and a type
Payload 'amount' is declared more than once in 'heal'
Payload 'amount' is declared more than once in 'heal'
Payload 'next' of type 'List' causes a cycle in the memory layout
```

Values of an enum with payloads have no `==`; test them with `is` or `match` instead. Such an enum is stored as its tag followed by room for its largest payload:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Effect: enum
{
	none
	hit(amount: i32)
	scale(factor: f64)
}

main: fun
{
	printf("%d %d\n", i32(sizeOf(Effect)), i32(alignOf(Effect)))
}
```

```output
16 8
```

If the case with the value 0 holds values, the enum has no default, and a variable of it must be given a value before it's read:

```cella error
~ mod example
~
Effect: enum
{
	hit(amount: i32)
	none
}

main: fun
{
	var effect: Effect
	val copy = effect
}
```

```errors
Cannot use uninitialized values
```

Cases that share a value must also hold the same payload types:

```cella error
~ mod example
~
Effect: enum
{
	none
	hit(amount: i32) = 1
	miss(chance: f32) = 1
}

main: fun
{
}
```

```errors
'hit' and 'miss' share the value 1 but have different payloads
'hit' and 'miss' share the value 1 but have different payloads
```

## Bare case names

Where the compiler already knows which enum it needs, a case can be written without the type name. That covers typed declarations, arguments, return values, assignments, array elements and comparisons with a value of the enum:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Team: enum { red, blue }

Effect: enum
{
	none
	hit(amount: i32)
}

opposite: fun(team: Team) -> Team
{
	if team == red
		ret blue

	ret red
}

strength: fun(effect: Effect) -> i32 => match effect
{
	none => 0
	hit(val n) => n
}

main: fun
{
	var team: Team = red
	team = opposite(team)
	val effects: array[Effect, 2] = [hit(5), none]
	printf("%d %d %d\n", i32(team), strength(effects[0]), strength(hit(7)))
}
```

```output
1 5 7
```

Without an expected type, a bare case name is an error. A name that could also mean a variable or function of the expected type is ambiguous, and has to be written in full:

```cella error
~ mod example
~
Team: enum { red, blue }

blue: val Team = Team.red

main: fun
{
	val team = red
	val same = Team.red == blue
}
```

```errors
Cannot infer the type of 'red'
'blue' is ambiguous
```

## Testing for a case

`value is case` is `true` when the value is that case. For a case with a payload, the payload goes in parentheses: `_` accepts any value, and `val name` binds the value to a name that can be used where the test is known to be true:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Effect: enum
{
	none
	hit(amount: i32)
	heal(amount: i32)
}

main: fun
{
	val effect = Effect.hit(9)
	printf("%d %d %d\n", i32(effect is none), i32(effect is hit(_)), i32(effect is Effect.heal(_)))

	if effect is hit(val n) && n > 5
		printf("big hit %d\n", n)
}
```

```output
0 1 0
big hit 9
```

The case after `is` can be bare or qualified. `is` accepts every pattern `match` does; [Pattern matching](pattern-matching.md) lists them.

## Converting to and from integers

An enum without payloads converts to any integer type with `T(x)`, which gives its case value. An integer converts back with the enum's name:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Code: enum
{
	none
	first = 100
	second
}

main: fun
{
	val code = Code.second
	printf("%d %d\n", i32(code), u8(code))

	val raw: u16 = 100
	val back = Code(raw)
	printf("%d\n", i32(back == Code.first))
}
```

```output
101 101
1
```

These conversions are never implicit. A constant that matches no case is a compile error, and a value that matches no case at run time panics:

```cella error
~ mod example
~
Code: enum
{
	none
	first = 100
}

main: fun
{
	val bad = Code(50)
}

number: fun -> i32 => Code.first
```

```errors
'Code' has no case with the value 50
Cannot convert type 'Code' to 'i32'
```

```cella
~ mod example
~
Code: enum
{
	none
	first = 100
}

main: fun
{
	val raw = 50
	val _ = Code(raw)
}
```

```output
Panic at main.ce:12:10: 'Code' has no case with this value
```

An enum with payloads has no conversion to or from integers. An enum can't declare its own conversions to or from integer types either, since those are built in ([Conversions](conversions.md) covers declared conversions):

```cella error
~ mod example
~
Effect: enum
{
	none
	hit(amount: i32)
}

Color: enum
{
	red
	green

	as: op(self) -> i32 => 0
}

main: fun
{
	val n = i32(Effect.none)
}
```

```errors
Conversion to 'i32' is built in
No constructor for 'i32' accepts argument of type 'Effect'
```

## Methods

An enum can declare methods, static functions, properties and static fields, as a record does; [Methods and properties](methods.md) covers them. Inside a method, `self` is the enum value, so `match self` is the usual way to look at it, and a `mut self` method can replace `self` with another case:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Effect: enum
{
	none
	hit(amount: i32)
	heal(amount: i32)

	strong: fun(amount: i32) -> Effect => hit(amount * 2)

	size: fun(self) -> i32 => match self
	{
		none => 0
		hit(val n) => n
		heal(val n) => n
	}

	isHarmful: get(self) -> bool => self is hit(_)

	double: fun(mut self)
	{
		self = match self
		{
			none => none
			hit(val n) => hit(n * 2)
			heal(val n) => heal(n * 2)
		}
	}
}

main: fun
{
	var effect = Effect.strong(3)
	effect.double()
	printf("%d %d\n", effect.size(), i32(effect.isHarmful))
}
```

```output
12 1
```

An enum can't declare fields, constructors or a destructor, and a method can't share a name with a case:

```cella error
~ mod example
~
Effect: enum
{
	none
	hit(amount: i32)

	count: i32

	new: op
	{
	}
}

Shot: enum
{
	miss
	hit(amount: i32)

	hit: fun -> Shot => miss
}

main: fun
{
}
```

```errors
Cannot declare fields in enums
Cannot declare constructors in enums
'hit' is declared more than once in 'Shot'
'hit' is declared more than once in 'Shot'
```

## Owned enums

A plain enum copies like an integer. `own enum` declares an enum whose values can't be copied, only moved, the way `own rec` does for records. After a move, the old variable can't be used:

```cella error
~ mod example
~
Ticket: own enum
{
	open(id: i32)
	closed
}

main: fun
{
	val ticket = Ticket.open(1)
	val moved = ticket
	val again = ticket
}
```

```errors
Cannot use moved values
```

An enum whose payloads hold owning values, such as a record with a destructor, must be declared `own enum` ("Cannot store owning values in enums that aren't 'own'"). [Ownership and destructors](ownership.md) explains moves.

## Generic enums

An enum can take type parameters, written after its name. Each use names the type, or lets the compiler infer it:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Maybe[T]: enum
{
	nothing
	just(value: T)
}

half: fun(n: i32) -> Maybe[i32]
{
	if n % 2 != 0
		ret nothing

	ret just(n / 2)
}

main: fun
{
	val results = [half(8), half(3)]
	for result in results
	{
		match result
		{
			just(val v) => printf("%d\n", v)
			nothing => printf("odd\n")
		}
	}
}
```

```output
4
odd
```

[Generics](generics.md) covers type parameters and their constraints, including [`T: enum`](generics.md#enum) for generic code over enums without payloads.

## Tagless enums

`enum match T` declares an enum that stores a value of type `T` and nothing else. Its cases sort the values of `T` into groups: a case lists the values it stands for after `=`, and one case written `= else` takes every other value. A case can have a payload written as a name with no type, which is the value itself, and the `else` case must have one:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Socket: enum match i32
{
	invalid = -1
	open(handle) = else
}

Parity: enum match u8
{
	even = 0, 2, 4, 6
	odd = 1, 3, 5, 7
	large(value) = else
}

describe: fun(p: Parity) -> i32 => match p
{
	even => 0
	odd => 1
	large(val v) => i32(v)
}

main: fun
{
	val raw = 7
	val socket = Socket(raw)
	match socket
	{
		open(val h) => printf("handle %d\n", h)
		invalid => printf("invalid\n")
	}

	printf("%d %d %d\n", describe(Parity(3)), describe(Parity(40)), i32(sizeOf(Socket)))
	printf("%d %d\n", i32(Socket.invalid), i32(socket))
}
```

```output
handle 7
1 40 4
-1 7
```

A tagless enum takes no more room than `T`, and converting between it and `T` never changes the value. Converting from `T` can't fail, since the `else` case accepts everything the other cases don't. A case with a payload can be created with a value, which has to be one that case stands for; a constant that isn't is a compile error, and a value that isn't panics at run time:

```cella error
~ mod example
~
Socket: enum match i32
{
	invalid = -1
	open(handle) = else
}

main: fun
{
	val bad: Socket = open(-1)
}
```

```errors
'Socket.open' can't hold -1
```

```cella
~ mod example
~
Socket: enum match i32
{
	invalid = -1
	open(handle) = else
}

main: fun
{
	val raw = -1
	val _: Socket = open(raw)
}
```

```output
Panic at main.ce:12:18: 'Socket.open' can't hold this value
```

`T` can be an integer type, `char`, `bool`, a pointer type or a function type. For pointer and function types the only value a case can list is `null`, which makes an enum for pointers that may be null:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Node: rec
{
	value: i32
}

NodeRef: enum match ptr[Node]
{
	none = null
	some(node) = else
}

read: fun(n: NodeRef) -> i32 => match n
{
	some(val p) => p.value
	none => -1
}

main: fun
{
	var node = Node(5)
	val found: NodeRef = some(@node)
	val missing: NodeRef = none
	printf("%d %d %d\n", read(found), read(missing), i32(sizeOf(NodeRef)))
}
```

```output
5 -1 8
```

A case without a payload needs a value, the values must be constants, and no value can be listed twice. The `else` case is needed unless the listed values cover every value of `T`, and there can be only one:

```cella error
~ mod example
~
Repeats: enum match u8
{
	low = 1, 2
	high = 2, 3
	rest(value) = else
}

Missing: enum match u16
{
	low = 1
}

Unvalued: enum match i32
{
	zero
	rest(value) = else
}

Floats: enum match f32
{
	any(value) = else
}

Pointers: enum match ptr[i32]
{
	zero = 0
	other(value) = else
}

main: fun
{
}
```

```errors
2 is listed more than once
2 is listed more than once
'Missing' needs an 'else' case
Case 'zero' needs a value
Cannot declare 'enum match f32'
Only 'null' can be listed for 'ptr[i32]'
```

A tagless enum has no tag type, so `enum(u8) match i32` is an error, and listing several values or writing `else` is only allowed in an `enum match`.
