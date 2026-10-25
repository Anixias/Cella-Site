# Keywords

Cella has two kinds of keywords. Reserved keywords mean the same thing everywhere and can never be used as names. Contextual keywords have a meaning only in certain places, such as at the start of a declaration, and are ordinary names everywhere else.

## Reserved keywords

A reserved keyword can't name a variable, parameter, function, type, field or case:

```cella error
~ mod example
~
main: fun
{
	val match = 3
}
```

```errors
'match' is a keyword
```

### Values

| Keyword | Meaning | Chapter |
| --- | --- | --- |
| `true`, `false` | The two `bool` values. | [Bool, char and strings](text.md) |
| `null` | The null pointer, for `ptr`, `ptr[T]` and `cstr`; `T: null` constrains a type parameter. | [Pointers](pointers.md#null), [Generics](generics.md#null) |
| `undef` | A value left uninitialized on purpose: `var buffer: array[u8, 64] = undef`. | [Variables](variables.md#undef) |
| `sizeOf` | The size of a type or value in bytes, as a `usize`. | [Pointers](pointers.md#sizeof-and-alignof) |
| `alignOf` | The alignment of a type or value in bytes, as a `usize`. | [Pointers](pointers.md#sizeof-and-alignof) |
| `nameOf` | The name of a declaration as a string: `nameOf(Point)`. | [Bool, char and strings](text.md#nameof) |
| `self` | The value a method was called on. | [Methods](methods.md) |

### Declarations and bindings

| Keyword | Meaning | Chapter |
| --- | --- | --- |
| `fun` | Declares a function (`area: fun(...)`), starts a lambda (`fun(x) => x * 2`) and names function types (`fun[i32 -> i32]`). | [Functions](functions.md), [Closures](closures.md) |
| `val` | Declares a binding that can't be reassigned; also a read-only static field and a pattern binding. | [Variables](variables.md) |
| `var` | Declares a binding that can be reassigned; also a writable static field and a pattern binding. | [Variables](variables.md) |
| `const` | Declares a compile-time constant; also marks constant functions (`const fun`, `const op`), constant accessors (`const get`, `const set`, `const prop`), value parameters (`const length: usize`), constant implementations (`impl const Hash`) and constant bounds (`T: const Hash`). | [Variables](variables.md), [Constant functions](constant-functions.md), [Generics](generics.md) |
| `new` | Names constructors (`new: op(...)`) and explicit conversions (`new: op(self) -> T`); `T: new(...)` constrains a type parameter. | [Records](records.md), [Conversions](conversions.md) |
| `drop` | Names destructors (`drop: op`), destroys a value early (`drop x`, `drop *p`); `T: drop` constrains a type parameter. | [Ownership](ownership.md) |
| `default` | Restores zeroed construction (`new: op() = default`); `T: default` constrains a type parameter. | [Records](records.md), [Generics](generics.md) |
| `ref` | Declares a record that holds borrows (`ref rec`) and names function types that may borrow (`ref fun[...]`). | [Borrows](borrows.md), [Closures](closures.md) |

### Control flow

| Keyword | Meaning | Chapter |
| --- | --- | --- |
| `if`, `else` | Conditional statements; `else if` chains them. | [Control flow](control-flow.md) |
| `while` | Loops while a condition holds. | [Control flow](control-flow.md) |
| `do` | Runs a body once before checking its `while` condition. | [Control flow](control-flow.md) |
| `loop` | Loops until a `break`. | [Control flow](control-flow.md) |
| `for` | Loops over a range, an array or a type with loop operators; `for: op` declares a loop operator. | [Control flow](control-flow.md), [Operators](operators.md) |
| `in` | Separates a `for` loop's variable from what it walks; `in: op` declares a loop operator. | [Control flow](control-flow.md), [Operators](operators.md) |
| `break` | Leaves a loop, optionally a labeled one. | [Control flow](control-flow.md) |
| `cont` | Starts a loop's next iteration, optionally a labeled one. | [Control flow](control-flow.md) |
| `ret` | Returns from a function, with or without a value. | [Functions](functions.md) |
| `match` | Picks an arm by matching a value against patterns. | [Pattern matching](pattern-matching.md) |
| `is` | Tests a value against a pattern: `shape is circle(_)`. | [Pattern matching](pattern-matching.md#the-is-operator) |
| `when` | Compiles code only when a flag condition holds. | [Conditional compilation](conditional-compilation.md) |
| `panic` | Stops the program with a message: `panic "bad index"`; `panic: op` declares a module's panic operator. | [Checks and panics](panics.md#panicking-on-purpose) |

### Modes and memory

| Keyword | Meaning | Chapter |
| --- | --- | --- |
| `imm` | Borrows without writing: `imm` parameters and arguments, `imm[T]` borrow types, `for imm x in xs`. | [Parameter modes](parameter-modes.md), [Borrows](borrows.md) |
| `mut` | Borrows for writing: `mut` parameters and arguments, `mut[T]` borrow types, `for mut x in xs`, `match mut`. | [Parameter modes](parameter-modes.md), [Borrows](borrows.md) |
| `own` | Moves a value where a plain use wouldn't (`own *p`, `own slot` out of a `mut` parameter, `own self.field`), and declares types whose values only move (`own rec`, `own enum`) and closures that own their captures (`own fun`). | [Ownership](ownership.md), [Pointers](pointers.md) |
| `dyn` | Names trait object types: `dyn[Shape]`. | [Trait objects](trait-objects.md) |
| `atomic` | Starts an atomic load, store, update or fence; `T: atomic` constrains a type parameter. | [Atomics](atomics.md) |

## Contextual keywords

These words are keywords only where the grammar expects them. Anywhere else they are ordinary names:

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
	val set = 3
	val copy = set * 2
	printf("%d %d\n", set, copy)
}
```

```output
3 6
```

| Keyword | Meaning | Chapter |
| --- | --- | --- |
| `mod` | Starts a file's `mod` line, makes a declaration visible to its module only, and starts a path from the root module (`mod.geometry.area`). | [Modules](modules.md) |
| `use` | Imports names from other modules; `use when` compiles a whole file only when a flag condition holds. | [Modules](modules.md), [Conditional compilation](conditional-compilation.md) |
| `pub` | Exports a declaration from its project. | [Modules](modules.md) |
| `pvt` | Makes a declaration visible to its file, or a member visible to its type. | [Modules](modules.md), [Methods](methods.md) |
| `ext` | Declares C functions and globals (`ext { }`), C function types (`ext fun[...]`), C-compatible enums (`ext enum`), C names (`ext("name")`); `T: ext` constrains a type parameter. | [Calling C](calling-c.md) |
| `rec` | Declares a record type. | [Records](records.md) |
| `enum` | Declares an enum type; `T: enum` and `T: enum(Tag)` constrain a type parameter. | [Enums](enums.md), [Generics](generics.md#enum) |
| `union` | Declares a union type. | [Unions](unions.md) |
| `trait` | Declares a trait; `K: trait` makes a parameter that takes a trait. | [Traits](traits.md), [Trait objects](trait-objects.md) |
| `impl` | Implements traits for a type (`rec impl Shape`, `Circle: impl Shape`) and adds members in `impl` blocks. | [Traits](traits.md) |
| `op` | Declares operators, constructors, destructors and conversions: `+: op(...)`, `new: op(...)`, `drop: op`. | [Operators](operators.md) |
| `as` | Declares an implicit conversion: `as: op(self) -> T`. | [Conversions](conversions.md) |
| `req` | Marks fields that every construction must set, and lists the traits and constraints a trait requires (`Shape: trait req Named`). | [Records](records.md), [Traits](traits.md) |
| `prop` | Declares a property with `get` and `set` accessors. | [Methods](methods.md#properties) |
| `get`, `set` | Declare property accessors; `pvt set` and `mod set` limit who can write a field. | [Methods](methods.md) |
| `copy` | Constrains a type parameter to types that can be copied: `T: copy`. | [Generics](generics.md) |
| `noref` | Constrains a type parameter to types that hold no borrows: `T: noref`. | [Generics](generics.md) |

## Memory orderings

After `atomic`, the words `relaxed`, `acquire` and `release`, and the pair `acquire release`, choose the memory ordering. Without one, the operation is sequentially consistent. Anywhere else these words are ordinary names:

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
	var counter = 0
	atomic relaxed *@counter += 5
	val release = atomic acquire *@counter
	printf("%d\n", release)
}
```

```output
5
```

[Atomics](atomics.md) explains what each ordering guarantees.

## Built-in names

The names of the built-in types (`i32`, `str`, `ptr`, `array` and the rest, listed in [Built-in types](builtin-types.md)) and `Self` aren't keywords, but nothing can be declared with them:

```cella error
~ mod example
~
main: fun
{
	val str = 5
}
```

```errors
Cannot use 'str' as a name
```
