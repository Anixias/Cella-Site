# Bool, char and strings

This chapter covers `bool`, `char` for single characters, and the two string types: `str`, a pointer and a length, and `cstr`, a C string. It also covers string literals, their escape sequences and suffixes, interpolated strings with constant holes, and `nameOf`.

## `bool`

A `bool` is `true` or `false` and takes one byte. `!` negates it, and `&&` and `||` are logical and and or. They stop as soon as the result is known, so the right side runs only when it's needed. `&`, `|` and `^` also work on `bool`s and always evaluate both sides; `^` is true when exactly one side is. `==` and `!=` compare two `bool`s.

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
check: fun(name: cstr, value: bool) -> bool
{
	printf("%s ", name)
	ret value
}
~
main: fun
{
	val a = check("first", false) && check("second", true)
	printf("-> %d\n", a)
	val b = check("first", false) & check("second", true)
	printf("-> %d\n", b)
	printf("%d %d %d\n", !a, true ^ false, a == b)
}
```

```output
first -> 0
first second -> 0
1 1 1
```

`&=`, `|=` and `^=` assign the result back. `bool`s have no ordering, and no arithmetic.

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
	var ready = true
	val failed = false
	ready &= !failed
	ready ^= true
	printf("%d\n", ready)
}
```

```output
0
```

Conditions in `if`, `while` and the other control-flow forms must be `bool`s. Integers aren't true or false on their own; compare them instead, as in `count != 0`. A `bool` converts to an integer with `i32(flag)`, as 0 or 1, but nothing converts to `bool`.

```cella error
~ mod example
~
main: fun
{
	val count = 1
	val flag: bool = 1
	val made = bool(count)
	val inverted = !count
	val ordered = true < false
}
```

```errors
Cannot convert type 'integer literal' to 'bool'
No constructor for 'bool' accepts argument of type 'i32'
Operator '!' cannot be applied to 'i32'
No operation defined for '<' between 'bool' and 'bool'
```

## `char`

A `char` is one Unicode character, stored as its code point in 4 bytes. Any code point from U+0000 to U+10FFFF is a valid `char` except the surrogates U+D800 to U+DFFF. A `char` literal is a character in single quotes, and the source file's UTF-8 can hold any character directly:

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
	val letter = 'a'
	val accented = 'é'
	val emoji = '😀'
	printf("%u %u %u %zu\n", u32(letter), u32(accented), u32(emoji), sizeOf(letter))
}
```

```output
97 233 128512 4
```

A literal holds exactly one character, or one [escape sequence](#escape-sequences):

```cella error
~ mod example
~
main: fun
{
	val empty = ''
	val two = 'ab'
	val unknown = '\q'
}
```

```errors
Invalid character literal
Invalid character literal
Invalid character literal
```

### Operations on `char`

Adding an integer to a `char`, or subtracting one, gives another `char`. Subtracting two `char`s gives the distance between them as an `i32`. `char`s compare by code point, and a `for` loop can walk a range of them, as [Control flow](control-flow.md#for-over-ranges) shows.

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
	val letter = 'c'
	val next = letter + 1
	val back = letter - 2
	val offset = letter - 'a'
	printf("%c %c %d\n", next, back, offset)
	printf("%d %d\n", letter < 'd', letter == 'c')
}
```

```output
d a 2
1 1
```

A `char` isn't an integer: other arithmetic, the bitwise operators and mixing a `char` with an integer type are errors.

```cella error
~ mod example
~
main: fun
{
	val letter = 'a'
	val byte: u8 = 97
	val sum = 'a' + 'b'
	val doubled = letter * 2
	val masked = letter & 1
	val same = byte == letter
}
```

```errors
No operation defined for '+' between 'char' and 'char'
No operation defined for '*' between 'char' and 'integer literal'
No operation defined for '&' between 'char' and 'integer literal'
No operation defined for '==' between 'u8' and 'char'
```

