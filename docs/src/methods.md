# Methods and properties

A type's body can hold functions as well as fields. Functions that work on a value of the type are methods, and functions that belong to the type without a value are static functions. Properties look like fields but run code when they're read or written. This chapter covers all three, the static fields and constants a type can hold, and the visibility words that hide members from code outside the type.

The examples use records. Methods, static members, properties and member visibility work the same way in enums, as the last section says.

## Methods

A method is a function declared inside a type whose first parameter is `self`. It's called on a value with a dot, and `self` is that value:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Rect: rec
{
	width: i32
	height: i32

	area: fun(self) -> i32 => self.width * self.height

	grow: fun(mut self, amount: i32)
	{
		self.width += amount
		self.height += amount
	}
}

main: fun
{
	var r = Rect(2, 3)
	printf("%d\n", r.area())
	r.grow(1)
	printf("%d\n", r.area())
}
```

```output
6
12
```

`self` has no type written; it's always the type the method is declared in. Fields and other methods are reached through it, as `self.width` and `self.area()`. A bare name inside a method never means a field or a method:

```cella error
~ mod example
~
Counter: rec
{
	value: i32

	bump: fun(mut self) => self.value += 1

	twice: fun(mut self)
	{
		bump()
		self.bump()
	}
}

main: fun
{
}
```

```errors
Cannot call methods without a receiver
```

Members can be declared in any order, and a method can call methods declared after it, or itself. Methods can be overloaded like functions (see [Functions](functions.md)): `scaled: fun(self, factor: i32)` and `scaled: fun(self, factor: f64)` can live side by side.

### Receivers

`self` is the method's receiver, and like any parameter it has a mode. The mode says what the method can do with the value it's called on:

| Receiver | `self` is | The method can |
| --- | --- | --- |
| `self` | the value itself: a copy, or the value moved into the method | read, change and consume it |
| `imm self` | a read-only borrow of the value | read it |
| `mut self` | a mutable borrow of the value | read and change it |

The call is written the same way for every receiver: `r.area()`, `r.grow(1)`. Unlike other arguments, the receiver never needs `imm` or `mut` at the call site. [Parameter modes](parameter-modes.md) explains the modes in general.

A `mut self` method changes the value it's called on, so the value must be something that can change, such as a `var`:

```cella error
~ mod example
~
Rect: rec
{
	width: i32
	height: i32

	grow: fun(mut self, amount: i32) => self.width += amount
}

main: fun
{
	val r = Rect(2, 3)
	r.grow(1)
}
```

```errors
Cannot mutably borrow values
```

It can't be called on a temporary either, such as `Rect(2, 3).grow(1)`, since the change would be lost; that is the error "Cannot mutably borrow unstored values". The other receivers work on temporaries.

With `imm self`, the method can't change the value. Assigning to one of its fields is an error:

```cella error
~ mod example
~
Rect: rec
{
	width: i32
	height: i32

	reset: fun(imm self)
	{
		self.width = 0
	}
}

main: fun
{
}
```

```errors
Cannot reassign read-only parameters
```

A `self` method has the value to itself, so it can change it; for a type that copies, the caller's value stays as it was.

### Copy or borrow

For a type that copies, `self` and `imm self` both read the value, and the difference only shows when the value changes during the call. A copy keeps the value as it was when the call started, while a borrow sees it as it is now:

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

	before: fun(self, mut x: i32) -> i32
	{
		x = 99
		ret self.x
	}

	after: fun(imm self, mut x: i32) -> i32
	{
		x = 99
		ret self.x
	}
}

main: fun
{
	var p = Point(1, 2)
	val first = p.before(mut p.x)
	p.x = 1
	val second = p.after(mut p.x)
	printf("%d %d\n", first, second)
}
```

```output
1 99
```

A type that can't be copied moves into a `self` method instead, so a method that only reads such a value takes `imm self`.

### Consuming the value

