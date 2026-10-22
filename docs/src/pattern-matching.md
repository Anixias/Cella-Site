# Pattern matching

A pattern describes a shape a value can have: a particular number, a range, an enum case with certain payload values, a record with certain fields. `match` compares a value against a list of patterns and runs the first one that fits, and `is` tests a value against one pattern. Patterns can also bind names to the parts of the value they look at.

## The match statement

`match` takes a value and a block of arms. Each arm is a pattern, `=>`, and a statement. The arms are tried from top to bottom, and the first one whose pattern fits runs:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Light: enum { red, yellow, green }

main: fun
{
	val lights = [Light.green, Light.yellow, Light.red]
	for light in lights
	{
		match light
		{
			green => printf("go\n")
			yellow =>
			{
				printf("slow down\n")
				printf("then stop\n")
			}
			red => printf("stop\n")
		}
	}
}
```

```output
go
slow down
then stop
stop
```

An arm's statement can be a block. Arms go on separate lines, or on one line separated by commas, but not both:

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
	val n = 2
	match n { 1 => printf("one\n"), 2 => printf("two\n"), else => printf("many\n") }
}
```

```output
two
```

An `else` arm runs when no other arm fits. It must be the last arm, and a match has at most one. A match statement doesn't have to handle every value: when no arm fits and there is no `else`, it does nothing.

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
	for n in 0..4
	{
		match n
		{
			1 => printf("one\n")
			3 => printf("three\n")
		}
	}
}
```

```output
one
three
```

The compiler rejects arms that can never run: an arm after `else`, a second `else`, or a value that an earlier arm already matched:

```cella error
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Light: enum { red, yellow, green }

first: fun(light: Light)
{
	match light
	{
		else => printf("any\n")
		red => printf("red\n")
	}
}

second: fun(light: Light)
{
	match light
	{
		red => printf("red\n")
		red => printf("red again\n")
		else => printf("other\n")
		else => printf("other again\n")
	}
}

main: fun
{
}
```

```errors
'else' must be the last arm
'red' is matched more than once
'red' is matched more than once
A match can have only one 'else' arm
A match can have only one 'else' arm
```

## Match expressions

A `match` can also give a value. Each arm is then a pattern, `=>`, and an expression, and the match's value is the value of the arm that fits. A match expression works anywhere an expression does, including as a function's expression body:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Role: enum { fighter, healer, tank }

damage: fun(role: Role) -> i32 => match role
{
	fighter => 7
	tank => 3
	else => 1
}

main: fun
{
	val role = Role.healer
	val bonus = match role { fighter => 10, else => 2 }
	printf("%d %d %d\n", damage(Role.fighter), damage(role), bonus)

	if match role { healer => true, else => false }
		printf("healer\n")
}
```

```output
7 1 2
healer
```

The arms must agree on a type. When the match is used where a type is expected, as in a typed declaration or an argument, the arms are checked against that type; otherwise each arm's value has to convert to a common type, and a literal takes the type of the others:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Role: enum { fighter, healer, tank }

main: fun
{
	val role = Role.healer
	val small: u8 = match role { fighter => 1, healer => 200, tank => 3 }
	val big: i64 = match role { fighter => 1, else => 5_000_000_000 }
	printf("%d %lld\n", small, big)
}
```

```output
200 5000000000
```

```cella error
~ mod example
~
Role: enum { fighter, healer, tank }

main: fun
{
	val r = Role.tank
	val mixed = match r
	{
		fighter => 1
		healer => "two"
		tank => 3
	}
}
```

```errors
The arms of this match have incompatible types: 'i32', 'str'
```

An arm can leave the function or loop instead of giving a value, since `ret`, `break` and `cont` are expressions:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Reading: enum
{
	missing
	value(n: i32)
}

show: fun(reading: Reading)
{
	val n = match reading { value(val n) => n, missing => ret }
	printf("read %d\n", n)
}

main: fun
{
	show(Reading.value(4))
	show(Reading.missing)
}
```

```output
read 4
```

A match expression can be followed by an index, a member access or a call, which apply to its value:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Kind: enum { small, large }