A step past U+10FFFF or into the surrogates is checked like integer overflow. With constants it's a compile error, "Addition overflows 'char'", and at run time a panic with "char overflow" in builds with overflow checks.

### Converting `char`s

A `char` converts to any integer type with `T(c)`, giving its code point, and an integer converts to a `char` with `char(n)`. Neither conversion happens implicitly. Both are checked: a code point that doesn't fit the integer type, or an integer that isn't a valid `char`, is an error for a constant and a "conversion overflow" panic at run time.

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
toChar: fun(code: u32) -> char => char(code)
~
main: fun
{
	val code = u32('A')
	printf("%u %c\n", code, toChar(code + 1))
	printf("%c\n", toChar(55296))
}
```

```output
65 B
Panic at main.ce:8:35: conversion overflow
```

```cella error
~ mod example
~
implicit: fun(letter: char) -> u32 => letter
narrow: fun -> u8 => u8('€')
surrogate: fun -> char => char(55296)
~
~ main: fun
~ {
~ }
```

```errors
Cannot convert type 'char' to 'u32'
'8364' doesn't fit in 'u8'
'55296' doesn't fit in 'char'
```

### Character literals with a suffix

An integer type suffix after a `char` literal makes it an integer holding the code point, as in `'a'u8`. This is how byte-oriented code compares bytes with characters, since a `u8` and a `char` don't mix. The code point must fit the type.

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
isDigit: fun(byte: u8) -> bool => byte >= '0'u8 && byte <= '9'u8
~
main: fun
{
	val text: str = "a7b"
	val digit = text[1] - '0'u8
	printf("%d %d %d\n", isDigit(text[0]), isDigit(text[1]), digit)
	printf("%d %d\n", '€'u16, '\n'i32)
}
```

```output
0 1 7
8364 10
```

```cella error
~ mod example
~
main: fun
{
	val a = '€'u8
	val b = 'a'f32
}
```

```errors
'€' doesn't fit in 'u8'
Cannot use 'f32' on char literals
```

## Escape sequences

`char` and string literals share these escape sequences:

| Escape | Meaning |
| --- | --- |
| `\n`, `\r`, `\t` | new line, carriage return, tab |
| `\0` | the zero character |
| `\\`, `\'`, `\"` | a backslash, a single quote, a double quote |
| `\a`, `\b`, `\f`, `\v` | bell, backspace, form feed, vertical tab |
| `\xHH` | the character with hex code `HH`, from `00` to `7F` |
| `\oNNN` | the character with octal code `NNN`, from `000` to `177` |
| `\uXXXX` | the code point `XXXX`, exactly four hex digits |
| `\UXXXXXXXX` | the code point `XXXXXXXX`, exactly eight hex digits |

