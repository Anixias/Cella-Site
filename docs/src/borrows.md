# Borrows

A borrow refers to a value that is stored somewhere else. [Parameter modes](parameter-modes.md) showed borrows that last for one call: an `imm` or `mut` parameter borrows the caller's variable until the function returns. This chapter covers borrows as values of their own, kept in local variables, returned from functions and stored in records. The compiler checks one rule for all of them: a borrow can't be used after the value it borrows is gone.

## What a borrow is

In C, a function that wants to change a caller's variable takes its address, and code that wants a second name for a variable keeps a pointer to it:

```c
int score = 10;
int *points = &score;
*points += 5;
```

A Cella borrow does the same job. `mut score` borrows `score`, and the borrow can be kept in a variable:

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
	var score = 10
	val points = mut score
	points += 5
	printf("%d\n", score)
}
```

```output
15
```

Underneath, a borrow is an address, the same size as a pointer. It differs from a C pointer in three ways:

- A borrow always refers to a value. There is no null borrow.
- A borrow is used as if it were the value. `points += 5` changes `score`, with no `*` to write.
- The compiler knows which variable each borrow came from, and rejects any use of the borrow after that variable's value is moved or destroyed.

A borrow never owns what it refers to. When a borrow goes out of scope, nothing happens to the value it borrowed.

## Making a borrow

`imm place` makes a read-only borrow and `mut place` a writable one. The place can be a local variable, a parameter, a field, an array element, a module variable or a value behind a pointer:

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

main: fun
{
	var point = Point(1, 2)
	var scores = [10, 20, 30]
	val x = mut point.x
	val last = mut scores[2]
	val view = imm point
	x = 7
	last += 1
	printf("%d %d %d\n", view.x, view.y, scores[2])
}
```

```output
7 2 31
```

`view` borrows all of `point`, so it sees the change made through `x`.

A read-only borrow can't be written through, and can't be turned into a writable one. A `val` can't be borrowed with `mut`, and only a stored value can be borrowed: a call's result or a literal has no place to refer to.

```cella error
~ mod example
~
Point: rec
{
	x: i32
}

make: fun -> i32 => 4

main: fun
{
	var point = Point(1)
	val view = imm point
	view.x = 5
	val inner = mut view.x
	val fixed = 3
	val changed = mut fixed
	val result = imm make()
	val literal = imm 5
}
```

```errors
Cannot write through read-only borrows
Cannot mutably borrow through read-only borrows
Cannot mutably borrow values
Cannot borrow unstored values
Cannot borrow unstored values
```

## Using a borrow

A borrow reads as the value it refers to. Arithmetic, comparisons and `.` work on it directly, and passing it to a parameter with no mode passes a copy of the value. To lend it on to a `mut` or `imm` parameter, write the mode at the call, as for a variable:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
bump: fun(mut n: i32) => n += 1

twice: fun(n: i32) -> i32 => n * 2

main: fun
{
	var count = 1
	val counter = mut count
	bump(mut counter)
	val before = counter
	counter += 10
	printf("%d %d %d\n", count, before, twice(counter))
}
```

```output
12 2 24
```

`val before = counter` doesn't borrow again. `i32` is plain data, so the declaration copies the value `counter` refers to at that moment, and the later `+= 10` doesn't change it. To make a second borrow of the same place, write `imm counter` or `mut counter`.

## Borrow types

The type of `imm x` is `imm[T]` and the type of `mut x` is `mut[T]`, where `T` is the type of `x`. They can be written in declarations, results, fields, arrays and type arguments. In a declaration with an `imm[T]` type, the `imm` on the value can be left out; a `mut[T]` declaration needs its `mut` written:

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
	var a = 1
	val b = 2
	val writer: mut[i32] = mut a
	val reader: imm[i32] = a
	val both: array[imm[i32], 2] = [a, b]
	writer += 5
	printf("%d %d %d\n", reader, both[0], both[1])
}
```

```output
6 6 2
```

A `mut[T]` converts to an `imm[T]`, never the other way around. A borrow doesn't convert to its value's type either: `val n: i32 = imm a` is an error, while `val n: i32 = reader` copies the value.