main: fun
{
	val kind = Kind.large
	val n = match kind { small => [1, 2], large => [3, 4] }[1]
	printf("%d\n", n)
}
```

```output
4
```

## Covering every value

A match expression must handle every value its input can have, since it has to give a value either way. The compiler counts enum cases, the values of `bool`, integer types and `char`, and record fields. For other types, such as floats, only an `else` arm covers the rest, and an `else` arm always does:

```cella error
~ mod example
~
Role: enum { fighter, healer, tank }

name: fun(role: Role) -> i32 => match role
{
	fighter => 1
}

parity: fun(b: bool) -> i32 => match b
{
	true => 1
}

bucket: fun(b: u8) -> i32 => match b
{
	0..100 => 1
	101..=255 => 2
}

main: fun
{
}
```

```errors
This match doesn't handle every case of 'Role': 'healer' and 'tank'
This match doesn't handle every value of 'bool'
This match doesn't handle every value of 'u8'
```

The last match misses 100. Ranges and relational patterns that together cover an integer type's whole range need no `else`:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
sign: fun(n: i8) -> i32 => match n
{
	< 0 => -1
	0 => 0
	> 0 => 1
}

half: fun(b: u8) -> i32 => match b
{
	0..128 => 0
	128..=255 => 1
}

main: fun
{
	printf("%d %d %d %d\n", sign(-5), sign(0), half(5), half(200))
}
```

```output
-1 0 0 1
```

A match statement in which every arm returns counts as returning when it covers every value, so the function needs no `ret` after it:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Team: enum { red, blue }

number: fun(team: Team) -> i32
{
	match team
	{
		red => ret 1
		blue => ret 2
	}
}

main: fun
{
	printf("%d\n", number(Team.blue))
}
```

```output
2
```

## Value patterns

Any expression can be a pattern. A value pattern fits when the input is `==` to it, so it works for any type that has `==`: literals, constants, variables and parameters are all values:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
limit: const i32 = 50

pick: fun(x: i32, low: i32, high: i32) -> i32 => match x
{
	0 => 0
	limit => 1
	low => 2
	high => 3
	else => 4
}

main: fun
{
	printf("%d %d %d %d %d\n", pick(0, 3, 9), pick(50, 3, 9), pick(3, 3, 9), pick(9, 3, 9), pick(7, 3, 9))
}
```

```output
0 1 2 3 4
```

A name in a pattern is always a value, never a new variable: `low` compares with the parameter `low`. Binding a new name takes a keyword, as shown in [Bindings](#bindings).

A record with its own `==` operator can be matched by value too. [Operators](operators.md) shows how to declare one. A type without `==` can't:

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

	==: op(a: Point, b: Point) -> bool => a.x == b.x && a.y == b.y
}

origin: val Point = Point(0, 0)

where: fun(p: Point) -> i32 => match p
{
	origin => 0
	Point(1, 1) => 1
	else => 2
}

main: fun
{
	printf("%d %d %d\n", where(Point(0, 0)), where(Point(1, 1)), where(Point(3, 1)))
}
```

```output
0 1 2
```

```cella error
~ mod example
~
Size: rec
{
	width: i32
}

main: fun
{
	val s = Size(1)
	match s
	{
		Size(1) => {}
	}
}
```

```errors
No operation defined for '==' between 'Size' and 'Size'
```

Two constant patterns with the same value in one match are an error, whichever way they're written:

```cella error
~ mod example
~
five: const i32 = 5

grade: fun(x: i32) -> i32 => match x
{
	5 => 1
	five => 2
	else => 0
}

main: fun
{
}
```

```errors
'5' and 'five' are the same value
'5' and 'five' are the same value
```

## Ranges

`a..b` fits values from `a` up to but not including `b`, and `a..=b` includes `b`. Ranges work for any type with `<` and `<=`, such as integers and `char`:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
kind: fun(c: char) -> i32 => match c
{
	'a'..='z' => 1
	'A'..='Z' => 2
	'0'..='9' => 3
	else => 0
}

grade: fun(score: i32) -> i32 => match score
{
	0..50 => 0
	50..80 => 1
	80..=100 => 2
	else => -1
}

main: fun
{
	printf("%d %d %d %d\n", kind('q'), kind('Q'), kind('7'), kind('#'))
	printf("%d %d %d %d\n", grade(49), grade(50), grade(100), grade(101))
}
```

