# Conversions

A conversion turns a value of one type into a value of another. Some happen on their own, such as an `i32` passed where an `i64` is expected. Others have to be written out as `T(x)`. The built-in types come with their conversions, and records and enums declare their own as members: `as` for conversions that happen on their own and `new` for ones that have to be written.

## Writing a conversion

`T(x)` converts `x` to the type `T`. It's written like a call to a constructor of `T`, and a constructor that takes one value is a conversion into `T`.

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Color: enum
{
	red
	green
	blue
}

main: fun
{
	val count = 7
	val wide: i64 = 300
	val flag = true
	val letter = 'a'
	printf("%.2f %d %d\n", f64(count) / 2.0, i32(u8(wide & 0xFF)), i32(flag))
	printf("%u %c %d\n", u32(letter), i32(char(98)), i32(Color.blue))
	val color = Color(1)
	printf("%d\n", i32(color == green))
}
```

```output
3.50 44 1
97 b 2
1
```

The built-in conversions cover:

- numbers to other number types, in every direction, as described in [Numbers and arithmetic](numbers.md);
- `bool` to any integer type, giving 0 or 1;
- `char` to and from integer types;
- enums without payloads to and from integer types (see [Enums](enums.md));
- pointers to other pointer types, `cstr` to and from `ptr` (see [Pointers and raw memory](pointers.md));
- values to trait objects, as in `dyn[Shape](circle)` (see [Trait objects](trait-objects.md)).

A conversion that can lose information, like `u8(x)` for an `i32` `x`, is checked. A constant that doesn't fit is a compile error, and other values are checked when the program runs; [Numbers and arithmetic](numbers.md) and [Checks and panics](panics.md) cover both.

## Implicit conversions

A conversion happens on its own wherever a value of one type is used as another: a declaration with a type, an assignment, an argument, a returned value or an operand.

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
average: fun(total: f64, count: f64) -> f64 => total / count

main: fun
{
	val total: i32 = 17
	val count: u8 = 4
	val wide: i64 = total
	printf("%lld %.2f\n", wide, average(total, count))
}
```

```output
17 4.25
```

Only conversions that can't lose anything happen on their own. Among the built-in types, those are:

- a number to a numeric type that holds every value of its type exactly, like `i32` to `i64`, `u8` to `i16`, `i32` to `f64` or `f32` to `f64` ([Numbers and arithmetic](numbers.md#implicit-numeric-conversions) lists them all);
- `cstr` and any `ptr[T]` to `ptr`, and `null` to any pointer.

Everything else has to be written as `T(x)`:

```cella error
~ mod example
~
main: fun
{
	val total: i32 = 17
	val big: i64 = 1
	val small: u8 = total
	val ratio: f64 = big
	val number: i32 = true
	val code: u32 = 'a'
}
```

```errors
Cannot convert type 'i32' to 'u8'
Cannot convert type 'i64' to 'f64'
Cannot convert type 'bool' to 'i32'
Cannot convert type 'char' to 'u32'
```

`i64` to `f64` isn't implicit because an `f64` can't hold every `i64` exactly.

### Types decide, not values

Whether a value converts on its own depends only on its type, never on the value it happens to hold. A constant is no exception: `limit` below is an `i32`, and an `i32` doesn't convert to `usize` on its own, even though 3 would fit.

```cella error
~ mod example
~
limit: const i32 = 3
half: const f64 = 0.5

reserve: fun(count: usize)
{
}

scale: fun(factor: f32)
{
}

main: fun
{
	reserve(limit)
	scale(half)
}
```

```errors
Cannot convert type 'i32' to 'usize'
Cannot convert type 'f64' to 'f32'
```

Literals are the one case where the value matters. A literal has no type until it's used, so it takes the type that's expected, as long as its value fits:

```cella error
~ mod example
~
reserve: fun(count: u8)
{
}

main: fun
{
	reserve(200)
	reserve(300)
	reserve(-1)
	val whole: i32 = 2.0
}
```

```errors
'300' doesn't fit in 'u8'
'-1' doesn't fit in 'u8'
Cannot convert type 'float literal' to 'i32'
```

## Declaring conversions

Records and enums declare conversions as members. There are four forms, one for each direction and kind:

| Form | Direction | Happens |
| --- | --- | --- |
| `as: op(self) -> T` | out of the type, to `T` | on its own, or as `T(x)` |
| `as: op(value: T) -> Type` | into the type, from `T` | on its own, or as `Type(x)` |
| `new: op(self) -> T` | out of the type, to `T` | only as `T(x)` |
| `new: op(value: T)` | into the type, from `T` | only as `Type(x)` |

`Type` stands for the declaring type. The last form is an ordinary constructor (see [Records](records.md)).

### `as` out of a type

`as` with a receiver converts the type to another one wherever that other type is expected:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Id: rec
{
	value: i32

	as: op(self) -> i32 => self.value
}

Ready: rec
{
	done: bool

	as: op(self) -> bool => self.done
}

show: fun(value: i32) => printf("%d\n", value)

main: fun
{
	val id = Id(4)
	show(id)
	val plain: i32 = id
	printf("%d %d\n", plain, id + 1)
	if Ready(true)
		printf("ready\n")
}
```

```output
4
4 5
ready
```

`id + 1` converts `id` to `i32` because `+` has no other way to take an `Id`.

### `as` into a type

A static `as`, with one parameter and no receiver, converts the parameter's type into the declaring type. It lets a function take several kinds of values through one parameter:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Arg: enum
{
	int(value: i64)
	flag(value: bool)

	as: op(value: i64) -> Arg => int(value)
	as: op(value: bool) -> Arg => flag(value)
}

log: fun(arg: Arg)
{
	match arg
	{
		int(val value) => printf("int %lld\n", value)
		flag(val value) => printf("flag %d\n", i32(value))
	}
}

main: fun
{
	log(5)
	log(true)
	val big: i64 = 7
	log(big)
	var arg: Arg = 8
	arg = false
	log(arg)
}
```

```output
int 5
flag 1
int 7
flag 0
```

### `new` out of a type

A conversion that shouldn't happen on its own, because it loses information or does real work, is `new` with a receiver. It only runs when written as `T(x)`:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Fixed: rec
{
	raw: i32

	new: op(self) -> i32 => self.raw >> 16
	new: op(self) -> f64 => f64(self.raw) / 65536.0
}

main: fun
{
	val value = Fixed(0x28000)
	printf("%d %.2f\n", i32(value), f64(value))
}
```

```output
2 2.50
```

`Fixed(0x28000)` is the field-by-field constructor, which sets `raw`.

Using it where an `i32` is expected without writing `i32(...)` is an error:

```cella error
~ mod example
~
Fixed: rec
{
	raw: i32

	new: op(self) -> i32 => self.raw >> 16
}

show: fun(value: i32)
{
}

main: fun
{
	val fixed = Fixed(1 << 16)
	val whole: i32 = fixed
	show(fixed)
}
```

```errors
Cannot convert type 'Fixed' to 'i32'
Cannot convert type 'Fixed' to 'i32'
```

## Receivers

The receiver of an outward conversion says how the value is taken, as for any method:

- `self` takes the value, a copy or the value itself, and returns a new one.
- `imm self` borrows the value. It can return a borrow of part of it, `imm[T]`, or a type that borrows, such as `str`.
- `mut self` borrows the value writably and returns `mut[T]`.

A type can give out a borrow of something it holds this way. `Slot` below converts to a `Sprite` by lending its own: a read-only borrow where a `Sprite` is read, a writable one where it's passed as `mut`.

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Sprite: rec
{
	hp: i32
}

Slot: rec
{
	sprite: Sprite

	as: op(imm self) -> imm[Sprite] => imm self.sprite
	as: op(mut self) -> mut[Sprite] => mut self.sprite
}

draw: fun(sprite: Sprite) => printf("draw %d\n", sprite.hp)

heal: fun(mut sprite: Sprite) => sprite.hp += 10

main: fun
{
	var hero = Slot(Sprite(5))
	draw(hero)
	heal(mut hero)
	draw(hero)
}
```

```output
draw 5
draw 15
```

A string type is a common case. It owns its bytes and lends them as a `str`, so it can go wherever a `str` is expected:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ 	malloc: fun(size: usize) -> ptr[u8]
~ 	free: fun(memory: ptr[u8])
~ 	memcpy: fun(target: ptr[u8], source: ptr[u8], size: usize) -> ptr[u8]
~ }
~
String: own rec
{
	data: pvt ptr[u8]
	length: pvt usize

	new: op(text: str)
	{
		self.data = malloc(text.byteLength)
		self.length = text.byteLength
		memcpy(self.data, text.data, text.byteLength)
	}

	as: op(imm self) -> str => str(self.data, self.length)

	drop: op
	{
		free(self.data)
	}
}

show: fun(text: str) => printf("[%.*s]\n", i32(text.byteLength), text.data)

main: fun
{
	val name = String("Ada")
	show(name)
	val view: str = name
	show(view)
	show(String("temporary"))
}
```

```output
[Ada]
[Ada]
[temporary]
```

The `str` borrows from `name`, so it follows the rules for borrows (see [Borrows](borrows.md)): it can't outlive `name`, and it can't be kept from a temporary that's dropped at the end of its statement:

```cella error
~ mod example
~
~ ext
~ {
~ 	malloc: fun(size: usize) -> ptr[u8]
~ 	free: fun(memory: ptr[u8])
~ }
~
~ String: own rec
~ {
~ 	data: pvt ptr[u8]
~ 	length: pvt usize
~
~ 	new: op(text: str)
~ 	{
~ 		self.data = malloc(text.byteLength)
~ 		self.length = text.byteLength
~ 	}
~
~ 	as: op(imm self) -> str => str(self.data, self.length)
~
~ 	drop: op
~ 	{
~ 		free(self.data)
~ 	}
~ }
~
local: fun -> str
{
	val name = String("local")
	ret name
}

main: fun
{
	val view: str = String("temporary")
	val length = view.byteLength
}
```

```errors
Cannot return borrows of local variables
Cannot borrow unstored values
```

A `self` conversion on a type that can't be copied consumes the value, so converting a named variable moves it, as any move does (see [Ownership and destructors](ownership.md)):

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
	size: i32

	drop: op
	{
		printf("drop buffer %d\n", self.size)
	}
}

Text: own rec
{
	size: i32

	as: op(self) -> Buffer => Buffer(self.size)

	drop: op
	{
		printf("drop text %d\n", self.size)
	}
}

send: fun(buffer: Buffer) => printf("send %d\n", buffer.size)

main: fun
{
	val text = Text(1)
	send(text)
	send(Text(2))
}
```

```output
drop text 1
send 1
drop buffer 1
drop text 2
send 2
drop buffer 2
```

The receiver and the result have to agree:

```cella error
~ mod example
~
Text: rec
{
	value: i32

	as: op(mut self) -> i32 => 1
	as: op(self) -> mut[i32] => mut self.value
}

main: fun
{
}
```

```errors
Cannot return 'i32' from 'as' with 'mut self'
Cannot return 'mut[i32]' from 'as' with 'self'
```

## How conversions are used

### Exact matches come first

When a call has overloads, one that takes the argument's own type wins over one that needs a conversion. A generic type parameter is inferred from the argument's own type, never from what it converts to:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Id: rec
{
	value: i32

	as: op(self) -> i32 => self.value
}

pick: fun(value: i32) => printf("i32 %d\n", value)

pick: fun(value: Id) => printf("Id %d\n", value.value)

only: fun(value: i32) => printf("only %d\n", value)

same[T: copy]: fun(value: T) -> T => value

main: fun
{
	val id = Id(4)
	pick(id)
	only(id)
	printf("same %d\n", same(id).value)
}
```

```output
Id 4
only 4
same 4
```

### `.` doesn't look through `as`

`.` only reaches a type's own members, never the members of what it converts to. A conversion is also not a member that can be called by name:

```cella error
~ mod example
~
Sprite: rec
{
	hp: i32
}

Slot: rec
{
	sprite: Sprite

	as: op(imm self) -> imm[Sprite] => imm self.sprite
}

Id: rec
{
	value: i32

	as: op(self) -> i32 => self.value
}

main: fun
{
	val slot = Slot(Sprite(5))
	val hp = slot.hp
	val number = Id(1).as()
}
```

```errors
Type 'Slot' has no member 'hp'
Type 'Id' has no member 'as'
```

Write `Sprite(slot).hp` or `i32(id)` instead.

## A type's own constructor comes first

A type can declare both a constructor and an `as` from the same type. `T(x)` then calls the constructor, and the `as` runs only where the conversion happens on its own:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Meters: rec
{
	value: f64

	new: op(value: f64)
	{
		printf("constructor\n")
		self.value = value
	}

	as: op(value: f64) -> Meters
	{
		printf("as\n")
		ret Meters(value)
	}
}

show: fun(length: Meters) => printf("%.1f\n", length.value)

main: fun
{
	val a = Meters(2.0)
	show(3.0)
}
```

```output
constructor
as
constructor
3.0
```

`Meters(value)` inside the `as` calls the constructor too, so the `as` doesn't call itself. The same holds for a record's field-by-field constructor, which is why a short `as` can build its result directly:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Meters: rec
{
	value: f64

	as: op(value: f64) -> Meters => Meters(value)
}

main: fun
{
	val length: Meters = 4.5
	printf("%.1f\n", length.value)
}
```

```output
4.5
```

## Conversions don't chain

A value converts at most once. When no single conversion leads from its type to the one expected, there is no conversion, even if two in a row would get there. Below, an `i32` would have to widen to `i64` and then go through `Arg`'s `as`, and an `Id` would have to become an `i32` and then widen to `i64`:

```cella error
~ mod example
~
Arg: enum
{
	int(value: i64)

	as: op(value: i64) -> Arg => int(value)
}

Id: rec
{
	value: i32

	as: op(self) -> i32 => self.value
}

log: fun(arg: Arg)
{
}

main: fun
{
	val count: i32 = 5
	log(count)
	val wide: i64 = Id(4)
}
```

```errors
Cannot convert type 'i32' to 'Arg'
Cannot convert type 'Id' to 'i64'
```

`log(5)` works, since the literal `5` becomes an `i64` directly, and `log(i64(count))` converts in two written steps.

## Ambiguous conversions

Both types can declare a conversion between them: the source with `as` out, and the target with `as` in or a constructor. Neither wins, so every use is an error:

```cella error
~ mod example
~
Source: rec
{
	id: i32

	as: op(self) -> Name => Name(self.id)
	new: op(self) -> Label => Label(self.id)
}

Name: rec
{
	id: i32

	as: op(value: Source) -> Name => Name(value.id)
}

Label: rec
{
	id: i32

	new: op(id: i32)
	{
		self.id = id
	}

	new: op(value: Source)
	{
		self.id = value.id
	}
}

main: fun
{
	val source = Source(1)
	val name: Name = source
	val label = Label(source)
}
```

```errors
Conversion from 'Source' to 'Name' is ambiguous
Conversion to 'Label' is ambiguous
```

A value with several `as` conversions can also leave an operator with more than one way to go:

```cella error
~ mod example
~
Wide: rec
{
	value: i32

	as: op(self) -> i32 => self.value
	as: op(self) -> i64 => i64(self.value)
}

main: fun
{
	val negated = -Wide(1)
}
```

```errors
Operation '-' on 'Wide' is ambiguous
```

## Declaration rules

An outward conversion takes only its receiver, and an inward one exactly one parameter. A type can't convert to itself, can't declare two conversions for the same pair of types, and can't declare both an `as` and a `new` to the same target:

```cella error
~ mod example
~
Text: rec
{
	value: i32

	as: op(self, extra: i32) -> i32 => extra
	as: op(self) -> Text => self
	as: op(a: i32, b: i32) -> Text => Text(a)
	as: op(self) -> u16 => 1
	as: op(self) -> u16 => 2
	as: op(self) -> u32 => 1
	new: op(self) -> u32 => 1
}

main: fun
{
}
```

```errors
Cannot take parameters in 'as' operators with 'self'
Cannot convert 'Text' to itself
'as' operators need 'self' or one parameter
Conversion to 'u16' with 'self' is declared more than once in 'Text'
Conversion to 'u16' with 'self' is declared more than once in 'Text'
Cannot declare both 'as' and 'new' conversions to 'u32'
Cannot declare both 'as' and 'new' conversions to 'u32'
```

An inward `as` must return the declaring type, so it can't be used to add a conversion between two other types:

```cella error
~ mod example
~
Text: rec
{
	value: i32

	as: op(value: i64) -> i32 => 1
}

main: fun
{
}
```

```errors
Cannot return 'i32' from 'as' operators without 'self'
```

## Built-in conversions can't be redeclared

Where the language already converts between two types, a type can't declare its own conversion between them. An enum without payloads converts to and from every integer type, so it can't declare one:

```cella error
~ mod example
~
Color: enum
{
	red
	green

	as: op(self) -> i32 => 100
	new: op(self) -> u16 => 99
	as: op(value: i32) -> Color => green
}

main: fun
{
}
```

```errors
Conversion to 'i32' is built in
Conversion to 'u16' is built in
Conversion from 'i32' is built in
```

A case's number is set with a case value instead (see [Enums](enums.md)).

## Conversions in generic code

A constraint like `[T: new(Source)]` asks for a way to write `T(source)`. Constructors, a record's field-by-field constructor and `new` conversions meet it; `as` conversions don't:

```cella error
~ mod example
~
Source: rec
{
	id: i32

	as: op(self) -> ViaAs => ViaAs(self.id)
	new: op(self) -> ViaNew => ViaNew(self.id)
}

ViaAs: rec
{
	id: i32
}

ViaNew: rec
{
	id: i32
}

convert[T: new(Source)]: fun(value: Source) -> T => T(value)

main: fun
{
	val source = Source(1)
	val viaNew: ViaNew = convert(source)
	val viaAs: ViaAs = convert(source)
}
```

```errors
'convert' requires 'T: new(Source)'
```

Traits can require `as` and `new` conversions too, and each requirement is met only by its own kind. Constraints are covered in [Generics](generics.md) and requirements in [Traits](traits.md).
