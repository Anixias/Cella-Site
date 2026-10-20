# Cella Documentation

Cella is a systems programming language. It works at the level of C: raw pointers, no garbage collector and no runtime. On top of that it adds ownership and destructors, borrowed parameters, enums with payloads, generics, traits and modules. The compiler generates code with LLVM and builds executables and libraries for 64-bit Windows and Linux.

This documentation covers the language itself: its syntax, its types and the rules the compiler checks. The standard library is documented separately.

```cella
mod greeting

ext
{
	printf: fun(format: cstr, ...) -> i32
}

Shape: enum
{
	circle(radius: f64)
	rect(width: f64, height: f64)
}

area: fun(shape: Shape) -> f64 => match shape
{
	circle(val r) => 3.14159 * r * r
	rect(val w, val h) => w * h
}

main: fun
{
	val shapes = [Shape.circle(1.0), Shape.rect(2.0, 3.0), Shape.rect(0.5, 4.0)]
	var total = 0.0
	for shape in shapes
	{
		total += area(shape)
	}

	printf("total area %.2f\n", total)
}
```

```output
total area 11.14
```

## How the documentation is organized

The chapters build on each other, so reading them in order works best.

- **Getting started** installs Cella and builds a first program.
- **Basics** covers the pieces every program uses: literals, numbers, strings, variables, functions and control flow.
- **Data** covers arrays, records, enums, unions and pattern matching.
- **Memory** explains ownership, destructors, parameter modes, borrows and raw pointers.
- **Abstraction** covers generics, traits, operators, conversions and closures.
- **Programs** covers modules, conditional compilation, calling C, checks and atomics.
- **Reference** lists keywords, operators, built-in types and project settings.

## Examples

Every example in this documentation is compiled and run with the current compiler, and the output shown under it is what the program printed. Examples that the compiler rejects show its errors under the lines they point to.

The examples print through C's `printf`, declared in an `ext` block as above. Most examples leave that declaration out to stay short; the copy button on each example copies the whole program, declaration included.

> Cella is still changing and hasn't had a release yet. This documentation follows the compiler as it is today.