```output
1 2 3 0
0 1 2 -1
```

## Relational patterns

A comparison operator followed by a value fits the values that compare that way: `< x`, `<= x`, `> x`, `>= x` and `!= x`. Since the first fitting arm wins, the order of arms matters:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
size: fun(x: i32) -> i32 => match x
{
	> 10 => 3
	>= 5 => 2
	!= 0 => 1
	else => 0
}

main: fun
{
	printf("%d %d %d %d\n", size(11), size(5), size(-3), size(0))
}
```

```output
3 2 1 0
```

## Several patterns in one arm

An arm can list several patterns separated by commas. It fits when any of them does:

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
	var total = 0
	for i in 0..20
	{
		match i
		{
			0, 1 => total += 1
			2..5, 7 => total += 10
			>= 15 => total += 100
			else => {}
		}
	}

	printf("%d\n", total)
}
```

```output
542
```

## Enum cases

A case name is a pattern that fits values of that case. It can be bare or qualified with its type. For a case with a payload, each payload value gets a pattern of its own in parentheses, in order:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Hit: enum
{
	miss
	hit(amount: i32)
	combo(first: i32, second: i32)
}

score: fun(h: Hit) -> i32 => match h
{
	Hit.miss => 0
	hit(0) => 1
	hit(1..10) => 2
	hit(_) => 3
	combo(> 5, _) => 4
	combo(_, _) => 5
}

main: fun
{
	val hits = [Hit.miss, Hit.hit(0), Hit.hit(4), Hit.hit(40), Hit.combo(6, 1), Hit.combo(1, 6)]
	var total = 0
	for h in hits
		total = total * 10 + score(h)

	printf("%d\n", total)
}
```

```output
12345
```

Any pattern can go inside a payload, including another case pattern, so nested enums are matched in one step:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Inner: enum
{
	empty
	value(n: i32)
}

Outer: enum
{
	nothing
	wrap(inner: Inner)
}

depth: fun(o: Outer) -> i32 => match o
{
	wrap(value(1..10)) => 3
	wrap(value(_)) => 2
	wrap(empty) => 1
	nothing => 0
}

main: fun
{
	printf("%d %d %d %d\n", depth(Outer.wrap(Inner.value(5))), depth(Outer.wrap(Inner.value(42))),
		depth(Outer.wrap(Inner.empty)), depth(Outer.nothing))
}
```

```output
3 2 1 0
```

A case pattern must give one pattern per payload value, and it has to be a case of the input's enum:

```cella error
~ mod example
~
Hit: enum
{
	miss
	hit(amount: i32)
}

Team: enum { red, blue }

main: fun
{
	val h = Hit.hit(1)
	val a = h is hit
	val b = h is hit(1, 2)
	val c = h is miss()
	val d = h is Team.red
	val e = h is fly
}
```

```errors
'Hit.hit' holds 1 value: amount
'Hit.hit' holds 1 value: amount
'Hit.miss' holds no values
Expected a case of 'Hit'
'Hit' has no case 'fly'
```

## Bindings

A binding gives a name to a part of the value. It starts with a keyword:

- `val name` reads the part. A part that can be copied is copied. Any other part is moved out when the match takes its input, and borrowed read-only when it only looks at it; see [Moving parts out](#moving-parts-out).
- `var name` makes a copy that the arm can change. The change doesn't reach the matched value. When the match takes its input, it takes the part instead of copying it.
- `mut name` borrows the part mutably, so changing it changes the matched value.

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
	pair(left: i32, right: i32)
}

