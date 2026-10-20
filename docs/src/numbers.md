# Numbers and arithmetic

Cella has signed and unsigned integers from 8 to 128 bits, two pointer-sized integers and two floating-point types. This chapter covers their literals, how a literal gets its type, the operators, and what happens when a result doesn't fit.

## Integer types

Each integer type is named for its signedness and its width in bits:

| Signed | Unsigned | Size in bytes |
| --- | --- | --- |
| `i8` | `u8` | 1 |
| `i16` | `u16` | 2 |
| `i32` | `u32` | 4 |
| `i64` | `u64` | 8 |
| `i128` | `u128` | 16 |
| `isize` | `usize` | pointer size, 8 on 64-bit targets |

Signed types use two's complement, so an `i8` holds -128 to 127 and a `u8` holds 0 to 255. `usize` is the type of sizes, lengths and array indexes, and `isize` is its signed counterpart, the type of the difference between two pointers. `sizeOf` gives the size of a type or a value, as a `usize`:

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
	val count: i32 = 10
	printf("%zu %zu %zu %zu\n", sizeOf(i8), sizeOf(u64), sizeOf(i128), sizeOf(usize))
	printf("%zu\n", sizeOf(count))
}
```

```output
1 8 16 8
4
```

## Floating-point types

`f32` and `f64` are IEEE 754 single and double precision numbers, 4 and 8 bytes, like C's `float` and `double`. Arithmetic on them follows IEEE 754: dividing by zero gives an infinity, and a NaN compares unequal to everything, itself included.

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
	val half: f32 = 0.5
	val third = 1.0 / 3.0
	val zero = 0.0
	val nan = zero / zero
	printf("%.2f %.6f %f\n", half, third, 1.0 / zero)
	printf("%d %d\n", nan == nan, nan != nan)
}
```

```output
0.50 0.333333 inf
0 1
```

C's `printf` takes `f32` values as `double`, so `%f` prints both float types.

## Integer literals

An integer literal is written in decimal, or in hexadecimal, binary or octal with a prefix. Underscores among the digits are ignored, so they can group digits:

| Form | Example | Value |
| --- | --- | --- |
| Decimal | `1_000_000` | 1000000 |
| Hexadecimal, `0x` or `0X` | `0xFF`, `0xDEAD_BEEF` | 255, 3735928559 |
| Binary, `0b` or `0B` | `0b1010_0101` | 165 |
| Octal, `0o` or `0O` | `0o755` | 493 |

Leading zeros don't make a literal octal: `010` is ten. A minus sign is an operator, so `-0x10` is the negation of `0x10`.

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
	val million = 1_000_000
	val mask = 0xFF
	val flags = 0b1010_0101
	val mode = 0o755
	printf("%d %d %d %d %d %d\n", million, mask, flags, mode, 010, -0x10)
}
```

```output
1000000 255 165 493 10 -16
```

A digit that doesn't belong to the literal's base, or a prefix with no digits after it, is an error:

```cella error
~ mod example
~
main: fun
{
	val a = 0b102
	val b = 0o78
	val c = 0x
	val d = 0xFG
}
```

```errors
Invalid digit '2' in binary literal
Invalid digit '8' in octal literal
Expected hex digits
Invalid suffix 'G'
```

## Float literals

A float literal has a decimal point with digits on both sides, an exponent, or both: `1.5`, `1.5e3`, `2.5E-3`, `1e10`. Underscores separate digits as in integers.

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
	val exponent = 1.5e3
	val tiny = 2.5E-3
	val grouped = 1_000.000_5
	val large = 1e10
	printf("%.1f %.4f %.4f %.1f\n", exponent, tiny, grouped, large)
}
```

```output
1500.0 0.0025 1000.0005 10000000000.0
```

`1.` and `.5` aren't literals:

```cella error
~ mod example
~
main: fun
{
	val a = 1.
	val b = .5
}
```

```errors
Expected a digit after '.'
Expected a digit before '.'
```

A float literal too large for `f64` is an error, while one too small to represent becomes zero.

```cella error
~ mod example
~
main: fun
{
	val big = 1e400
}
```

```errors
Float literal too large to fit any type
```