Strings also take `\{` and `\}` for braces, which [interpolated strings](#interpolated-strings) otherwise use. `\0` always means the zero character, so `"\012"` is a zero followed by the characters `1` and `2`; octal codes are written with `\o`. `\x` and `\o` cover only the ASCII range. `\u` and `\U` take any code point that is a valid `char`, and a string stores it as its two to four UTF-8 bytes.

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
dump: fun(text: str)
{
	for i in 0..text.byteLength
		printf(" %02x", text[i])

	printf("\n")
}
~
main: fun
{
	dump("tab\there")
	dump("C:\\new")
	dump("\x41\o102\"")
	dump("caf\u00e9 \U0001F600")
	dump("\012")
}
```

```output
 74 61 62 09 68 65 72 65
 43 3a 5c 6e 65 77
 41 42 22
 63 61 66 c3 a9 20 f0 9f 98 80
 00 31 32
```

Any other backslash sequence, or one with the wrong digits, is an error:

```cella error
~ mod example
~
main: fun
{
	val a = "\q"
	val b = "\x80"
	val c = "\u12"
	val d = "\uD800"
}
```

```errors
Invalid escape sequence in string literal
Invalid escape sequence in string literal
Invalid escape sequence in string literal
Invalid escape sequence in string literal
```

## `str`

A `str` is a read-only view of UTF-8 text: a pointer to its first byte and the number of bytes, 16 bytes in all on a 64-bit target. The two parts are its read-only properties `data`, a `ptr[u8]`, and `byteLength`, a `usize`. A `str` doesn't own its bytes, and nothing guarantees a zero byte after them.

The length counts bytes, not characters: a character outside ASCII takes two to four bytes.

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
	val plain: str = "hello"
	val accented: str = "héllo"
	val emoji: str = "😀"
	printf("%zu %zu %zu %zu\n", plain.byteLength, accented.byteLength, emoji.byteLength, sizeOf(plain))
}
```

```output
5 6 4 16
```

C's `printf` prints a `str` with `%.*s`, which takes the length as an `int` and then the pointer:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
show: fun(text: str) => printf("[%.*s]\n", i32(text.byteLength), text.data)
~
main: fun
{
	show("hello world")
	show("")
}
```

```output
[hello world]
[]
```

### Indexing bytes

`text[i]` reads the byte at index `i` as a `u8`. The index is a `usize`, or a type that converts to one implicitly, and it's checked against `byteLength`: reading past the end stops the program with "index out of bounds".

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
byteAt: fun(text: str, index: usize) -> u8 => text[index]
~
main: fun
{
	val text: str = "abc"
	var total: u32 = 0
	for i in 0..text.byteLength
		total += text[i]

	printf("%c %u\n", byteAt(text, 2), total)
	printf("%c\n", byteAt(text, 3))
}
```

```output
c 294
Panic at main.ce:8:47: index out of bounds
```

A `str` can't be changed through: its bytes and its properties are read-only.

```cella error
~ mod example
~
main: fun
{
	var text: str = "hello"
	text[0] = 72
	text.byteLength = 3
}
```

```errors
Cannot write through 'str'
Cannot reassign read-only properties
```

### Building a `str`

`str(data, byteLength)` makes a `str` from a `ptr[u8]` and a length, the reverse of its two properties. This is how code takes part of a string, or views bytes from elsewhere as text, such as a buffer or a C string. `str()` is the empty string. Below, `text.data + start` points `start` bytes further on; [Pointers and raw memory](pointers.md#pointer-arithmetic) covers pointer arithmetic.

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ 	strlen: fun(text: cstr) -> usize
~ }
~
show: fun(text: str) => printf("[%.*s]\n", i32(text.byteLength), text.data)
~
slice: fun(text: str, start: usize, length: usize) -> str => str(text.data + start, length)
~
main: fun
{
	val text: str = "hello world"
	show(slice(text, 6, 5))
	show(str(text.data, 4))

	val name: cstr = "from C"
	show(str(name, strlen(name)))

	val empty = str()
	printf("%zu\n", empty.byteLength)
}
```

```output
[world]
[hell]
[from C]
0
```

The compiler doesn't check that the pointer and length describe valid UTF-8. A `str` built from a pointer borrows whatever the pointer came from, so one built from a local buffer can't be returned; [Borrows](borrows.md) covers the rules.

```cella error
~ mod example
~
local: fun -> str
{
	var buffer: array[u8, 4]
	buffer[0] = 65
	ret str(@buffer[0], 1)
}
~
~ main: fun
~ {
~ }
```

```errors
Cannot return borrows of local variables
```

`==` and `+` don't work on `str` values. `+` works only on constant strings, described [below](#constant-strings).

## `cstr`

A `cstr` is a pointer to a zero-terminated string, which is what C functions take and return. It's 8 bytes on a 64-bit target and has no length; C functions such as `strlen` find the end by looking for the zero byte. `c[i]` reads byte `i` as a `u8`; with no length to compare against, the index isn't checked. A `cstr` can be `null`, and it converts implicitly to a plain `ptr`, the untyped pointer described in [Pointers and raw memory](pointers.md#the-untyped-pointer-ptr).

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ 	strlen: fun(text: cstr) -> usize
~ }
~
main: fun
{
	val word: cstr = "world"
	printf("%s %zu %c %d\n", word, strlen(word), word[0], word[5])

	var missing: cstr = null
	printf("%d\n", missing == null)
	missing = word
	printf("%d %zu\n", missing == null, sizeOf(missing))
}
```

```output
world 5 w 0
1
0 8
```

A `str` doesn't convert to a `cstr`, since its bytes need not be followed by a zero, and a `cstr` has no arithmetic.

```cella error
~ mod example
~
~ ext
~ {
~ 	puts: fun(text: cstr) -> i32
~ }
~
main: fun
{
	val text: str = "hello"
	puts(text)
	val word: cstr = "world"
	val rest = word + 1
}
```

```errors
Cannot convert type 'str' to 'cstr'
No operation defined for '+' between 'cstr' and 'integer literal'
```

## String literals

A string literal in double quotes has no type of its own, like a number. It becomes a `str` or a `cstr` where it's used. As a `cstr`, its bytes are followed by a zero; the zero isn't counted in a `str`'s `byteLength`. A literal's `byteLength` and `data` can be read directly, and `byteLength` is a constant.

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ 	puts: fun(text: cstr) -> i32
~ }
~
show: fun(text: str) => printf("[%.*s]\n", i32(text.byteLength), text.data)
~
main: fun
{
	show("as a str")
	puts("as a cstr")
	var buffer: array[u8, "abc".byteLength]
	printf("%zu %zu\n", "héllo".byteLength, buffer.length)
}
```

```output
[as a str]
as a cstr
6 3
```

A local declared from a literal takes its type from how the function uses it, and is a `str` when nothing decides. A literal used both ways needs two literals, or an explicit type:

```cella error
~ mod example
~
~ ext
~ {
~ 	puts: fun(text: cstr) -> i32
~ }
~
show: fun(text: str)
{
}
~
main: fun
{
	val greeting = "hi"
	show(greeting)
	puts(greeting)
}
```

```errors
Cannot infer the type of 'greeting' from 'str' and 'cstr'
```

A string literal must end on the line it starts on, and two literals next to each other don't join; `+` joins [constant strings](#constant-strings).

### String literal suffixes

A suffix of `u8`, `u16` or `u32` turns a string literal into an array of its encoded text, with no zero at the end: `u8` gives the UTF-8 bytes, `u16` the UTF-16 code units and `u32` the code points. This is useful for byte signatures and for APIs that take UTF-16.

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
	val magic = "GIF89a"u8
	val accented = "hé"u8
	val units = "hé"u16
	val points = "h😀"u32
	printf("%zu %d %d\n", magic.length, magic[0], magic[5])
	printf("%zu %d %d %d\n", accented.length, accented[0], accented[1], accented[2])
	printf("%zu %d %d\n", units.length, units[0], units[1])
	printf("%zu %d %d\n", points.length, points[0], points[1])
}
```