main: fun
{
	var effect = Effect.pair(1, 2)
	match effect
	{
		pair(var a, val b) =>
		{
			a += 10
			printf("%d %d\n", a, b)
		}
		none => {}
	}

	if effect is pair(mut a, val b)
		a = b * 100

	match effect
	{
		pair(val a, val b) => printf("%d %d\n", a, b)
		none => {}
	}
}
```

```output
11 2
200 2
```

`mut` needs a value that can be changed, and a `val` binding can't be assigned:

```cella error
~ mod example
~
Effect: enum
{
	none
	hit(amount: i32)
}

main: fun
{
	val fixed = Effect.hit(1)
	if fixed is hit(mut n)
		n = 2

	var e = Effect.hit(1)
	if e is hit(val n)
		n = 5
}
```

```errors
Cannot mutably borrow values
Cannot reassign read-only pattern bindings
```

A pattern followed by a binding tests and binds at once: `1..10 val n` fits values from 1 to 9 and names the value `n`:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Hit: enum
{
	miss
	hit(amount: i32)
}

describe: fun(h: Hit) -> i32 => match h
{
	hit(1..10 val n) => n
	hit(val n) => n * 100
	miss => 0
}

main: fun
{
	printf("%d %d %d\n", describe(Hit.hit(4)), describe(Hit.hit(40)), describe(Hit.miss))
}
```

```output
4 4000 0
```

Bindings go inside parentheses, in a payload or a record pattern. Apart from a [type test](#type-tests), a pattern can't bind at the top of an arm. A name can be bound only once per pattern, and an arm with several patterns can't bind names:

```cella error
~ mod example
~
Hit: enum
{
	miss
	hit(amount: i32)
	pair(a: i32, b: i32)
}

twice: fun(h: Hit) -> i32 => match h
{
	pair(val n, val n) => n
	else => 0
}

listed: fun(h: Hit) -> i32 => match h
{
	hit(val n), pair(val n, _) => n
	miss => 0
}

whole: fun(x: i32) -> i32 => match x
{
	1..10 val n => n
	else => 0
}

main: fun
{
}
```

```errors
'n' is bound more than once
'n' is bound more than once
Cannot bind names in arms with several patterns
Cannot bind names in arms with several patterns
Expected '=>'
```

## Ignoring values with `_`

`_` fits any value and binds nothing. It stands in for payload values and fields an arm doesn't care about:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Move: enum
{
	stay
	step(dx: i32, dy: i32)
}

isVertical: fun(m: Move) -> bool => match m
{
	step(0, _) => true
	else => false
}

main: fun
{
	printf("%d %d\n", i32(isVertical(Move.step(0, 3))), i32(isVertical(Move.step(1, 3))))
}
```

```output
1 0
```

## The is operator

`value is pattern` is a `bool` expression that is `true` when the pattern fits. It accepts every pattern a match arm does:

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
}

main: fun
{
	val x = 7
	val c = 'k'
	printf("%d %d %d %d\n", i32(x is 1..10), i32(x is > 7), i32(x is 7), i32(c is 'a'..='z'))

	val effect = Effect.hit(9)
	printf("%d %d\n", i32(effect is none), i32(effect is hit(> 5)))
}
```

```output
1 0 1 1
0 1
```

Bindings made by `is` can be used wherever the test is known to have passed: on the right of `&&`, and in the body of the `if` or `while` it controls. They can't be used in an `else` or after `||`. The loop here follows a chain of pointers; `@` takes an address and `*` reads through it, as [Pointers and raw memory](pointers.md) explains:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Node: enum
{
	end
	link(value: i32, next: ptr[Node])
}

main: fun
{
	var last = Node.end
	var middle = Node.link(2, @last)
	val first = Node.link(1, @middle)

	var current = first
	var total = 0
	while current is link(val value, val next)
	{
		total += value
		current = *next
	}

	if first is link(val value, _) && value > 0
		printf("first %d, total %d\n", value, total)
}
```

```output
first 1, total 3
```

```cella error
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
}