```cella error
~ mod example
~
main: fun
{
	var a = 1
	val reader = imm a
	val writer: mut[i32] = reader
	val number: i32 = imm a
	val implicit: mut[i32] = a
}
```

```errors
Cannot convert type 'imm[i32]' to 'mut[i32]'
Cannot convert type 'imm[i32]' to 'i32'
Cannot mutably borrow values implicitly
```

Parameters never have borrow types. A parameter borrows through its mode instead, and the compiler suggests the mode to write:

```cella error
~ mod example
~
inc: fun(counter: mut[i32])
{
	counter += 1
}

look: fun(value: imm[i32]) -> i32 => value
~
~ main: fun
~ {
~ }
```

```errors
Cannot use borrow types for parameters
Cannot use borrow types for parameters
```

The first error has the hint "Did you mean 'mut counter: i32'?", and the second "Did you mean 'imm value: i32'?".

A borrow has no default, since it can't be null. A borrow variable declared without a value must be assigned before it's used, and a record with a borrow field has no `T()`:

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
	var r: imm[i32]
	printf("%d\n", r)
}
```

```errors
Cannot use uninitialized values
```

## Assigning to a borrow

What an assignment does to a borrow depends on what is assigned. Assigning a borrow repoints the variable at a new place. Assigning a value to a `mut` borrow writes through it, as any other use does:

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
	var a = 1
	var b = 2
	var target = mut a
	target = 10
	target = mut b
	target = 20
	printf("%d %d\n", a, b)
	var reader: imm[i32] = a
	printf("%d ", reader)
	reader = b
	printf("%d\n", reader)
}
```

```output
10 20
10 20
```

A read-only borrow can't be written through, so assigning a place to an `imm[T]` variable always repoints it, and `reader = b` borrows `b`. Assigning it something that isn't stored, like `reader = 5`, is "Cannot borrow unstored values". A borrow declared with `val` can't be repointed:

```cella error
~ mod example
~
main: fun
{
	var a = 1
	var b = 2
	val fixed = mut a
	fixed = mut b
}
```

```errors
Cannot reassign values
```

## Borrowing declarations

Plain data copies, so `val b = a` makes a copy when `a` is an `i32` or a record of numbers. A value whose type moves instead, such as a record with a destructor, can't be copied (see [Ownership and destructors](ownership.md#copying-and-moving)), so `val b = a` moves `a` into `b`. To borrow it instead, write `val b = imm a`:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Texture: own rec
{
	id: i32

	drop: op
	{
		printf("free %d\n", self.id)
	}
}

main: fun
{
	val texture = Texture(1)
	val same = imm texture
	printf("borrowed %d\n", same.id)
	val moved = texture
	printf("moved %d\n", moved.id)
}
```

```output
borrowed 1
moved 1
free 1
```

The texture is freed once, when `moved` goes out of scope. `same` never owned it.

A declaration moves only out of a place the function owns. A value it can't take, such as one behind an `imm` or `mut` parameter, a loop variable or a value reached through another borrow, is borrowed instead, so `val b = a` there makes `b` an `imm` borrow. Writing `imm` in such a declaration changes nothing, and the compiler gives the hint "Redundant 'imm'". The same rule applies wherever a value is bound: elements in `for` loops (see [Arrays](arrays.md)), `val` bindings in patterns (see [Pattern matching](pattern-matching.md)), and values reached through `*` and `[]` operators (see [Operators](operators.md)).

A borrowing declaration is a read-only borrow, so it can't be moved out of or written through, even when it's declared with `var`:

```cella error
~ mod example
~
Texture: own rec
{
	id: i32

	drop: op
	{
	}
}

take: fun(texture: Texture)
{
}