```output
6 71 97
3 104 195 169
2 104 233
2 104 128512
```

`magic` is an `array[u8, 6]`; [Arrays](arrays.md) covers arrays. Other suffixes are errors:

```cella error
~ mod example
~
main: fun
{
	val a = "abc"i32
	val b = "abc"f64
}
```

```errors
Cannot use 'i32' on string literals
Cannot use 'f64' on string literals
```

### Constant strings

String literals, `const` declarations of type `str` or `cstr`, and the results of `nameOf` are constant strings. A `val` isn't one, even at the top level of a module. `+` joins constant strings into a new one, at compile time. A `str` constant and a `cstr` constant don't join with each other.

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
title: const str = "Cella"
version: const cstr = "1.0"
full: const str = title + " " + "language"
tagged: const cstr = version + "-beta"
~
show: fun(text: str) => printf("%.*s\n", i32(text.byteLength), text.data)
~
main: fun
{
	show(full)
	printf("%s\n", tagged)
	val joined = "x" + "y" + "z"
	show(joined)
}
```

```output
Cella language
1.0-beta
xyz
```

```cella error
~ mod example
~
title: const str = "Cella"
label: const cstr = "c"
~
main: fun
{
	var name = "world"
	val joined = title + name
	val mixed = title + label
	val number = "a" + 5
}
```

```errors
'name' isn't a constant
No operation defined for '+' between 'str' and 'cstr'
No operation defined for '+' between 'string literal' and 'integer literal'
```

## Interpolated strings

A string literal can contain holes in braces, as in `"{title} v{version}"`. Outside a template, an interpolated string is a constant string: every hole must hold a constant string, and the compiler joins the pieces. The result is a string literal, usable as a `str` or a `cstr`. Holes can hold `str` and `cstr` constants alike, `nameOf`, `+` of constant strings, and other string literals, including interpolated ones.

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
title: const str = "Cella"
version: const cstr = "1.0"
banner: const cstr = "{title} v{version}!"
~
Point: rec
{
	x: i32
}
~
main: fun
{
	const name = "world"
	printf("%s\n", banner)
	printf("%s\n", "Hello, {name}! {nameOf(Point)} {"a" + "b"} [{"{title}"}]")
}
```