## Type suffixes

A suffix names a literal's type directly: `300u16`, `0xFFu8`, `1_000_000u64`, `4usize`, `-128i8`. Integer literals take any integer suffix, and both integer and float literals take `f32` and `f64`, as in `0.5f32` or `2f32`. The value must fit the type.

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
	val mask = 0xF0u8
	val big = 1_000_000_000_000u64
	val low = -128i8
	val size = 4usize
	val half = 0.5f32
	printf("%d %llu %d %zu %.1f\n", mask, big, low, size, half)
	printf("%zu %zu %zu\n", sizeOf(mask), sizeOf(low), sizeOf(half))
}
```

```output
240 1000000000000 -128 4 0.5
1 1 4
```

A bare `u` suffix makes an unsigned literal without fixing its width. It takes whatever unsigned type it's used as, and on its own it's a `u32`, or a `u64` or `u128` when the value needs one. It can't become a signed or float type.

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
	val small = 5u
	val byte: u8 = 200u
	val top = 0x8000_0000_0000_0000u
	printf("%u %d %llx\n", small, byte, top)
	printf("%zu %zu %zu\n", sizeOf(small), sizeOf(byte), sizeOf(top))
}
```

```output
5 200 8000000000000000
4 1 8
```

These are errors:

```cella error
~ mod example
~
main: fun
{
	val a = 300u8
	val b = 128i8
	val c = 1.5i32
	val d = -1u8
	val e: i32 = 5u
	val f = 3q
}
```

```errors
'300' doesn't fit in 'u8'
'128' doesn't fit in 'i8'
Cannot use 'i32' on float literals
Operator '-' cannot be applied to 'u8'
Cannot convert type 'unsigned integer literal' to 'i32'
Invalid suffix 'q'
```

## How literals get their type

A literal without a suffix has no type of its own until something decides it. Where a type is expected, as in a typed declaration, an argument or a return value, the literal takes that type, and its value must fit:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
half: fun(value: u8) -> u8 => value / 2
~
main: fun
{
	val small: i8 = -100
	val ratio: f64 = 3
	printf("%d %d %.1f\n", small, half(200), ratio)
}
```

```output
-100 100 3.0
```

```cella error
~ mod example
~
main: fun
{
	val a: u8 = 300
	val b: i32 = 3000000000
	val c: i32 = 0xFFFFFFFF
	val d: u8 = -1
	val e: f32 = 16777217
}
```

```errors
'300' doesn't fit in 'u8'
'3000000000' doesn't fit in 'i32'
'0xFFFFFFFF' doesn't fit in 'i32'
'-1' doesn't fit in 'u8'
'16777217' can't be represented exactly in 'f32'
```

An integer literal that becomes a float type must be exactly representable in it; `16777217` needs 25 bits of precision and `f32` has 24. Float literals with a fraction round to the nearest value, as in C, so `0.1` is fine as an `f32`.

Where nothing decides, an integer literal is an `i32`, or an `i64` or `i128` if its value needs one, and a float literal is an `f64`:

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
	val small = 5
	val big = 3000000000
	val huge = 10000000000000000000
	val fraction = 2.5
	printf("%zu %zu %zu %zu\n", sizeOf(small), sizeOf(big), sizeOf(huge), sizeOf(fraction))
}
```

```output
4 8 16 8
```

A local declared from a literal without a type, like `val small = 5`, also takes its type from how the function uses it; [Variables](variables.md) explains how. A literal larger than every integer type is an error, "Integer literal too large to fit any type".

## Arithmetic