A `self` method on a type that can't be copied takes the value over. The value is dropped at the end of the method unless the method moves it on, and the caller can't use it afterwards:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Letter: own rec
{
	id: i32

	send: fun(self) -> i32
	{
		printf("sending %d\n", self.id)
		ret self.id
	}

	drop: op
	{
		printf("drop %d\n", self.id)
	}
}

main: fun
{
	val letter = Letter(7)
	val sent = letter.send()
	printf("sent %d\n", sent)
}
```

```output
sending 7
drop 7
sent 7
```

```cella error
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
~ Letter: own rec
~ {
~ 	id: i32
~
~ 	send: fun(self) -> i32 => self.id
~
~ 	drop: op
~ 	{
~ 	}
~ }
~
main: fun
{
	val letter = Letter(7)
	letter.send()
	printf("%d\n", letter.id)
}
```

```errors
Cannot use moved values
```

Only a value the caller owns can be consumed. Through an `imm` or `mut` borrow, such a method can't be called:

```cella error
~ mod example
~
~ Letter: own rec
~ {
~ 	id: i32
~
~ 	send: fun(self) -> i32 => self.id
~
~ 	drop: op
~ 	{
~ 	}
~ }
~
post: fun(imm letter: Letter) -> i32 => letter.send()

main: fun
{
}
```

```errors
Cannot move read-only parameters
```

A method that consumes a value with a destructor can take a field out of `self` with `own self.field`. The value then counts as taken apart: its destructor doesn't run at the end of the method, and only the fields left in it are destroyed. This is how a value hands over what it holds:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
~ Letter: own rec
~ {
~ 	id: i32
~
~ 	drop: op
~ 	{
~ 		printf("drop %d\n", self.id)
~ 	}
~ }
~
Envelope: own rec
{
	letter: Letter

	drop: op
	{
		printf("drop envelope\n")
	}

	open: fun(self) -> Letter
	{
		val letter = own self.letter
		printf("opened\n")
		ret letter
	}
}

main: fun
{
	val envelope = Envelope(Letter(3))
	val letter = envelope.open()
	printf("got %d\n", letter.id)
}
```

```output
opened
got 3
drop 3
```

Without `own`, `val letter = self.letter` would only look at the field, since a field of a value with a destructor can't be moved out any other way.

### Calling through pointers and borrows

A method call through a pointer or a borrow reaches the value it points to, like `->` in C:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
~ Rect: rec
~ {
~ 	width: i32
~ 	height: i32
~
~ 	area: fun(self) -> i32 => self.width * self.height
~
~ 	grow: fun(mut self, amount: i32)
~ 	{
~ 		self.width += amount
~ 		self.height += amount
~ 	}
~ }
~
enlarge: fun(mut rect: Rect) => rect.grow(2)

main: fun
{
	var r = Rect(1, 1)
	val pointer = @r
	pointer.grow(1)
	enlarge(mut r)
	printf("%d\n", r.area())
}
```

```output
16
```

[Pointers and raw memory](pointers.md) covers `@` and pointers.

## Static functions

A function in a type's body without a `self` parameter is a static function. It belongs to the type rather than to a value, and it's called through the type's name. Static functions are the usual way to give a constructor a name:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
origin: fun -> i32 => 99

Point: rec
{
	x: i32
	y: i32

	origin: fun -> Point => Point(0, 0)

	diagonal: fun(n: i32) -> Point => Point(n, n)

	reset: fun(mut self)
	{
		val home = origin()
		self.x = home.x
		self.y = home.y
	}
}

main: fun
{
	var p = Point.diagonal(3)
	printf("%d %d\n", p.x, p.y)
	p.reset()
	printf("%d %d %d\n", p.x, p.y, origin())
}
```

```output
3 3
0 0 99
```

Inside the type, a static function can be called without the type's name, and it hides a module-level function with the same name: `origin()` in `reset` calls `Point.origin`, while `origin()` in `main` calls the function outside the type.

Static functions are called through the type and methods through a value, never the other way around. A static function has no `self` to use:

```cella error
~ mod example
~
Counter: rec
{
	value: i32

	bump: fun(mut self) => self.value += 1

	copyOf: fun -> Counter => Counter(self.value)
}

main: fun
{
	var c = Counter(1)
	c.copyOf()
	Counter.bump()
}
```

```errors
Cannot use 'self' in static functions
Cannot use static functions through values
Cannot use methods through types
```

Since the two are called differently, a method and a static function can share a name:

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

	sum: fun(self) -> i32 => self.x + self.y

	sum: fun(a: Point, b: Point) -> Point => Point(a.x + b.x, a.y + b.y)
}

main: fun
{
	val p = Point.sum(Point(1, 2), Point(3, 4))
	printf("%d\n", p.sum())
}
```

```output
10
```

## Static fields and constants

A `var` or `val` member is a static field: one variable shared by the whole program, stored once rather than in each value. It's written like a module-level variable, with a type and an initial value, and it's reached through the type's name, or without it inside the type. A `const` member is a named constant in the same way:

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
	maxHealth: const i32 = 50
	spawned: var i32 = 0
	speed: val f64 = 1.5

	health: i32

	spawn: fun -> Enemy
	{
		spawned += 1
		ret Enemy(maxHealth)
	}
}

main: fun
{
	val a = Enemy.spawn()
	Enemy.spawn()
	printf("%d %d %d %.1f\n", a.health, Enemy.spawned, Enemy.maxHealth, Enemy.speed)
	printf("%zu\n", sizeOf(Enemy))
}
```

```output
50 2 50 1.5
4
```

`sizeOf(Enemy)` counts only `health`; static fields and constants take no space in the values. The initial value must be a constant, and a `val` can't be changed after it. [Variables and constants](variables.md) covers the difference between `val`, `var` and `const`.

A static field belongs to the type, not to a value, so it can't be reached through one:

```cella error
~ mod example
~
Enemy: rec
{
	maxHealth: val i32 = 50
	health: i32

	isFull: fun(self) -> bool => self.health == self.maxHealth
}

main: fun
{
}
```

```errors
Cannot use static fields through values
```

The other rules for static fields:

```cella error
~ mod example
~
~ now: fun -> i32 => 1
~
Clock: rec
{
	started: val i32 = now()
	ticks: val i32
	limit: val i32 = 10
}

main: fun
{
	Clock.limit = 20
}
```

```errors
The initial value of 'started' must be a constant
Expected '=' and an initial value
Cannot reassign values
```

## Properties

A property is a member that is used like a field but runs a getter when it's read and a setter when it's written. `prop` declares one with both accessors:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
clamp: fun(value: i32, low: i32, high: i32) -> i32
{
	if value < low
		ret low
	else if value > high
		ret high

	ret value
}

Unit: rec
{
	hp: i32
	maxHp: i32

	health: prop i32
	{
		get(self) => self.hp
		set(mut self, value)
		{
			self.hp = clamp(value, 0, self.maxHp)
		}
	}
}

main: fun
{
	var hero = Unit(30, 30)
	hero.health -= 50
	printf("%d\n", hero.health)
	hero.health = 500
	printf("%d\n", hero.health)
}
```

```output
0
30
```

`hero.health = v` calls the setter with `v` as `value`. A compound assignment such as `hero.health -= 50` calls the getter, then the setter with the result. Every other use calls the getter.

Inside `prop`, the accessors' types can be left out, since they come from the property's type. When they're written they must match it: `get(self) -> i32` and `set(mut self, value: i32)`. Either accessor's body can be `=> expr` or a block.

A `prop` needs both accessors, and each at most once:

```cella error
~ mod example
~
Unit: rec
{
	hp: i32

	health: prop i32
	{
		get(self) => self.hp
	}
}

main: fun
{
}
```

```errors
'health' needs a setter
```

### Getters and setters on their own

A property with only one accessor is written as a standalone `get` or `set` member, with its types written out. A getter takes only the receiver and returns a value; a setter takes the receiver and one value and returns nothing:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Unit: rec
{
	hp: i32
	volume: i32

	isAlive: get(self) -> bool => self.hp > 0

	loudness: set(mut self, value: i32)
	{
		self.volume = value * 10
	}
}

main: fun
{
	var hero = Unit(5, 0)
	hero.loudness = 3
	if hero.isAlive
		printf("alive, volume %d\n", hero.volume)
}
```

