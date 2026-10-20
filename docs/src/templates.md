# String templates

A template is a string with holes, handed to a function that writes it out. The language doesn't format anything itself. It gives the receiving function the literal pieces of the string, a format spec for each hole, and a borrow of each hole's value, and that function decides how to turn the values into text and where to put it.

## A first template

A parameter of type `fstr[K]` takes a template. `K` is a [trait](traits.md) that every hole's value must implement, and it's how the receiving code works with values it knows nothing else about:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Display: trait
{
	print: fun(imm self)
}

str: impl Display
{
	print: fun(self) => printf("%.*s", i32(self.byteLength), self.data)
}

i32: impl Display
{
	print: fun(self) => printf("%d", self)
}

say: fun(text: fstr[Display])
{
	for i in 0..text.holes
	{
		text.piece(i).print()
		text.value(i).print()
	}

	text.piece(text.holes).print()
}

main: fun
{
	val name: str = "Ada"
	val hp = 30
	say("{name} has {hp} hp, {hp * 2} at full health\n")
}
```

```output
Ada has 30 hp, 60 at full health
```

The string passed to `say` has three holes, each an expression in braces. `say` walks them in order: it prints the literal piece before each hole, then the hole's value, and finally the piece after the last hole. The pieces are `str` values, so `say` prints them through `Display` as well.

`str` and `i32` take part because the program implements `Display` for them. A template only accepts holes whose types implement its trait, built-in types included.

## Reading a template

An `fstr[K]` has four members:

| Member | Type | What it gives |
| --- | --- | --- |
| `holes` | `usize` | the number of holes |
| `piece(i)` | `str` | the literal text before hole `i`; `piece(holes)` is the text after the last hole |
| `spec(i)` | `str` | the format spec of hole `i`, empty when it has none |
| `value(i)` | `imm[dyn[K]]` | a read-only borrow of hole `i`'s value |

There is always one more piece than there are holes, and a piece can be empty. This function prints a template's parts instead of its text:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
~ Display: trait
~ {
~ 	print: fun(imm self)
~ }
~
~ i32: impl Display
~ {
~ 	print: fun(self) => printf("%d", self)
~ }
~
dump: fun(text: fstr[Display])
{
	printf("%zu holes:", text.holes)
	for i in 0..=text.holes
	{
		val piece = text.piece(i)
		printf(" '%.*s'", i32(piece.byteLength), piece.data)
		if i < text.holes
		{
			val spec = text.spec(i)
			printf(" [%.*s]", i32(spec.byteLength), spec.data)
		}
	}

	printf("\n")
}

main: fun
{
	dump("a{1}b{2:x}c{3:>8}d")
	dump("{1}{2}")
	dump("no holes")
}
```

```output
3 holes: 'a' [] 'b' [x] 'c' [>8] 'd'
2 holes: '' [] '' [] ''
0 holes: 'no holes'
```

The indexes are `usize` values, and an index past the end panics like any other bounds check:

```cella
~ mod example
~
~ Display: trait
~ {
~ 	print: fun(imm self)
~ }
~
first: fun(text: fstr[Display]) -> usize => text.spec(0).byteLength

main: fun
{
	first("no holes")
}
```

```output
Panic at main.ce:8:45: index out of bounds
```

The members can't be assigned to:

```cella error
~ mod example
~
~ Display: trait
~ {
~ 	print: fun(imm self)
~ }
~
clear: fun(text: fstr[Display])
{
	text.holes = 0
}

main: fun
{
}
```

```errors
Cannot reassign read-only properties
```

## Holes

A hole holds any expression: a name, arithmetic, a call, a comparison, a string literal or a `match`. Holes are evaluated left to right when the template is made, before the receiving function runs:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
~ Display: trait
~ {
~ 	print: fun(imm self)
~ }
~
~ str: impl Display
~ {
~ 	print: fun(self) => printf("%.*s", i32(self.byteLength), self.data)
~ }
~
~ i32: impl Display
~ {
~ 	print: fun(self) => printf("%d", self)
~ }
~
~ say: fun(text: fstr[Display])
~ {
~ 	for i in 0..text.holes
~ 	{
~ 		text.piece(i).print()
~ 		text.value(i).print()
~ 	}
~
~ 	text.piece(text.holes).print()
~ }
~
next: fun(mut counter: i32) -> i32
{
	counter += 1
	ret counter
}