`+`, `-`, `*`, `/` and `%` work on integers and floats, and `-` and `+` also work as prefix operators. Integer division truncates toward zero, and the remainder has the sign of the left operand, as in C. `%` on floats gives the remainder of a truncating division too.

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
	val a = 7
	val b = -7
	printf("%d %d %d %d\n", a / 2, a % 2, b / 2, b % 2)
	printf("%.1f %.1f\n", 7.5 % 2.0, -7.5 % 2.0)
}
```

```output
3 1 -3 -1
1.5 -1.5
```

Operators bind as in C: prefix operators first, then `*`, `/` and `%`, then `+` and `-`, then shifts. One difference is that `&`, `^` and `|` bind tighter than comparisons, so `x & 1 == 0` means `(x & 1) == 0`. The [operator reference](operator-reference.md) lists every level.

`-` can't be applied to an unsigned value:

```cella error
~ mod example
~
main: fun
{
	val count: u32 = 5
	val negative = -count
}
```

```errors
Operator '-' cannot be applied to 'u32'
```

## How arithmetic is typed

The operands of an operator decide which operation runs. The type the result is going to doesn't change it; it only receives the result. With two `i32`s, `a * b` multiplies in `i32` even when it's stored in an `i64`, and `a / b` divides as integers even when it's stored in an `f64`. To compute in a wider type, convert an operand first:

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
	val a: i32 = 7
	val b: i32 = 2
	val quotient: f64 = a / b
	val precise: f64 = f64(a) / b
	val wide: i64 = i64(a) * 1000000000
	printf("%.2f %.2f %lld\n", quotient, precise, wide)
}
```

```output
3.00 3.50 7000000000
```

When the operands have the same type, the operation happens in that type. When one operand's type converts to the other's without losing anything, the operation happens in the wider type, and otherwise in the narrowest type both convert to. An `i32` and an `i64` add as `i64`s, an `i32` and an `f64` as `f64`s, and an `f32` and an `i32` as `f64`s, since an `f32` can't hold every `i32` exactly. Where no type holds both, the operation is an error:

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
	val count: i32 = 3
	val total: i64 = 40
	val ratio: f64 = 0.5
	val single: f32 = 1.5
	val sum = count + total
	val scaled = count * ratio
	val mixed = single * count
	printf("%lld %.1f %.1f\n", sum, scaled, mixed)
	printf("%zu %zu %zu\n", sizeOf(sum), sizeOf(scaled), sizeOf(mixed))
}
```

```output
43 1.5 4.5
8 8 8
```

```cella error
~ mod example
~
main: fun
{
	val total: i64 = 40
	val ratio: f64 = 0.5
	val result = total * ratio
}
```

```errors
No operation defined for '*' between 'i64' and 'f64'
```

### Literals take the other operand's type

A literal next to a typed operand takes that operand's type when it fits, so `small + 1` with a `u8` stays a `u8`, and `single / 2.0` with an `f32` stays an `f32`. A literal that doesn't fit takes its usual type instead, and the rules above apply: `small + 300` adds as `i32`s. A float literal next to an integer is an `f64`, so `count / 2.0` divides in `f64`.

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
	val small: u8 = 250
	val single: f32 = 1.5
	val count: i32 = 7
	val next = small + 1
	val far = small + 300
	val halved = single / 2.0
	val ratio = count / 2.0
	printf("%d %d %.2f %.2f\n", next, far, halved, ratio)
	printf("%zu %zu %zu %zu\n", sizeOf(next), sizeOf(far), sizeOf(halved), sizeOf(ratio))
}
```

```output
251 550 0.75 3.50
1 4 4 8
```

### Expressions made only of literals

An expression made only of integer literals is computed as if each literal had the destination's type, or `i32` where there is none. So `1 << 31` stored in an `i32` sets the sign bit, `~0` stored in a `u32` is all ones, and `3 / 5` stored in an `f64` is 0, since `3` and `5` are integers.