main: fun
{
	val effect = Effect.none
	if effect is hit(val n)
		printf("%d\n", n)
	else
		printf("%d\n", n)

	if effect is hit(val m) || m > 3
		printf("%d\n", m)
}
```

```errors
Symbol 'n' not found in this scope
Symbol 'm' not found in this scope
Symbol 'm' not found in this scope
```

## Guards

An arm can add a condition with `if` after its pattern. The arm runs only when the pattern fits and the condition is true; otherwise the next arms are tried. The condition can use the pattern's bindings:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Hit: enum
{
	miss
	hit(amount: i32)
}

score: fun(h: Hit) -> i32 => match h
{
	hit(val n) if n > 10 => 2
	hit(_) => 1
	miss => 0
}

main: fun
{
	printf("%d %d %d\n", score(Hit.hit(20)), score(Hit.hit(5)), score(Hit.miss))
}
```

```output
2 1 0
```

An arm with a guard doesn't count toward covering every value, since its condition can be false. It can't move values out of the input either:

```cella error
~ mod example
~
~ Buffer: own rec
~ {
~ 	id: i32
~
~ 	drop: op
~ 	{
~ 	}
~ }
~
Hit: enum
{
	miss
	hit(amount: i32)
}

Slot: own enum
{
	empty
	held(buffer: Buffer)
}

score: fun(h: Hit) -> i32 => match h
{
	hit(val n) if n > 10 => 2
	miss => 0
}

size: fun(slot: Slot) -> i32 => match slot
{
	held(val b) if b.id > 0 => 1
	else => 0
}

main: fun
{
}
```

```errors
This match doesn't handle every case of 'Hit': 'hit'
Cannot move values in arms with 'if'
```

## Record destructuring

A record pattern is the record's type name with fields in parentheses. Each field is named, followed by a pattern for its value; fields that aren't mentioned aren't checked. `val x` alone binds field `x` under its own name, and `field: val name` binds it under another:

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
}

where: fun(p: Point) -> i32 => match p
{
	Point(x: 0, y: 0) => 0
	Point(x: 0, val y) => 100 + y
	Point(x: > 10, y: val height) => 200 + height
	Point(val x, val y) => x * y
}

main: fun
{
	printf("%d %d %d %d\n", where(Point(0, 0)), where(Point(0, 7)), where(Point(11, 3)), where(Point(2, 3)))
}
```

```output
0 107 203 6
```

Record patterns nest inside each other and inside payloads, and a binding can follow a whole record pattern to name the record as well as its parts:

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
}

Enemy: rec
{
	health: i32
	position: Point
}

Shot: enum
{
	miss
	hit(at: Point, damage: i32)
}

state: fun(e: Enemy) -> i32 => match e
{
	Enemy(health: <= 0) => -1
	Enemy(health: 1..20 val hp, position: Point(x: 0)) => hp
	else => 99
}

score: fun(s: Shot) -> i32 => match s
{
	hit(Point(x: 0), val d) => d
	hit(Point(val x) val p, > 50) => x + p.y
	else => 0
}

main: fun
{
	printf("%d %d %d\n", state(Enemy(0, Point(1, 1))), state(Enemy(10, Point(0, 4))), state(Enemy(10, Point(3, 4))))
	printf("%d %d %d\n", score(Shot.hit(Point(0, 5), 7)), score(Shot.hit(Point(1, 2), 60)), score(Shot.miss))
}
```

```output
-1 10 99
7 3 0
```