main: fun
{
	var texture = Texture(1)
	var same = imm texture
	same.id = 5
	take(same)
	val copy: Texture = same
}
```

```errors
Cannot write through read-only borrows
Cannot move borrowed values
Cannot move borrowed values
```

`var` on a borrow only allows repointing it.

## A borrow can't outlive its value

The compiler follows every borrow from where it's made to each place it's used. A use is an error when, on some path to it, the value the borrow came from has been:

- moved, by passing it to a parameter that takes it by value or by any other move;
- dropped at the end of its scope, including a scope inside a loop that ended in an earlier pass;
- reassigned, when its type has a destructor, since that drops the old value.

```cella error
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
	}
}

moved: fun
{
	val buffer = Buffer(1)
	val view = imm buffer
	val taken = buffer
	printf("%d\n", view.id)
}

dropped: fun
{
	var x = 0
	var longest: imm[i32] = x
	{
		val temp = 5
		longest = temp
	}

	printf("%d\n", longest)
}

reassigned: fun
{
	var buffer = Buffer(1)
	val first = imm buffer
	buffer = Buffer(2)
	printf("%d\n", first.id)
}

looped: fun
{
	val x = 0
	var last: imm[i32] = x
	for i in 0..3
	{
		printf("%d\n", last)
		val local = i
		last = local
	}
}
~
~ main: fun
~ {
~ }
```

```errors
Cannot use borrows of moved values
Cannot use borrows of dropped values
Cannot use borrows of reassigned values
Cannot use borrows of dropped values
```

Each error has a note with the line where the value was moved, dropped or reassigned. In the loop, the note says the value was dropped "in an earlier iteration".

Only uses are checked. A borrow whose value is gone is fine as long as nothing reads it again, and repointing it at a live value makes it usable again:

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
	val start = 10
	var current: imm[i32] = start
	for i in 0..3
	{
		val doubled = i * 2
		current = doubled
		printf("%d ", current)
	}

	current = start
	printf("%d\n", current)
}
```

```output
0 2 4 10
```

The check follows fields and elements separately. A borrow of one field stays valid when another field is moved out:

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

Pair: own rec
{
	first: Buffer
	second: Buffer
}

main: fun
{
	val pair = Pair(Buffer(1), Buffer(2))
	val first = imm pair.first
	val second = pair.second
	printf("%d %d\n", first.id, second.id)
}
```

```output
1 2
drop 2
drop 1
```

Assigning a new value to plain data runs no destructor, so it doesn't end borrows of it. The borrow sees whatever the variable holds when it's read:

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

main: fun
{
	var point = Point(1, 2)
	val view = imm point
	point = Point(3, 4)
	printf("%d %d\n", view.x, view.y)
}
```

```output
3 4
```

## Returning borrows

A function can return a borrow. The returned borrow must come from one of these:

- an `imm` or `mut` parameter, directly or through a call the parameter was lent to;
- a borrow that a parameter holds, such as a field of a `ref rec` parameter;
- a module variable or value.

The caller then treats the result as a borrow of the arguments it lent:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Enemy: rec
{
	hp: i32
	kills: i32
}

stronger: fun(imm a: Enemy, imm b: Enemy) -> imm[Enemy]
{
	if a.hp >= b.hp
		ret imm a
	ret imm b
}

kills: fun(mut enemy: Enemy) -> mut[i32] => mut enemy.kills

main: fun
{
	var bat = Enemy(3, 0)
	val rat = Enemy(5, 0)
	val best = stronger(imm bat, imm rat)
	kills(mut bat) += 2
	val count = mut kills(mut bat)
	count += 1
	printf("%d %d\n", best.hp, bat.kills)
}
```

```output
5 3
```

A call that returns a `mut[T]` is a place: it can be assigned to, as in `kills(mut bat) += 2`, or borrowed again with `mut`.

Every other source is an error, since the value would be gone once the function returns. A parameter with no mode is the function's own value, a copy or a value moved in for the function to destroy, so it doesn't outlive the call:

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

Holder: ref rec
{
	buffer: imm[Buffer]
}

make: fun(id: i32) -> Buffer => Buffer(id)

local: fun -> imm[i32]
{
	val x = 5
	ret imm x
}

owned: fun(buffer: Buffer) -> imm[Buffer] => imm buffer

copied: fun(a: i32) -> imm[i32] => imm a

temporary: fun -> Holder => Holder(make(3))
~
~ main: fun
~ {
~ }
```