```output
alive, volume 30
```

A getter-only property can't be written and a setter-only property can't be read. That includes compound assignments, which do both:

```cella error
~ mod example
~
~ Unit: rec
~ {
~ 	hp: i32
~ 	volume: i32
~
~ 	isAlive: get(self) -> bool => self.hp > 0
~
~ 	loudness: set(mut self, value: i32)
~ 	{
~ 		self.volume = value * 10
~ 	}
~ }
~
main: fun
{
	var hero = Unit(5, 0)
	hero.isAlive = false
	val level = hero.loudness
	hero.loudness += 1
}
```

```errors
Cannot reassign read-only properties
Cannot read write-only properties
Cannot read write-only properties
```

One name has one form: two standalone accessors with the same name conflict, and so do a property and a field. For a property with both a getter and a setter, use `prop`.

### Accessor rules

Either accessor's receiver can be `self`, `imm self` or `mut self`, and `self` only for a type that copies. A setter usually takes `mut self`, since it changes the value. A getter with `mut self` can change the value while it's read, so reading it needs a value that can change, as with a `mut self` method. Getters take no parameters, and setters take exactly one, which can't have a mode:

```cella error
~ mod example
~
Unit: rec
{
	hp: i32

	scaled: get(self, factor: i32) -> i32 => self.hp * factor

	volume: set(mut self) => self.hp = 0

	speed: set(mut self, value: i32) -> i32 => 0
}

main: fun
{
}
```

```errors
Getters cannot take parameters
Setters must take one parameter
Setters cannot return values
```

A property isn't stored anywhere, so it can't be borrowed, moved or have its address taken. Passing `mut hero.health` to a function is the error "Cannot mutably borrow properties". Read it into a variable, change that, and assign it back.

An assignment to a property has no value, so `val x = (hero.health = 5)` is an error, unlike an assignment to a field.

### Static properties

Without a receiver, an accessor is static: it belongs to the type, like a static function, and it's used through the type's name:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Unit: rec
{
	created: var i32 = 0

	hp: i32

	count: get -> i32 => created

	resetCount: set(value: i32)
	{
		created = value
	}

	make: fun(hp: i32) -> Unit
	{
		created += 1
		ret Unit(hp)
	}
}

main: fun
{
	Unit.make(10)
	Unit.make(20)
	printf("%d\n", Unit.count)
	Unit.resetCount = 0
	printf("%d\n", Unit.count)
}
```

```output
2
0
```

A `prop` is either static or not: both accessors take a receiver, or neither does. "Cannot combine static and instance accessors" is the error for mixing them.

## Visibility

Every member is visible wherever its type is, unless it says otherwise. Two words restrict a member:

| Word | The member is visible |
| --- | --- |
| `pvt` | only inside its type: in the type's own methods, static functions, constructors, properties and operators |
| `mod` | anywhere in its module, including the module's other files |

The word goes after the colon, before the rest of the member: `hp: pvt i32`, `helper: pvt fun(self) -> i32`, `new: pvt op(value: i32)`.

```cella error
~ mod example
~
Wallet: rec
{
	cents: pvt i64

	new: pvt op(cents: i64)
	{
		self.cents = cents
	}

	empty: fun -> Wallet => Wallet(0)

	add: fun(mut self, cents: i64) => self.cents += self.checked(cents)

	checked: pvt fun(self, cents: i64) -> i64 => cents
}