When a literal doesn't fit that type, or a step overflows it, the expression is computed exactly instead, and the result takes the smallest of `i32`, `i64` and `i128` that holds it. So `300 - 100` fits in a `u8`, and `2147483647 + 1` without a destination is an `i64`. Float literals combine in `f64`.

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
	val signBit: i32 = 1 << 31
	val allOnes: u32 = ~0
	val ratio: f64 = 3 / 5
	val fits: u8 = 300 - 100
	val grown = 2147483647 + 1
	val shifted = 1 << 40
	printf("%d %u %.1f %d\n", signBit, allOnes, ratio, fits)
	printf("%lld %zu %lld %zu\n", grown, sizeOf(grown), shifted, sizeOf(shifted))
}
```

```output
-2147483648 4294967295 0.0 200
2147483648 8 1099511627776 8
```

An exact result still has to fit the destination:

```cella error
~ mod example
~
main: fun
{
	val sum: u8 = 200 + 100
	val doubled: i32 = (1 << 31) * 2
	val fraction: i32 = 7 / 2.0
}
```

```errors
Cannot convert type 'i32' to 'u8'
Cannot convert type 'i64' to 'i32'
Cannot convert type 'float literal' to 'i32'
```

### Mixed signs

An operation on a signed and an unsigned integer happens in the smallest signed type that holds both, so `u8 + i8` is an `i16`, `u16 + i8` an `i32` and `u32 + i32` an `i64`. `u128` with a signed operand has nothing wider and is an error, and so are `usize` and `isize` with an operand of the other signedness unless every value fits on every target.

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
	val small: u8 = 200
	val negative: i8 = -100
	val count: u32 = 4000000000
	val offset: i32 = -2000000000
	val bytes = small + negative
	val words = count + offset
	printf("%d %zu %lld %zu\n", bytes, sizeOf(bytes), words, sizeOf(words))
}
```

```output
100 2 2000000000 8
```

```cella error
~ mod example
~
main: fun
{
	val signed: i32 = -1
	val huge: u128 = 1
	val size: usize = 3
	val wide: i64 = 2
	val sum = signed + huge
	val product = size * wide
}
```

```errors
No operation defined for '+' between 'i32' and 'u128'
No operation defined for '*' between 'usize' and 'i64'
```

## Overflow

Integer `+`, `-`, `*` and prefix `-`, and their compound assignments, check for overflow in debug builds. A result that doesn't fit the type stops the program with a panic that names the operation and where it happened:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
increment: fun(value: u8) -> u8 => value + 1
~
main: fun
{
	printf("%d\n", increment(254))
	printf("%d\n", increment(255))
}
```

```output
255
Panic at main.ce:8:36: addition overflow
```

The messages are "addition overflow", "subtraction overflow", "multiplication overflow" and "negation overflow". Release builds don't check, and the result wraps around: `255 + 1` in a `u8` is 0. The `OverflowChecks` project setting turns the checks on or off in every build:

```celp group=unchecked
OutputType = "Executable"
OverflowChecks = false
```

```cella group=unchecked
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
increment: fun(value: u8) -> u8 => value + 1
~
main: fun
{
	printf("%d\n", increment(255))
}
```

```output group=unchecked
0
```

When every operand is a constant, the compiler computes the result and reports overflow as an error, in every build:

```cella error
~ mod example
~
limit: const u8 = 200
~
main: fun
{
	val sum = limit + 100
	val product: i8 = i8(64) * 2
}
```

```errors
Addition overflows 'u8'
Multiplication overflows 'i8'
```

[Checks and panics](panics.md) covers panics and the project settings that control them.

## Wrapping operators

`+%`, `-%` and `*%` add, subtract and multiply with wraparound in every build, for code like hashes that means to wrap. Their compound forms are `+%=`, `-%=` and `*%=`. They take the same operands as `+`, `-` and `*`, but only integers.

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
	val byte: u8 = 255
	val count: u32 = 1
	val large: i32 = 2000000000
	printf("%d %u %d\n", byte +% 1, count -% 2, large *% 2)

	var hash: u32 = 2166136261
	hash *%= 16777619
	hash +%= 7
	printf("%u\n", hash)
}
```

```output
0 4294967295 -294967296
84696358
```

```cella error
~ mod example
~
main: fun
{
	val half = 1.5
	val sum = half +% 2.0
}
```

```errors
No operation defined for '+%' between 'f64' and 'float literal'
```

## Division by zero