main: fun
{
	var counter = 0
	say("{next(mut counter)} {next(mut counter)} {counter}\n")
	say("{"quoted"} {match counter { 2 => 20, else => 0 }}\n")
}
```

```output
1 2 2
quoted 20
```

Every hole's type must implement the template's trait:

```cella error
~ mod example
~
~ Display: trait
~ {
~ 	print: fun(imm self)
~ }
~
~ i32: impl Display
~ {
~ 	print: fun(self)
~ 	{
~ 	}
~ }
~
Point: rec
{
	x: i32
}

say: fun(text: fstr[Display])
{
}

main: fun
{
	val p = Point(1)
	say("{p} {p.x}")
}
```

```errors
'Point' doesn't implement 'Display'
```

A hole can't be empty, and its braces must close in the same string. A literal `{` is written `\{`, and a `}` on its own is ordinary text, as in any string (see [Braces in strings](text.md#braces-in-strings)).

## Format specs

A hole may end in a format spec: a `:` followed by any text up to the closing brace, as in `{price:.2}`. The spec is passed along as text through `spec(i)`, and what it means is up to the receiving code. Spaces are kept, and escape sequences work as in the rest of the string, so `\}` puts a brace in a spec. A hole without a `:`, or with nothing after it, has an empty spec.

This `Display` takes the spec as a parameter, and `i32` prints in hex when the spec is `x`:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Display: trait
{
	print: fun(imm self, spec: str)
}

str: impl Display
{
	print: fun(self, spec: str) => printf("%.*s", i32(self.byteLength), self.data)
}

i32: impl Display
{
	print: fun(self, spec: str)
	{
		if spec.byteLength == 1 && spec[0] == u8('x')
			printf("%x", self)
		else
			printf("%d", self)
	}
}

say: fun(text: fstr[Display])
{
	for i in 0..text.holes
	{
		text.piece(i).print("")
		text.value(i).print(text.spec(i))
	}

	text.piece(text.holes).print("")
}

main: fun
{
	val color = 16753920
	say("{color} is {color:x} in hex\n")
}
```

```output
16753920 is ffa500 in hex
```

## Strings without holes

A template parameter also takes a string literal without holes or a `str` value. Either becomes a template with no holes and one piece:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
~ Display: trait
~ {
~ 	print: fun(imm self)
~ }
~
~ str: impl Display
~ {
~ 	print: fun(self) => printf("%.*s", i32(self.byteLength), self.data)
~ }
~
~ say: fun(text: fstr[Display])
~ {
~ 	for i in 0..text.holes
~ 	{
~ 		text.piece(i).print()
~ 		text.value(i).print()
~ 	}
~
~ 	text.piece(text.holes).print()
~ }
~
title: fun -> str => "Cella\n"

main: fun
{
	val name: str = "Ada\n"
	say("plain\n")
	say(name)
	say(title())
}
```

```output
plain
Ada
Cella
```

Nothing else converts to a template, not even a `cstr`:

```cella error
~ mod example
~
~ Display: trait
~ {
~ 	print: fun(imm self)
~ }
~
say: fun(text: fstr[Display])
{
}

main: fun
{
	val c: cstr = "x"
	say(c)
	say(5)
}
```

```errors
Cannot convert type 'cstr' to 'fstr[Display]'
Cannot convert type 'integer literal' to 'fstr[Display]'
```

Outside a template, a string with holes is a constant: every hole must be a constant string, and the compiler joins the pieces into one string (see [Interpolated strings](text.md#interpolated-strings)).

When a function is overloaded for `str` and for a template, a string without holes goes to the `str` overload, and a string with holes goes to the template, even when its holes are constants:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
~ Display: trait
~ {
~ 	print: fun(imm self)
~ }
~
~ str: impl Display
~ {
~ 	print: fun(self) => printf("%.*s", i32(self.byteLength), self.data)
~ }
~
~ i32: impl Display
~ {
~ 	print: fun(self) => printf("%d", self)
~ }
~
show: fun(text: str) => printf("str\n")
show: fun(text: fstr[Display]) => printf("template, holes: %zu\n", text.holes)

unit: const str = "items"

main: fun
{
	val count = 3
	show("plain")
	show("{unit}")
	show("{count} {unit}")
}
```

```output
str
template, holes: 1
template, holes: 2
```

## Templates and traits