Parentheses with no field names and no bindings, such as `Point(1, 1)`, are a value pattern compared with `==`, as shown in [Value patterns](#value-patterns). Enum payloads are always positional, so payload values can't be named. The compiler checks the fields and the type:

```cella error
~ mod example
~
Point: rec
{
	x: i32
	y: i32
}

Enemy: rec
{
	health: i32
	secret: pvt i32
}

Shot: enum
{
	miss
	hit(at: Point, damage: i32)
}

positional: fun(p: Point) -> i32 => match p
{
	Point(0, val y) => y
	else => 0
}

unknown: fun(p: Point) -> i32 => match p
{
	Point(z: 1) => 1
	else => 0
}

hidden: fun(e: Enemy) -> i32 => match e
{
	Enemy(secret: 1) => 1
	else => 0
}

wrongType: fun(p: Point) -> i32 => match p
{
	Enemy(health: 1) => 1
	else => 0
}

named: fun(s: Shot) -> i32 => match s
{
	hit(at: _, damage: val d) => d
	else => 0
}

main: fun
{
}
```

```errors
Expected a field name
Type 'Point' has no member 'z'
'secret' is private to its type
Expected 'Point'
Cannot name payload values
```

A record pattern that leaves fields unchecked doesn't cover every value, so a match expression over records usually needs a final arm that binds or ignores every field, or an `else`:

```cella error
~ mod example
~
Point: rec
{
	x: i32
	y: i32
}

onAxis: fun(p: Point) -> i32 => match p
{
	Point(x: 0) => 1
}

main: fun
{
}
```

```errors
This match doesn't handle every value of 'Point'
```

## Type tests

When the input is a trait object, a `dyn` value, a pattern can test which type it holds and bind it: `Circle c` fits when the value is a `Circle`. These patterns are covered in [Trait objects](trait-objects.md). On any other value, a type name alone isn't a pattern:

```cella error
~ mod example
~
Point: rec
{
	x: i32
}

main: fun
{
	val p = Point(3)
	val n = match p { Point => 1, else => 0 }
}
```

```errors
Cannot use types as values
```

## match mut

By default, a match takes its input or looks at it, as [Moving parts out](#moving-parts-out) explains. `match mut` borrows the input mutably instead, so every binding, `val` ones included, refers to the part inside the input, and assigning to a binding changes the input. `is` takes the same `mut`:

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
}

describe: fun(e: Effect) -> i32 => match e
{
	hit(val n) => n
	none => -1
}

boost: fun(mut e: Effect)
{
	match mut e
	{
		hit(val n) => n *= 2
		none => {}
	}
}

main: fun
{
	var effect = Effect.hit(5)
	match mut effect
	{
		hit(val n) => n += 1
		none => {}
	}

	printf("%d\n", describe(effect))

	if mut effect is hit(val n)
		n += 10

	boost(mut effect)
	printf("%d\n", describe(effect))
}
```

```output
6
32
```

A `var` binding under `match mut` is a copy, as it is elsewhere. The input of `match mut` must be something that can be borrowed mutably: a `var`, a `mut` parameter, a field or element of one, or a place reached through a pointer:

```cella error
~ mod example
~
Effect: enum
{
	none
	hit(amount: i32)
}

make: fun -> Effect => Effect.hit(1)

readOnly: fun(imm e: Effect)
{
	if mut e is hit(val n)
		n = 1
}

main: fun
{
	val fixed = Effect.hit(1)
	match mut fixed
	{
		hit(val n) => n += 1
		else => {}
	}

	match mut make()
	{
		hit(val n) => n += 1
		else => {}
	}
}
```

```errors
Cannot mutably borrow read-only parameters
Cannot mutably borrow values
Cannot mutably borrow unstored values
```

## Moving parts out

A match takes its input the way a declaration does. When the input is a value the function owns, such as a local variable, a parameter taken by value or a temporary, `val` and `var` bindings take the parts they bind: a part that can be copied is copied, and one that can't is moved out, which moves the whole input into the match. Parts that aren't bound are dropped at the end of the arm. [Ownership and destructors](ownership.md) explains moves and destructors.

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Buffer: own rec
{
	id: i32

	drop: op
	{
		printf("drop %d\n", self.id)
	}
}

Slot: own enum
{
	empty
	held(buffer: Buffer)
}

keep: fun(buffer: Buffer) -> i32 => buffer.id

main: fun
{
	val slot = Slot.held(Buffer(4))
	match slot
	{
		held(var buffer) =>
		{
			buffer.id += 10
			printf("kept %d\n", keep(buffer))
		}
		empty => {}
	}

	printf("end\n")
}
```

```output
drop 14
kept 14
end
```

After such a match, the input has been moved and can't be used. To look at a value without taking it, match `imm` of it, as in `match imm slot`; its bindings then borrow the parts. A value the function doesn't own, such as an `imm` or `mut` parameter, is only looked at the same way, so its bindings can't be moved on:

```cella error
~ mod example
~
Buffer: own rec
{
	id: i32

	drop: op
	{
	}
}

Slot: own enum
{
	empty
	held(buffer: Buffer)
}

take: fun(buffer: Buffer) -> i32 => buffer.id

used: fun -> i32
{
	val slot = Slot.held(Buffer(1))
	match slot
	{
		held(val buffer) => take(buffer)
		else => {}
	}

	ret match slot { held(val buffer) => buffer.id, else => 0 }
}

parameter: fun(imm slot: Slot) -> i32 => match slot
{
	held(val buffer) => take(buffer)
	else => 0
}

main: fun
{
}
```

```errors
Cannot use moved values
Cannot move pattern bindings
```

`match imm` keeps the input for later:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
~ Buffer: own rec
~ {
~ 	id: i32
~
~ 	drop: op
~ 	{
~ 		printf("drop %d\n", self.id)
~ 	}
~ }
~
Slot: own enum
{
	empty
	held(buffer: Buffer)
}

main: fun
{
	val slot = Slot.held(Buffer(3))
	match imm slot
	{
		held(val buffer) => printf("looked at %d\n", buffer.id)
		empty => {}
	}

	if imm slot is held(val buffer)
		printf("still %d\n", buffer.id)

	printf("end\n")
}
```

```output
looked at 3
still 3
end
drop 3
```

A temporary, such as the result of a call, belongs to the match the same way:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
~ Buffer: own rec
~ {
~ 	id: i32
~
~ 	drop: op
~ 	{
~ 		printf("drop %d\n", self.id)
~ 	}
~ }
~
Slot: own enum
{
	empty
	held(buffer: Buffer)
}

make: fun(id: i32) -> Slot => Slot.held(Buffer(id))

take: fun(buffer: Buffer) -> i32 => buffer.id

main: fun
{
	val id = match make(7)
	{
		held(val buffer) => take(buffer)
		empty => 0
	}

	printf("%d\n", id)
}
```

```output
drop 7
7
```

Record patterns work the same way: a `val` binding moves its field out of a record the match takes, and the fields that aren't bound are dropped at the end of the arm. A record with its own destructor can't have fields moved out of it, so bindings of its fields borrow them:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
~ Name: own rec
~ {
~ 	id: i32
~
~ 	drop: op
~ 	{
~ 		printf("drop %d\n", self.id)
~ 	}
~ }
~
Pair: own rec
{
	first: Name
	second: Name
}

main: fun
{
	val pair = Pair(Name(1), Name(2))
	match pair
	{
		Pair(val first) => printf("moved %d\n", first.id)
	}

	printf("end\n")
}
```

```output
moved 1
drop 2
drop 1
end
```

## when arms

A `when` block inside a match holds arms that exist only in builds where a flag is on, with an optional `else` block for the other builds. [Conditional compilation](conditional-compilation.md) covers flags.

## Float patterns

Floats can be matched like integers. Ranges and relational patterns are the usual way:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
classify: fun(f: f64) -> i32 => match f
{
	< 0.0 => -1
	0.0..1.0 => 0
	else => 1
}

main: fun
{
	printf("%d %d %d\n", classify(-2.5), classify(0.5), classify(3.0))
}
```

```output
-1 0 1
```

A float value pattern, such as `0.0` or `!= 2.0`, compares exactly, which rounding makes unreliable. The compiler accepts it with the warning "Float patterns compare exactly". Patterns never cover every float, so a match expression over floats needs an `else`:

```cella error
~ mod example
~
sign: fun(f: f64) -> i32 => match f
{
	< 0.0 => -1
	>= 0.0 => 1
}

main: fun
{
}
```

```errors
This match doesn't handle every value of 'f64'
```

## Order of evaluation

The input of a match is evaluated once, before any arm. Arms are then tried from top to bottom, and a pattern's values and guard are evaluated only when that arm is tried:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
trace: fun(n: i32) -> i32
{
	printf("trace %d\n", n)
	ret n
}

main: fun
{
	match trace(3)
	{
		trace(1) => printf("one\n")
		trace(3) => printf("three\n")
		trace(5) => printf("five\n")
	}
}
```

```output
trace 3
trace 1
trace 3
three
```