Integer division and remainder by zero stop the program with "division by zero", and dividing the smallest signed value by -1, whose result doesn't fit, stops it with "division overflow". Unlike the overflow checks, these happen in every build. The remainder of the smallest value and -1 is 0.

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
divide: fun(a: i32, b: i32) -> i32 => a / b
remainder: fun(a: i32, b: i32) -> i32 => a % b
~
main: fun
{
	printf("%d %d\n", divide(7, 2), remainder(-2147483648, -1))
	printf("%d\n", divide(1, 0))
}
```

```output
3 0
Panic at main.ce:8:39: division by zero
```

A constant zero divisor is a compile error. Float division by zero isn't checked and gives an infinity or a NaN.

```cella error
~ mod example
~
main: fun
{
	var x = 10
	x = x / 0
	x %= 0
}
```

```errors
Division by zero
Division by zero
```

## Bitwise operators

`&`, `|` and `^` are bitwise and, or and exclusive or, and prefix `~` flips every bit. They work on integers of any width and follow the same typing rules as arithmetic. Floats have no bitwise operators.

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
	val flags: u8 = 0b1100
	printf("%d %d %d %d\n", flags & 0b1010, flags | 0b0001, flags ^ 0b1111, ~flags)
	val low = flags & 1 == 0
	printf("%d\n", low)
}
```

```output
8 13 3 243
1
```

## Shifts

`<<` shifts left and `>>` shifts right. A right shift of a signed value copies the sign bit in, and a right shift of an unsigned value shifts zeros in. The result has the left operand's type, and bits shifted past the top are dropped without an overflow check. The shift amount can be any integer type.

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
	val negative = -64
	val top: u32 = 0x8000_0000
	val byte: u8 = 0xFF
	val count: u8 = 3
	printf("%d %d %u %d %d\n", 1 << 4, negative >> 2, top >> 31, byte << 4, 1000 << count)
}
```

```output
16 -16 1 240 8000
```

A constant shift amount must be from 0 to one less than the width of the type. An amount known only at run time that's the width or more, or negative, shifts every bit out: the result is 0, or -1 for a right shift of a negative value.

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
shiftLeft: fun(value: u32, amount: i32) -> u32 => value << amount
shiftRight: fun(value: i32, amount: i32) -> i32 => value >> amount
~
main: fun
{
	printf("%u %u %u\n", shiftLeft(1, 31), shiftLeft(1, 40), shiftLeft(1, -1))
	printf("%d %d\n", shiftRight(-64, 40), shiftRight(64, 40))
}
```

```output
2147483648 0 0
-1 0
```

```cella error
~ mod example
~
main: fun
{
	val count: u32 = 1
	val a = count << 32
	val b = i32(1) << 40
}
```

```errors
Shift amount 32 is out of range for 'u32'
Shift amount 40 is out of range for 'i32'
```

## Rotations

`<<<` and `>>>` rotate: bits shifted out of one end come back in at the other. The amount wraps around the width, so rotating a `u8` by 9 is the same as rotating it by 1, and a negative amount rotates the other way.

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
	val byte: u8 = 0x81
	val word: u32 = 0x1234_5678
	printf("%d %d %d %d\n", byte <<< 1, byte >>> 1, byte <<< 9, byte <<< -1)
	printf("%08x %08x\n", word <<< 8, word >>> 8)
}
```

```output
3 192 3 192
34567812 78123456
```

## Comparisons

`<`, `<=`, `>`, `>=`, `==` and `!=` compare two numbers and give a `bool`. Any two integer types can be compared, even pairs with no common type for arithmetic such as `i128` and `u128`, and the comparison is by value, so a negative signed value is less than any unsigned one. Integers and floats compare where they could be added.

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
	val negative: i32 = -1
	val largest: u32 = 4294967295
	val wide: i64 = -5
	val small: u8 = 200
	printf("%d %d %d\n", negative < largest, negative == largest, wide < small)
}
```

```output
1 0 1
```