```errors
Cannot return borrows of local variables
Cannot return borrows of by-value parameters
Cannot return borrows of by-value parameters
Cannot return borrows of unstored values
```

In a method, a returned borrow may come only from `self`:

```cella error
~ mod example
~
Enemy: rec
{
	hp: i32
}

Referee: rec
{
	best: Enemy

	leader: fun(imm self) -> imm[Enemy] => imm self.best

	pick: fun(imm self, imm a: Enemy, imm b: Enemy) -> imm[Enemy]
	{
		if a.hp >= b.hp
			ret imm a
		ret imm b
	}
}
~
~ main: fun
~ {
~ }
```

```errors
Cannot return borrows of parameters other than 'self'
Cannot return borrows of parameters other than 'self'
```

The caller's side follows the same rules as any other borrow. Here `leader` borrows `referee`, so replacing `referee` ends it:

```cella error
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Name: own rec
{
	id: i32

	drop: op
	{
	}
}

Referee: own rec
{
	best: Name

	leader: fun(imm self) -> imm[Name] => imm self.best
}

main: fun
{
	var referee = Referee(Name(1))
	val leader = referee.leader()
	referee = Referee(Name(2))
	printf("%d\n", leader.id)
}
```

```errors
Cannot use borrows of reassigned values
```

Module values live for the whole program, so a function can return a borrow of one:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
limit: val i32 = 3

maxLevel: fun -> imm[i32] => imm limit

main: fun
{
	printf("%d\n", maxLevel())
}
```

```output
3
```

## Records that hold borrows

A record with a field that holds a borrow is declared `ref rec`, and an enum with such a payload `ref enum`. Types that hold borrows are the borrow types, `str` (it borrows its bytes; see [Bool, char and strings](text.md)), `ref` records and enums, arrays of any of these, and closures kept as `ref fun` (see [Function values and closures](closures.md)).

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Tally: ref rec
{
	count: mut[i32]
	step: i32
}

Target: ref enum
{
	none
	unit(health: imm[i32])
}

bump: fun(mut tally: Tally) => tally.count += tally.step

describe: fun(target: Target) -> i32 => match target
{
	unit(val health) => health
	none => -1
}

main: fun
{
	var kills = 2
	var tally = Tally(mut kills, 5)
	bump(mut tally)
	bump(mut tally)
	val hp = 40
	printf("%d %d %d\n", kills, describe(Target.unit(hp)), describe(Target.none))
}
```

```output
12 40 -1
```

A `mut` field takes its argument with `mut`, as `Tally(mut kills, 5)` does. An `imm` field takes a place with or without `imm`. A plain `rec` or `enum` can't hold borrows, and the compiler suggests the fix. Unions can't hold borrows at all.

```cella error
~ mod example
~
Label: rec
{
	text: str
}

Target: enum
{
	none
	unit(health: imm[i32])
}

Raw: union
{
	whole: imm[i32]
	bits: u64
}
~
~ main: fun
~ {
~ }
```

```errors
Cannot store borrows in records that aren't 'ref'
Cannot store borrows in enums that aren't 'ref'
Cannot store borrows in unions
```

The hints read "Did you mean 'Label: ref rec'?" and "Did you mean 'Target: ref enum'?".

A `ref` value borrows whatever its fields borrow, so it follows the rule of the previous sections: it can't be used after those values are gone. A `ref rec` can have a destructor, and the destructor can use the borrows. This makes a guard that undoes something when its scope ends:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Scope: own ref rec
{
	depth: mut[i32]

	new: op(mut depth: i32)
	{
		depth += 1
		self.depth = mut depth
	}

	drop: op
	{
		self.depth -= 1
	}
}

