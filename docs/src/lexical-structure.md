# Lexical structure

This chapter covers how Cella source text is put together: source files, comments, names, keywords, where lines may break, and how lists of members are separated.

## Source files

Cella source files have the `.ce` extension and hold UTF-8 text. Lines may end in `\n`, `\r\n` or `\r`. Spaces and tabs separate tokens and mean nothing else: indentation is never significant.

Every source file starts with a `mod` line naming the module the file belongs to:

```cella
mod game

ext
{
	puts: fun(text: cstr) -> i32
}

main: fun
{
	puts("ready")
}
```

```output
ready
```

Only comments and blank lines may come before it. A file without a `mod` line, a file with two of them, and a file with anything else before it are errors:

```cella error
~ mod first
~
main: fun
{
}

mod second
```

```errors
Cannot declare more than one module name
Cannot declare more than one module name
```

The other two cases report:

```text
All files must begin with a module name
Module name must precede all other declarations or imports
```

A module name can have several parts separated by dots, such as `mod game.physics`. [Modules and visibility](modules.md) covers modules, and how files share them.

Characters that change how text is displayed without being visible themselves, such as the Unicode controls that reverse the direction of text, are errors anywhere in a file, even in comments and strings:

```text
Cannot use U+202E in source
```

## Comments

`//` starts a comment that runs to the end of the line. `/*` starts a block comment that runs to the next `*/`, across lines if needed. Block comments nest, so a block comment can comment out code that has block comments of its own:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
// The program starts here.
main: fun
{
	val width = 4 // in tiles
	/* val height = 2
	/* the old size */
	*/
	printf("%d\n", width /* not height */)
}
```

```output
4
```

A block comment that is never closed is an error, reported at its `/*`:

```text
Unterminated block comment
```

## Names

A name, also called an identifier, starts with a letter or `_` and continues with letters, digits and `_`. Letters include those of every script, not only ASCII, and digits are only allowed after the first character. Names are case-sensitive: `count` and `Count` are different names.

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Count: rec
{
	value: i32
}

main: fun
{
	val count = Count(1)
	val player2 = 2
	printf("%d %d\n", count.value, player2)
}
```

```output
1 2
```

The compiler accepts any of these names, but by default it gives a hint for names that don't follow the usual style, such as a variable named `Count` or `_offset`. [Project settings](project-settings.md#naming) covers the rules and how to change them.

Names are compared after Unicode normalization (NFC), so a letter written as one character and the same letter written as a base letter and a combining mark are the same name.

`_` on its own isn't a name. It marks a value or parameter that is never used, such as `val _ = make()` or a parameter written `_: i32`, and it can't be read:

```cella error
~ mod example
~
main: fun
{
	val _ = 3
	val copy = _
}
```

```errors
Cannot use '_' as a value
```

Names are usually written in camelCase for values and functions and PascalCase for types. The compiler doesn't enforce either.

## Keywords

Keywords are words with a meaning of their own. Reserved keywords can never be names:

```text
alignOf  atomic   break    const    cont     default  do       drop
dyn      else     false    for      fun      if       imm      in
is       loop     match    mut      nameOf   new      null     own
panic    ref      ret      self     sizeOf   true     undef    val
var      when     while
```

```cella error
~ mod example
~
main: fun
{
	val loop = 1
	val default = 2
}
```

```errors
'loop' is a keyword
'default' is a keyword
```

Contextual keywords mean something only in certain places, such as the start of a declaration or after a declaration's colon. Everywhere else they are ordinary names, such as the fields of this record ([Records](records.md) covers records):

```text
as       copy     enum     ext      get      impl     mod      noref
op       prop     pub      pvt      rec      req      set      trait
union    use
```

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Range: rec
{
	get: i32
	set: i32
}

main: fun
{
	val copy = Range(1, 2)
	printf("%d %d\n", copy.get, copy.set)
}
```

```output
1 2
```

[Keywords](keywords.md) lists every keyword with what it does.

## Lines and statements

A new line ends a statement. There are no semicolons. Most statements fit on one line:

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
	val width = 3
	val height = 4
	printf("%d\n", width * height)
}
```

```output
12
```

### Wrapping long lines

A statement continues on the next line when its line ends in a way that needs more: after a binary operator, an assignment operator, `is` or `=>`. Wrap a long expression after an operator. `volume` below has an expression body, `=>` followed by its result, which [Functions](functions.md#expression-bodies) covers:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
volume: fun(width: i64, height: i64, depth: i64) -> i64 =>
	width * height * depth

main: fun
{
	val total = 1 +
		2 *
		3
	val inRange = total > 2 &&
		total < 10
	printf("%d %d %lld\n", total, inRange, volume(2, 3, 4))
}
```

```output
7 1 24
```

A line can't start with a binary operator, an assignment operator, `is` or `=>`:

```cella error
~ mod example
~
main: fun
{
	val total = 3
	val inRange = total > 2
		&& total < 10
	val small = total
		is 3
}
```

```errors
Cannot start a line with '&&'
Cannot start a line with 'is'
```

`+`, `-` and `*` are different, because they can also start an expression: `+ 2`, `- 2` and `* p` are complete expressions on their own. A line that starts with one of them starts a new statement, and a value on its own isn't a statement:

```cella error
~ mod example
~
main: fun
{
	val total = 1
		+ 2
}
```

```errors
Cannot use values as statements
```

The same goes for declarations. The `=` before a value and the `=>` before an expression body must stay on the line before:

```cella error
~ mod example
~
limit: const i32
	= 5

twice: fun(x: i32) -> i32
	=> x * 2

main: fun
{
}
```

```errors
Cannot start a line with '='
Cannot start a line with '=>'
```

### Inside parentheses and brackets

Inside `( )` and `[ ]`, new lines don't end anything, so arguments, array elements and parenthesized expressions can be split anywhere:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
add: fun(a: i32, b: i32) -> i32 => a + b

main: fun
{
	val sum = add(
		10,
		20
	)
	val values = [
		1,
		2,
		3
	]
	val scaled = (sum
		* 2)
	printf("%d %d %d\n", sum, values[2], scaled)
}
```

```output
30 3 60
```

The `(` of a call and the `[` of an index must still be on the same line as what they apply to. On the next line, they start a new statement:

```cella error
~ mod example
~
twice: fun(x: i32) -> i32 => x * 2

main: fun
{
	val result = twice
		(4)
}
```

```errors
Cannot use values as statements
```

### Member access

`.` may start a line, so a chain of member accesses can be written one per line:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Size: rec
{
	width: i32
	height: i32
}

Window: rec
{
	size: Size
}

main: fun
{
	val window = Window(Size(640, 480))
	val width = window
		.size
		.width
	printf("%d\n", width)
}
```

```output
640
```

### Prefix operators

A prefix operator, such as `-`, `!`, `~`, `@` or `*`, must have its operand on the same line:

```cella error
~ mod example
~
main: fun
{
	val negative = -
		5
}
```

```errors
Expected an expression
```

## Separating members

Lists of members in braces, such as the fields of a record, the cases of an enum and the arms of a `match`, follow one rule: neighbouring items are separated either by a `,` on the same line or by a new line. One item per line needs no commas, and several items on one line need them. [Records](records.md), [Enums](enums.md) and [Pattern matching](pattern-matching.md) cover the forms in this example:

```cella
~ mod example
~
~ ext
~ {
~ 	printf: fun(format: cstr, ...) -> i32
~ }
~
Color: enum { red, green, blue }

Size: rec
{
	width: i32
	height: i32
}

main: fun
{
	val size = Size(3, 4)
	val code = match Color.green { red => 1, green => 2, blue => 3 }
	printf("%d %d\n", size.width * size.height, code)
}
```

```output
12 2
```

A `,` at the end of a line, a `,` after the last item, and two items on one line without a `,` are errors:

```cella error
~ mod example
~
Size: rec
{
	width: i32,
	height: i32
}

Pair: rec { first: i32, second: i32, }

Point: rec { x: i32 y: i32 }

main: fun
{
}
```

```errors
Cannot separate members on separate lines with ','
Cannot end lists with ','
Expected ',' or a new line before the next member
```

Lists in parentheses and brackets, such as arguments, parameters and array elements, always use commas, and they can't end with one either.

Top-level declarations are separated by new lines only:

```cella error
~ mod example
~
one: fun -> i32 => 1 two: fun -> i32 => 2

main: fun
{
}
```

```errors
Expected a new line before the next declaration
```

## Literals

Literals write values directly in the source. Each kind has its own chapter:

| Literal | Examples | Chapter |
| --- | --- | --- |
| Integers | `42`, `1_000_000`, `0xFF`, `0b1010`, `0o17`, `7u8` | [Numbers and arithmetic](numbers.md) |
| Floats | `3.14`, `1.5e3`, `2.0f32` | [Numbers and arithmetic](numbers.md) |
| Booleans | `true`, `false` | [Bool, char and strings](text.md) |
| Characters | `'a'`, `'\n'` | [Bool, char and strings](text.md) |
| Strings | `"hello"`, `"tab\there"` | [Bool, char and strings](text.md) |
| Interpolated strings | `"{count} items"` | [Bool, char and strings](text.md#interpolated-strings), [String templates](templates.md) |
| Arrays | `[1, 2, 3]` | [Arrays](arrays.md) |
| Null pointers | `null` | [Pointers and raw memory](pointers.md) |
| Uninitialized storage | `undef` | [Variables and constants](variables.md) |

A character that can't start any token is an error:

```cella error
~ mod example
~
main: fun
{
	val price = 5 $
}
```

```errors
Unexpected character '$'
```
