# Unions

A union stores several members in the same memory. Writing one member and reading another reads the same bytes as a different type, which is how C programs look at the bits of a float or describe data that can take one of several layouts. Unions work like C's unions and have the same layout, so they can be shared with C code.

## Declaring a union

A union is declared like a record, with `union` in place of `rec`. `T()` creates a union with every byte zero, as does declaring a variable without a value:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Bits: union
{
	float: f32
	raw: u32
}

main: fun
{
	var bits = Bits()
	printf("%x\n", bits.raw)

	bits.float = 1.0
	printf("%x\n", bits.raw)

	bits.raw = 0x40490fdb
	printf("%.5f\n", f64(bits.float))
}
```

```output
0
3f800000
3.14159
```

Writing `bits.float` stores the four bytes of the float, and reading `bits.raw` gives those same bytes as an integer. Nothing records which member was written last; every member can be read at any time.

## Creating a union from a member

`T(value)` with one argument creates a union with the member whose type is exactly the type of `value` set to it. Bytes the member doesn't cover are zero:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Bits: union
{
	float: f32
	raw: u32
}

bitsOf: fun(value: f32) -> u32 => Bits(value).raw

main: fun
{
	printf("%x %x\n", bitsOf(1.0), bitsOf(-2.0))
	printf("%.1f\n", f64(Bits(0x40490fdbu32).float))
}
```

```output
3f800000 c0000000
3.1
```

The member is picked by type alone, so the argument's type must be known. An untyped literal like `1` has none and needs a suffix, as in `1u32`. A union with two members of the argument's type can't pick one either:

```cella error
~ mod example
~
Bits: union
{
	float: f32
	raw: u32
}

Twin: union
{
	first: u32
	second: u32
}

main: fun
{
	val bits = Bits(1)
	val twin = Twin(1u32)
}
```

```errors
No constructor for 'Bits' accepts these arguments
Conversion to 'Twin' is ambiguous
```

The first error's note lists what `Bits` accepts: "'Bits' takes no arguments, or one value of a field's type: f32, u32".

## Members share one address

Every member of a union starts at offset 0, so they all have the same address:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Bits: union
{
	float: f32
	raw: u32
	bytes: array[u8, 4]
}

main: fun
{
	var bits = Bits()
	val a = isize(@bits.float)
	val b = isize(@bits.raw)
	val c = isize(@bits.bytes)
	printf("%d %d\n", i32(a == b), i32(b == c))

	bits.raw = 0x11223344
	printf("%x %x\n", bits.bytes[0], bits.bytes[3])
}
```

```output
1 1
44 11
```

A member smaller than the union covers only its first bytes. On the 64-bit Windows and Linux targets, the lowest byte of an integer comes first in memory, which is why `bytes[0]` is `0x44`.

## Reading and writing members

Members are read and written with `.`, like fields, and so are the parts of a member that is a record or an array. A union can be a field of a record, and a record can be a member of a union:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
MouseInput: rec
{
	x: i32
	y: i32
	buttons: u32
}

KeyInput: rec
{
	key: u16
	scan: u16
	flags: u32
	time: u64
}

InputData: union
{
	mouse: MouseInput
	keyboard: KeyInput
}

Input: rec
{
	kind: u32
	data: InputData
}

main: fun
{
	var input = Input(1, InputData())
	input.data.keyboard.key = 65
	input.data.keyboard.time = 99
	printf("%d %d\n", input.data.mouse.x, input.data.keyboard.key)
}
```

```output
65 65
```

`mouse.x` and `keyboard.key` start at the same offset, so `mouse.x` reads the key code in its low bytes.

Reading a member whose type allows only some bit patterns makes the value valid first. A `bool` read from a union is `true` when its byte is not zero:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Flags: rec
{
	on: bool
	off: bool
}

Packed: union
{
	flags: Flags
	raw: u16
}

main: fun
{
	var packed = Packed()
	packed.raw = 0x0200
	printf("%d %d\n", i32(packed.flags.on), i32(packed.flags.off))
}
```

```output
0 1
```

A `char` read from a union is checked: bytes that aren't a valid character panic.

```cella
~ mod example
~
Letter: union
{
	letter: char
	raw: u32
}

main: fun
{
	var letter = Letter()
	letter.raw = 0xFFFFFFFF
	val _ = letter.letter
}
```

```output
Panic at main.ce:13:10: invalid char
```

## Sizes

A union is as large as its largest member, rounded up to a multiple of its alignment, and its alignment is the largest alignment of its members:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Mixed: union
{
	small: u8
	wide: i64
	triple: array[u16, 3]
}

Color: union
{
	floats: array[f32, 4]
	ints: array[i32, 4]
}

main: fun
{
	printf("%d %d\n", i32(sizeOf(Mixed)), i32(alignOf(Mixed)))
	printf("%d %d\n", i32(sizeOf(Color)), i32(alignOf(Color)))
}
```

```output
8 8
16 4
```

## Constructors, methods and properties

A union can declare constructors, methods and properties, as a record does; [Records](records.md) and [Methods and properties](methods.md) cover them. A constructor sets the members it wants through `self`. Declaring a constructor removes `T()` and `T(value)`, the same as for records. Properties can give names to the bits of an integer member:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
ClearColor: union
{
	floats: array[f32, 4]
	uints: array[u32, 4]

	new: op(red: f32, green: f32, blue: f32)
	{
		self.floats = [red, green, blue, 1.0]
	}

	alpha: fun(self) -> f32 => self.floats[3]
}