main: fun
{
	var w = Wallet.empty()
	w.add(250)
	w.cents = 1000
	w.checked(5)
	val other = Wallet(5)
}
```

```errors
'cents' is private to its type
'checked' is private to its type
'new' is private to its type
```

A private constructor, as here, means values can only be made by the type's own code, such as the static function `empty`.

The built-in constructors follow the fields. Outside the type, the field-by-field constructor can't set a `pvt` or `pvt set` field (see [Read-only fields](#read-only-fields)), so it's unavailable there; `T()` still works when the record has a legal default.

There is no `pub` for members: a member of a `pub` type is exported along with it. [Modules and visibility](modules.md) covers visibility for top-level declarations, and the rule that a member can't use a type less visible than itself in its signature.

### Read-only fields

`pvt set` makes a field readable everywhere but writable only inside its type. `mod set` makes it writable only inside its module. This is the usual way to expose a value that the type keeps consistent:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Stack: rec
{
	items: pvt array[i32, 8]
	count: pvt set usize

	push: fun(mut self, value: i32)
	{
		self.items[self.count] = value
		self.count += 1
	}
}

main: fun
{
	var s = Stack()
	s.push(4)
	s.push(5)
	printf("%zu\n", s.count)
}
```

```output
2
```

Writing the field outside the type, or anything that could change it, such as passing it as `mut` or calling a `mut self` method on it, is an error:

```cella error
~ mod example
~
~ addOne: fun(mut value: usize) => value += 1
~
~ Stack: rec
~ {
~ 	items: pvt array[i32, 8]
~ 	count: pvt set usize
~ }
~
main: fun
{
	var s = Stack()
	s.count = 0
	s.count += 1
	addOne(mut s.count)
}
```

```errors
'count' is read-only outside its type
'count' is read-only outside its type
'count' is read-only outside its type
```

`pvt set` and `mod set` work on fields and on `var` static fields. A `val` can't be written anywhere, so they aren't allowed on one, and they aren't allowed on functions.

### Restricting one accessor

In a `prop`, one accessor can be restricted, which makes the property read-only or write-only outside the type:

```cella error
~ mod example
~
Unit: rec
{
	hp: pvt i32

	health: prop i32
	{
		get(self) => self.hp
		pvt set(mut self, value)
		{
			self.hp = value
		}
	}
}

main: fun
{
	var u = Unit()
	val h = u.health
	u.health = 3
}
```

```errors
'health' is read-only outside its type
```

Only one of the two can be restricted; restricting both is the error "Cannot restrict both accessors". To hide the whole property, put the word on the property: `health: pvt prop i32`.

### `mod` members

A `mod` member is visible to every file of its module, and hidden from other modules. Here `game.ce` declares a module `game`, and `main.ce` uses it:

```cella error group=modVisibility file=game.ce
mod game

Score: rec
{
	points: mod set i32
	bonus: mod i32

	add: fun(mut self, points: i32) => self.points += points + self.bonus
}

reward: fun(mut score: Score) => score.bonus = 5
```

```cella error group=modVisibility file=main.ce
~ mod example
~
use game.*

main: fun
{
	var score = Score()
	reward(mut score)
	score.add(10)
	score.points = 0
}
```

```errors group=modVisibility
'points' is read-only outside its module
```

`reward`, in the same module as `Score`, can write `bonus`. In `main`, even reading it is an error: "'bonus' is private to its module". [Modules and visibility](modules.md) covers modules and `use`.

### Visibility blocks

When several neighboring members share a visibility, a `pvt { }` or `mod { }` block inside the type applies it to all of them:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Shape: rec
{
	width: i32
	height: i32

	describe: fun(self) -> i32 => self.area() + self.edges()

	pvt
	{
		area: fun(self) -> i32 => self.width * self.height

		edges: fun(self) -> i32 => 4
	}
}

main: fun
{
	printf("%d\n", Shape(2, 3).describe())
}
```

```output
10
```

Members in a block can't repeat or contradict its word: a `pvt` block can't hold `mod` members, and a `mod` block can't hold `pvt` ones. A `mod` block can still hold `pvt set` fields. A destructor is never restricted, so it can't be `pvt` or `mod`, or sit in such a block.

## Methods in enums

Enums take methods, static functions, static fields and properties the same way records do, and in a method `self` is the enum value. Enums can't declare fields or constructors. [Enums](enums.md#methods) shows them.