```output
Cella v1.0!
Hello, world! Point ab [Cella]
```

A hole with a value that isn't a constant string is an error. Holes that hold numbers or other run-time values, and holes with format specs like `{price:.2}`, belong to [string templates](templates.md), where a function receives the pieces and the values and decides how to write them.

```cella error
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
title: const str = "Cella"
~
main: fun
{
	val count = 5
	val name: str = "world"
	printf("count = {count}\n")
	printf("hello {name}\n")
	printf("spec {title:x}\n")
}
```

```errors
'i32' is not a string
'name' isn't a constant
Cannot use format specs in constant strings
```

### Braces in strings

A `{` in any string starts a hole, so a literal brace is written `\{`. A `}` on its own is an ordinary character, and `\}` is accepted too. This matters for C format strings and for text like code or JSON:

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
	printf("\{%d}\n", 5)
	printf("struct \{ int x; }\n")
}
```

```output
{5}
struct { int x; }
```

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
	printf("{%d}\n", 5)
	printf("x{}y\n")
}
```

```errors
Expected an expression after '{'
Expected an expression
```

A string literal with holes can't take a suffix: `"a{x}"u8` is "Cannot use 'u8' on interpolated strings".

## `nameOf`

`nameOf(x)` is a constant string holding the name of `x` as it's written in the code, without its qualifiers: `nameOf(geometry.area)` is `"area"`. It takes anything with a name, such as a type, function, module, variable, parameter, field, method, enum case or label, and checks that the name exists. Like a string literal, it's usable as a `str` or a `cstr`.

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
~
Team: enum
{
	red
	blue
}
~
describe: fun(count: i32) -> cstr => nameOf(count)
~
main: fun
{
	val point = Point(1, 2)
	printf("%s %s %s\n", nameOf(point), nameOf(point.y), nameOf(Point.x))
	printf("%s %s %s %s\n", nameOf(Team), nameOf(Team.blue), nameOf(describe), describe(1))
	val text = nameOf(Point)
	printf("%zu\n", text.byteLength)
}
```

```output
point y x
Team blue describe count
5
```

A name that doesn't exist is reported as usual, and anything other than a name is an error:

```cella error
~ mod example
~
Point: rec
{
	x: i32
}
~
first: fun -> str => nameOf(Point.z)
second: fun -> str => nameOf(5)
third: fun -> str => nameOf("main")
~
main: fun
{
}
```

```errors
Type 'Point' has no member 'z'
Expected a name
Expected a name
```