`value(i)` gives each hole as a borrowed [trait object](trait-objects.md), so the receiving code can call the trait's members on it, and the members of the traits it requires. A record takes part by implementing the trait, and its implementation can use a template itself:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
~ Display: trait
~ {
~ 	print: fun(imm self)
~ }
~
~ str: impl Display
~ {
~ 	print: fun(self) => printf("%.*s", i32(self.byteLength), self.data)
~ }
~
~ i32: impl Display
~ {
~ 	print: fun(self) => printf("%d", self)
~ }
~
~ say: fun(text: fstr[Display])
~ {
~ 	for i in 0..text.holes
~ 	{
~ 		text.piece(i).print()
~ 		text.value(i).print()
~ 	}
~
~ 	text.piece(text.holes).print()
~ }
~
Point: rec impl Display
{
	x: i32
	y: i32

	print: fun(self) => say("({self.x}, {self.y})")
}

log[T: Display]: fun(label: str, imm value: T) => say("{label}: {value}\n")

relay: fun(imm value: dyn[Display]) => say("relayed {value}\n")

main: fun
{
	val spot = Point(3, 4)
	say("at {spot}\n")
	log("point", imm spot)
	log("number", 5)
	relay(imm spot)
}
```

```output
at (3, 4)
point: (3, 4)
number: 5
relayed (3, 4)
```

A hole can hold a generic value whose bound is the template's trait, as in `log`, or a `dyn` value of that trait, as in `relay`.

The argument of `fstr` must be a trait, exactly one:

```cella error
~ mod example
~
~ Display: trait
~ {
~ 	print: fun(imm self)
~ }
~
a: fun(text: fstr[i32])
{
}

b: fun(text: fstr)
{
}

c: fun(text: fstr[Display, Display])
{
}

main: fun
{
}
```

```errors
'i32' is not a trait
'fstr' takes one generic argument
'fstr' takes one generic argument
```

A generic function can leave the trait open with a `K: trait` parameter, written out at the call:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
~ Display: trait
~ {
~ 	print: fun(imm self)
~ }
~
~ i32: impl Display
~ {
~ 	print: fun(self) => printf("%d", self)
~ }
~
count[K: trait]: fun(text: fstr[K]) -> usize => text.holes

main: fun
{
	val n = 9
	printf("%zu\n", count[Display]("{n} {n} {n}"))
}
```

```output
3
```

## Templates as values

`fstr[K]` is an ordinary type. A template can be made explicitly with `fstr[Display](...)`, copied, passed on and returned:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
~ Display: trait
~ {
~ 	print: fun(imm self)
~ }
~
~ str: impl Display
~ {
~ 	print: fun(self) => printf("%.*s", i32(self.byteLength), self.data)
~ }
~
~ i32: impl Display
~ {
~ 	print: fun(self) => printf("%d", self)
~ }
~
~ say: fun(text: fstr[Display])
~ {
~ 	for i in 0..text.holes
~ 	{
~ 		text.piece(i).print()
~ 		text.value(i).print()
~ 	}
~
~ 	text.piece(text.holes).print()
~ }
~
Message: ref rec
{
	text: fstr[Display]
}

pass: fun(text: fstr[Display]) -> fstr[Display] => text

main: fun
{
	val count = 3
	val template = fstr[Display]("{count} items\n")
	val copy = template
	say(pass(copy))

	val message = Message("message {count}\n")
	say(message.text)
}
```

```output
3 items
message 3
```

A template borrows its hole values, so it follows the rules for [borrows](borrows.md). It can't outlive the values in its holes, a record that holds one must be a `ref rec`, and a module variable can't hold one:

```cella error
~ mod example
~
~ Display: trait
~ {
~ 	print: fun(imm self)
~ }
~
~ i32: impl Display
~ {
~ 	print: fun(self)
~ 	{
~ 	}
~ }
~
Holder: rec
{
	text: fstr[Display]
}

saved: var fstr[Display] = "x"

make: fun -> fstr[Display]
{
	val local = 5
	ret "{local}"
}

compute: fun -> i32 => 4

show: fun(text: fstr[Display])
{
}

main: fun
{
	val later: fstr[Display] = "{compute()}"
	show(later)
}
```

```errors
Cannot store borrows in records that aren't 'ref'
Cannot store borrows in module variables
Cannot return borrows of local variables
Cannot borrow unstored values
```

The last error is about `compute()`: its result is a temporary that ends with its statement, so a template that keeps it can't be used afterwards.

Since a template holds borrows of Cella values, it can't appear in an `ext` signature:

```cella error
~ mod example
~
~ Display: trait
~ {
~ 	print: fun(imm self)
~ }
~
ext
{
	log: fun(text: fstr[Display])
}

main: fun
{
}
```

```errors
Cannot use 'fstr[Display]' in 'ext' signatures
```