main: fun
{
	var depth = 0
	{
		val outer = Scope(mut depth)
		printf("%d ", depth)
		{
			val inner = Scope(mut depth)
			printf("%d ", depth)
		}

		printf("%d ", depth)
	}

	printf("%d\n", depth)
}
```

```output
1 2 1 0
```

The destructor counts as a use, so the value a `Scope` borrows must still be there when the scope's destructor runs. Building a `ref` value from a temporary is an error, since the temporary is gone at the end of the statement:

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

Holder: ref rec
{
	buffer: imm[Buffer]
}

make: fun(id: i32) -> Buffer => Buffer(id)

temporary: fun -> i32
{
	val holder = Holder(make(3))
	ret holder.buffer.id
}
~
~ main: fun
~ {
~ }
```

```errors
Cannot borrow unstored values
```

The first error points at the closing brace of `early`, with the notes "'scope' is dropped here" and the line where `depth` was moved.

## View records

A `ref rec` or `ref enum` whose fields can all be copied is a view record. A view record is a window onto something else: borrowing from it means borrowing what it borrows, not the record. The difference shows in a method that hands out borrows. This lexer borrows an array, and each token it returns borrows an element of that array:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Token: ref rec
{
	value: imm[i32]
	index: usize
}

Lexer: ref rec
{
	items: imm[array[i32, 6]]
	offset: usize

	next: fun(mut self) -> Token
	{
		val token = Token(imm self.items[self.offset], self.offset)
		self.offset += 1
		ret token
	}
}

main: fun
{
	val items = [10, 20, 30, 40, 50, 60]
	var first = Lexer(items, 0)
	val a = first.next()
	var kept = first.next()
	{
		var inner = Lexer(items, 4)
		kept = inner.next()
	}

	printf("%d %d\n", a.value, kept.value)
}
```

```output
10 50
```

`next` takes `mut self`, so its token could have borrowed the lexer. Since `Lexer` is a view record, the token borrows `items` instead, and `kept` stays valid after `inner` is gone. Several tokens can be held at once, and a view record can be copied freely; every copy borrows the same values.

The same rule lets a function return a borrow that a view record parameter holds, even when the parameter is a copy:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Tally: ref rec
{
	count: mut[i32]
}

counter: fun(tally: Tally) -> mut[i32] => tally.count

main: fun
{
	var kills = 1
	val tally = Tally(mut kills)
	counter(tally) += 4
	printf("%d\n", kills)
}
```

```output
5
```

The other side of this rule is that a view record can't lend out its own fields. A method returning a borrow of `self` or of one of its fields is an error:

```cella error
~ mod example
~
Lexer: ref rec
{
	items: imm[array[i32, 6]]
	offset: usize

	offsetRef: fun(mut self) -> mut[usize] => mut self.offset

	itself: fun(mut self) -> mut[Lexer] => mut self
}
~
~ main: fun
~ {
~ }
```

```errors
Cannot return borrows of view records
Cannot return borrows of view records
```

A `ref rec` with a field that can't be copied, such as a field whose type has a destructor, isn't a view record. Borrows taken from it borrow the record itself, so its methods can return borrows of its fields:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Guard: own rec
{
	drop: op
	{
		printf("released\n")
	}
}

Counter: own ref rec
{
	items: imm[array[i32, 3]]
	count: i32
	guard: Guard

	countRef: fun(mut self) -> mut[i32] => mut self.count
}

main: fun
{
	val items = [1, 2, 3]
	var counter = Counter(items, 7, Guard())
	val count = mut counter.countRef()
	count += 1
	printf("%d\n", counter.count)
}
```

```output
8
released
```

## Storing borrows

A local variable can hold any borrow, under the rules above. Storing a borrow where the caller can see it, in a `mut` parameter or a constructor's `self`, is limited, so that the caller's borrows stay valid after the call.

A `mut` parameter can receive only borrows that came from that same parameter. A function can rearrange what its argument borrows, but can't make it borrow something new:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Token: ref rec
{
	text: str
	rest: str
}

swap: fun(mut token: Token)
{
	val text = token.text
	token.text = token.rest
	token.rest = text
}

show: fun(text: str)
{
	printf("%.*s\n", i32(text.byteLength), text.data)
}

main: fun
{
	var token = Token("first", "second")
	swap(mut token)
	show(token.text)
}
```

```output
second
```

Storing a borrow from anywhere else, including another parameter, is an error, and so is storing through a borrow that a parameter holds:

```cella error
~ mod example
~
Token: ref rec
{
	text: str
	rest: str
}

Pair: ref rec
{
	token: mut[Token]
}

Tally: ref rec
{
	count: mut[i32]
}

retarget: fun(mut token: Token, other: str)
{
	token.text = other
}

repoint: fun(mut tally: Tally)
{
	var local = 1
	tally.count = mut local
}

retargetHeld: fun(pair: Pair, other: str)
{
	pair.token.text = other
}
~
~ main: fun
~ {
~ }
```

```errors
Cannot store new borrows in 'mut' parameters
Cannot store new borrows in 'mut' parameters
Cannot store borrows through borrows from parameters
```

A constructor's `self` is checked like a result. It can store borrows of `imm` and `mut` parameters, and borrows that its parameters hold, like a `str` parameter's bytes. Borrows of locals and by-value parameters would end when the constructor returns:

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

Counter: ref rec
{
	count: imm[i32]

	new: op
	{
		val local = 1
		self.count = imm local
	}
}

Gauge: ref rec
{
	level: imm[i32]

	new: op(level: i32)
	{
		self.level = imm level
	}
}

Viewer: ref rec
{
	view: imm[Buffer]

	new: op(buffer: Buffer)
	{
		self.view = imm buffer
	}
}
~
~ main: fun
~ {
~ }
```

```errors
Cannot store borrows of local variables in 'self'
Cannot store borrows of by-value parameters in 'self'
Cannot store borrows of by-value parameters in 'self'
```

A destructor can't store new borrows in `self` either: "Cannot store new borrows in 'self'".

## A value can't borrow itself

A value can't hold a borrow of its own storage. Moving the value would move the borrow along with it, still pointing at the old place:

```cella error
~ mod example
~
Pair: ref rec
{
	value: i32
	alias: mut[i32]
}

main: fun
{
	var spare = 0
	var pair = Pair(1, mut spare)
	pair.alias = mut pair.value
}
```

```errors
Cannot store borrows of values in themselves
```

The same holds in constructors (`self.alias = mut self.value`), between elements of one array, and through payloads. Structures that point into themselves, like a circular list, use [pointers](pointers.md), which the compiler doesn't check.

## Module variables can't hold borrows

A module variable or static field declared with `var` can't hold a borrow, since it outlives every local. A module `val` can hold one only when its value is a constant, like a string literal:

```cella error
~ mod example
~
title: val str = "Cella"
name: var str = "a"
limit: val i32 = 4
pointed: val imm[i32] = limit
~
~ main: fun
~ {
~ }
```

```errors
Cannot store borrows in module variables
Cannot store borrows in module values
```

Borrows of module variables can be made, kept in locals and returned, as `maxLevel` showed above. They follow the same rules: reassigning a module variable whose type has a destructor ends the borrows of it.

## Borrows in closures

A lambda that uses a local variable captures it by reference, which makes the closure a borrow of that variable. The rules in this chapter apply to it: calling a closure after a variable it captured is moved or out of scope is an error. [Function values and closures](closures.md) covers the details.

## What isn't checked

The compiler checks that a borrow never outlives the value it borrows. It doesn't check how borrows overlap. Several `mut` borrows of one variable can exist at once, and the variable can be written while an `imm` borrow of it is held:

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
	var x = 1
	val reader = imm x
	val first = mut x
	val second = mut x
	first += 100
	second += 1000
	printf("%d %d\n", x, reader)
}
```

```output
1101 1101
```

The same goes for calls: one variable can be passed to two `mut` parameters (see [Parameter modes](parameter-modes.md#aliasing-isnt-checked)).

An `imm` borrow promises only that code using it doesn't write through it. The value can still change through other names.

Also unchecked, as in C:

- Invalidation. A borrow of memory reached through a pointer, such as an element of a heap buffer, isn't tied to that memory. Freeing or reallocating it leaves the borrow pointing at freed memory. See [Pointers and raw memory](pointers.md).
- Data races. Nothing stops two threads from using borrows of the same value at once. See [Atomics](atomics.md).
