# Built-in types

These are the types the language provides. Everything else, such as records, enums, unions and traits, is declared in code. Sizes and alignments are in bytes, as `sizeOf` and `alignOf` report them on the 64-bit targets Cella builds for. The default is the value a variable of the type starts with when it's declared without one.

## Summary

| Type | Size | Alignment | Default |
| --- | --- | --- | --- |
| `i8`, `u8` | 1 | 1 | `0` |
| `i16`, `u16` | 2 | 2 | `0` |
| `i32`, `u32` | 4 | 4 | `0` |
| `i64`, `u64` | 8 | 8 | `0` |
| `i128`, `u128` | 16 | 16 | `0` |
| `isize`, `usize` | 8 | 8 | `0` |
| `f32` | 4 | 4 | `0.0` |
| `f64` | 8 | 8 | `0.0` |
| `bool` | 1 | 1 | `false` |
| `char` | 4 | 4 | the character with code 0 |
| `str` | 16 | 8 | the empty string |
| `cstr` | 8 | 8 | `null` |
| `ptr`, `ptr[T]` | 8 | 8 | `null` |
| `ptr[dyn[K]]` | 16 | 8 | `null` |
| `array[T, N]` | `N` times the size of `T` | the alignment of `T` | every element at its default |
| `imm[T]`, `mut[T]` | 8 | 8 | none |
| `imm[dyn[K]]`, `mut[dyn[K]]` | 16 | 8 | none |
| `fun[...]`, `ref fun[...]` | 16 | 8 | none |
| `ext fun[...]` | 8 | 8 | none |
| `fstr[K]` | 24 | 8 | none |
| `dyn[K]` | no fixed size | | none |
| `never` | no size | | none |

`sizeOf` and `alignOf` take a type or a value and give a `usize`:

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
	printf("%zu %zu\n", sizeOf(i128), alignOf(i128))
	printf("%zu %zu\n", sizeOf(str), alignOf(str))
	printf("%zu %zu\n", sizeOf(array[u16, 5]), alignOf(array[u16, 5]))
	printf("%zu %zu\n", sizeOf(fun[i32 -> i32]), sizeOf(ext fun[i32 -> i32]))
}
```

```output
16 16
16 8
10 2
16 8
```

## Integers

| Type | Smallest value | Largest value |
| --- | --- | --- |
| `i8` | -128 | 127 |
| `i16` | -32768 | 32767 |
| `i32` | -2147483648 | 2147483647 |
| `i64` | -2⁶³ | 2⁶³ - 1 |
| `i128` | -2¹²⁷ | 2¹²⁷ - 1 |
| `isize` | -2⁶³ | 2⁶³ - 1 |
| `u8` | 0 | 255 |
| `u16` | 0 | 65535 |
| `u32` | 0 | 4294967295 |
| `u64` | 0 | 2⁶⁴ - 1 |
| `u128` | 0 | 2¹²⁸ - 1 |
| `usize` | 0 | 2⁶⁴ - 1 |

Signed integers use two's complement. `isize` and `usize` are as wide as a pointer; `usize` is the type of sizes and lengths. [Numbers](numbers.md) covers literals, arithmetic and overflow.

## Floating-point numbers

`f32` and `f64` are IEEE 754 single and double precision numbers. [Numbers](numbers.md) covers them.

## `bool` and `char`

`bool` is `true` or `false`, stored in one byte. `char` is a Unicode scalar value: a code point from 0 to 0x10FFFF, other than the surrogates 0xD800 to 0xDFFF. [Bool, char and strings](text.md) covers both.

## `str` and `cstr`

A `str` is a run of UTF-8 bytes it doesn't own, with two read-only properties: `data`, a `ptr[u8]` to the first byte, and `byteLength`, a `usize`. A `cstr` is a single pointer to zero-terminated bytes, the form C functions take. A string literal becomes either, depending on the type it's given. [Bool, char and strings](text.md) covers both.

## Pointers

`ptr[T]` points to a `T`, and `ptr` points to memory of no particular type. Nothing is checked through a pointer. A pointer to a trait object, `ptr[dyn[K]]`, also carries what it needs to call the trait's members, so it's twice as large. [Pointers](pointers.md) covers them.

## Arrays

`array[T, N]` holds `N` values of type `T` in a row, with no padding between them, so its size is `N` times the size of `T`. `N` is a `usize` known at compile time and can be 0. [Arrays](arrays.md) covers them.

## Borrow types

`imm[T]` and `mut[T]` borrow a `T` that lives somewhere else, without and with the right to write it. A borrow is the size of a pointer, or twice that when it borrows a trait object. [Borrows](borrows.md) covers them.

## Function types

`fun[A, B -> R]` holds a function that takes `A` and `B` and returns `R`. `ref fun[...]` can also hold closures, which borrow the variables they capture. `ext fun[...]` holds a C function pointer, the only kind C can call. [Function values and closures](closures.md#function-types) covers them.

## Trait objects

`dyn[K]` is a value of some type that implements the trait `K`, chosen at run time. Its size depends on that type, so it's used only behind a borrow or a pointer, never by value. [Trait objects](trait-objects.md) covers it.

## Templates

`fstr[K]` holds the pieces of an interpolated string, with every value it fills in implementing the trait `K`. [String templates](templates.md) covers it.

## `never`

`never` is the result type of a function that doesn't return, such as one that always exits or loops forever. It's only allowed as a result type, and it has no size. [Functions](functions.md#functions-that-never-return) covers it.

## Defaults

Writing a built-in type's name with empty parentheses gives its default, and a variable declared with `var` and no value starts at its default. For every type that has one, the default is all zero bytes:

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
	printf("%d %.1f %d %u\n", i32(), f64(), bool(), u32(char()))
	printf("%zu %d %d\n", str().byteLength, cstr() == null, ptr[u8]() == null)
	var counts: array[i32, 3]
	counts[1] += 5
	printf("%d %d %d\n", counts[0], counts[1], counts[2])
}
```

```output
0 0.0 0 0
0 1 1
0 5 0
```

Borrows, function values, templates and trait objects have no default, since all zero bytes isn't a valid value of them. A variable of one of these types must be given a value before it's used:

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
	val handler: fun[i32 -> i32]
	printf("%d\n", handler(1))
}
```

```errors
Cannot use uninitialized values
```

The types with a default meet the `T: default` constraint, and an array has one when its element type does. [Generics](generics.md#constraints) covers constraints.

## Copies and borrows

Every built-in type other than `dyn[K]` and `never` can be copied, so they meet `T: copy`. Borrow types, `str`, `ref fun[...]`, `fstr[K]`, borrowed trait objects and arrays of any of them hold borrows, so they don't meet `T: noref`:

```cella error
~ mod example
~
keep[T: noref]: fun(own value: T) -> T => value

main: fun
{
	val word: str = "hi"
	val kept = keep(word)
}
```

```errors
'keep' requires 'T: noref'
```

`cstr` and pointers hold no borrows: nothing is checked through them. [Borrows](borrows.md) explains what holding a borrow means.

## Built-in names

None of these type names can be used to declare anything else, as [Keywords](keywords.md) shows.