Comparisons chain: `a < b < c` means `a < b && b < c`, with `b` evaluated once. Any of `<`, `<=`, `>` and `>=` can be mixed in a chain, and `==` and `!=` chain the same way, so `a == b == c` means `a == b && b == c`. As with `&&`, a chain stops at the first comparison that fails, and the operands after it aren't evaluated.

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
~
main: fun
{
	val small: u8 = 7
	printf("%d %d\n", 0 <= small < 10, 1 < 3 < 2)
	printf(" %d\n", trace(1) < trace(2) < trace(3))
	printf(" %d\n", trace(1) == trace(2) == trace(3))
}
```

```output
1 0
[1][2][3] 1
[1][2] 0
```

## Compound assignment

Every binary arithmetic, bitwise, shift and rotate operator has a compound assignment form: `+=`, `-=`, `*=`, `/=`, `%=`, `+%=`, `-%=`, `*%=`, `&=`, `|=`, `^=`, `<<=`, `>>=`, `<<<=` and `>>>=`. `x += y` works like `x = x + y` with `x` evaluated once, and it's checked for overflow and division by zero like the operator. The right side must convert to the left side's type without loss, except for shifts and rotations, whose amount can be any integer type.

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
	var value = 100
	value += 5
	value -= 10
	value *= 3
	value /= 4
	value %= 50

	var bits: u8 = 0b1100
	bits &= 0b1010
	bits |= 0b0001
	bits <<= 2

	var total: u32 = 0
	val small: u8 = 200
	total += small
	printf("%d %d %u\n", value, bits, total)
}
```

```output
21 36 200
```

```cella error
~ mod example
~
main: fun
{
	var byte: u8 = 1
	val count: i32 = 5
	byte += count
	byte += 300
}
```

```errors
Cannot convert type 'i32' to 'u8'
'300' doesn't fit in 'u8'
```

## Implicit numeric conversions

A number converts to another numeric type without being written out only when every value of its type fits the other type exactly:

- A signed integer converts to any wider signed integer, and an unsigned integer to any wider integer of either signedness.
- `i8`, `i16`, `i32`, `u8` and `u16` convert to `isize`, and `u8`, `u16` and `u32` to `usize`. `isize` converts to `i64` and `i128`, and `usize` to `u64`, `u128` and `i128`.
- `f32` converts to `f64`.
- `i8`, `i16`, `u8` and `u16` convert to `f32`, and those and `i32` and `u32` to `f64`.

Everything else is written out. Named constants follow the same rules as variables: a `const` of type `i32` doesn't become a `usize`, even when its value fits. [Conversions](conversions.md) covers conversions in general.

```cella error
~ mod example
~
main: fun
{
	val count: i32 = 3
	val size: usize = count
	val wide: i64 = 5
	val offset: isize = wide
	val ratio: f64 = 0.5
	val single: f32 = ratio
}
```

```errors
Cannot convert type 'i32' to 'usize'
Cannot convert type 'i64' to 'isize'
Cannot convert type 'f64' to 'f32'
```

## Converting with `T(x)`

A conversion is written as a call to the type: `i64(x)`, `u8(x)`, `f32(x)`. Every numeric type converts to every other one this way. Converting a float to an integer truncates toward zero. Converting an `f64` to an `f32` rounds to the nearest value, and a value too large for `f32` becomes an infinity. A `bool` converts to any integer as 0 or 1; nothing converts to `bool`.

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
	val ratio = 2.7
	val count: i64 = 300
	val flag = true
	printf("%d %d %d\n", i32(ratio), i32(-ratio), i32(count))
	printf("%.1f %d %zu\n", f64(count), i32(flag), usize(count))
}
```

```output
2 -2 300
300.0 1 300
```

### Checked conversions

A conversion that can lose information is checked like arithmetic. A constant that doesn't fit is an error:

```cella error
~ mod example
~
main: fun
{
	val a = u8(300)
	val b = u32(-1)
	val c = i32(3.9e10)
}
```

```errors
'300' doesn't fit in 'u8'
'-1' doesn't fit in 'u32'
'3.9e10' doesn't fit in 'i32'
```

A value that doesn't fit at run time stops the program with "conversion overflow" in builds with overflow checks:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
narrow: fun(value: i32) -> u8 => u8(value)
~
main: fun
{
	printf("%d\n", narrow(200))
	printf("%d\n", narrow(-1))
}
```

```output
200
Panic at main.ce:8:34: conversion overflow
```

Without the checks, integer conversions keep the low bits, so 300 converted to a `u8` is 44 and -1 converted to a `u32` is 4294967295, and float-to-integer conversions saturate at the type's limits, with NaN becoming 0. To keep only the low bits on purpose, mask the value first, so it always fits:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
low: fun(value: u32) -> u8 => u8(value & 0xFF)
~
main: fun
{
	printf("%d %d\n", low(300), low(0xFFFF_FFFF))
}
```

```output
44 255
```