Flags: union
{
	raw: u32

	visible: prop bool
	{
		get(self) => (self.raw & 1) != 0
		set(mut self, value) => self.raw = (self.raw & ~1) | u32(value)
	}

	layer: prop u32
	{
		get(self) => (self.raw >> 2) & 15
		set(mut self, value) => self.raw = (self.raw & ~(15 << 2)) | ((value & 15) << 2)
	}
}

main: fun
{
	val color = ClearColor(0.5, 0.25, 0.125)
	printf("%.1f %x\n", f64(color.alpha()), color.uints[3])

	var flags = Flags()
	flags.visible = true
	flags.layer = 5
	printf("%d %d %d\n", i32(flags.visible), flags.layer, flags.raw)
}
```

```output
1.0 3f800000
1 5 21
```

A union can't declare a destructor or `req` members and can't be a `ref union`:

```cella error
~ mod example
~
Holder: union
{
	count: req i32
	raw: u32

	drop: op
	{
	}
}

Shared: ref union
{
	value: i32
}

main: fun
{
}
```

```errors
Cannot declare required fields in unions
Cannot declare destructors in unions
Cannot declare 'ref' unions
```

## What a union can hold

A union holds only plain data: integers, floats, `bool`, `char`, pointers, `cstr`, `ext enum` values, and arrays and records made of them. A member can't have a destructor, hold a borrow, or be a type with no all-zero value such as a function value. Plain enums can't be members either, and neither can records with fields that the union's module can't see or write, such as `pvt` and `pvt set` fields:

```cella error
~ mod example
~
Name: own rec
{
	id: i32

	drop: op
	{
	}
}

Color: enum
{
	red
	green
}

Locked: rec
{
	count: pvt set i32
}

Holds: union
{
	name: Name
	callback: fun[i32]
	color: Color
	locked: Locked
	raw: u64
}

main: fun
{
}
```

```errors
Cannot store values with destructors in unions
Cannot store values without defaults in unions
Cannot store 'Color' values in unions
Cannot store 'Locked' values in unions
```

All members of a union share one visibility. A member can't be less visible than the others, and a member can't restrict who may write it:

```cella error
~ mod example
~
Hidden: union
{
	a: pvt i32
	b: i32
}

Guarded: union
{
	a: pvt set i32
	b: i32
}

Private: union
{
	a: pvt i32
	b: pvt u32
}

main: fun
{
}
```

```errors
Cannot make union members less visible than other members
Cannot restrict writes to union members
```

## Unions in constants

Reading a member of a union built from a constant is a constant too, so constants can be written as raw bits. The bits are kept exactly, including those of infinities and NaNs:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
F32Bits: union
{
	raw: u32
	value: f32
}

Word: union
{
	value: u32
	bytes: array[u8, 4]
}

largest: const f32 = F32Bits(0x7F7FFFFFu32).value
infinity: const f32 = F32Bits(0x7F800000u32).value
oneBits: const u32 = F32Bits(1.0f32).raw
lowByte: const u8 = Word(0x11223344u32).bytes[0]

main: fun
{
	printf("%g %g\n", f64(largest), f64(infinity))
	printf("%x %x\n", oneBits, lowByte)
}
```

```output
3.40282e+38 inf
3f800000 44
```

A constant can read a member whose type is an integer, a float, `bool`, `char` or an array of them. A `bool` read this way must be 0 or 1, and a `char` must be a valid character; otherwise the value isn't a constant. A constant can also hold a whole union, as in `infinity: const F32Bits = F32Bits(0x7F800000u32)`.

## Generic unions

A union can take type parameters. A type parameter used in a member must have the `ext` and `default` constraints, since a union holds only plain data that is valid when zeroed (see [What a union can hold](#what-a-union-can-hold)). One generic union can then reinterpret the bits of any such type as another:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Bitcast[From: ext + default, To: ext + default]: union
{
	from: From
	to: To
}

nan: const f32 = Bitcast[u32, f32](0x7FC00000u32).to

bitsOf: fun(value: f64) -> u64 => Bitcast[f64, u64](value).to

main: fun
{
	printf("%g %llx\n", f64(nan), bitsOf(-2.0))
	printf("%x %x\n", Bitcast[u16, u32](0xABCDu16).to, Bitcast[u64, u16](0x1122334455667788u64).to)
}
```

```output
nan c000000000000000
abcd 7788
```

When the two types have different sizes, the union is as large as the larger one: a smaller `From` leaves the rest of `to` zero, and a smaller `To` reads only the first bytes of `from`. Without the constraints, the member is rejected:

```cella error
~ mod example
~
Bare[T]: union
{
	value: T
}

Plain[T: ext]: union
{
	value: T
}
~
~ main: fun
~ {
~ }
```

```errors
Cannot store borrows in unions
Cannot store values without defaults in unions
```

## Using unions with C

A union has the layout of the C union with the same members in the same order, so a union or a record that contains one can be passed to C functions, by value or through a pointer, and C can fill it in. Here C's `memset` writes the bytes of a union through its address:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
ext
{
	memset: fun(dest: ptr, value: i32, count: usize) -> ptr
}

Bits: union
{
	float: f32
	raw: u32
	bytes: array[u8, 4]
}

main: fun
{
	var bits = Bits()
	memset(@bits, 0x3f, sizeOf(Bits))
	printf("%x %d %.4f\n", bits.raw, bits.bytes[2], f64(bits.float))
}
```

```output
3f3f3f3f 63 0.7471
```

The record-with-a-union shape from [Reading and writing members](#reading-and-writing-members), a tag field followed by a union, is how C APIs describe a value that can take one of several forms. In Cella's own code, an [enum with payloads](enums.md#payloads) does the same job and checks which case a value is. [Calling C](calling-c.md) covers declaring C functions and the types that can cross into C.
