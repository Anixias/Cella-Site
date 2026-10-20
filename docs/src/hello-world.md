# Hello, World

## Installing Cella

Cella installs a small launcher named `cella`, which manages compiler versions and runs the right one for each project. On Windows, run this in PowerShell:

```powershell
irm https://anixias.github.io/Cella/install.ps1 | iex
```

On Linux:

```sh
curl -fsSL https://anixias.github.io/Cella/install.sh | sh
```

The installer puts everything in `C:\cella` or `~/.cella`, or in `CELLA_HOME` if it's set, and adds `cella` to your path.

Windows programs link with Visual Studio's C++ build tools and the Windows SDK when they're installed, and with MinGW-w64 otherwise. Linux programs need glibc 2.34 or later.

## A first program

`cella new` creates a project:

```sh
cella new hello
```

This makes a `hello` folder with two files. `hello.celp` describes the project, and `main.ce` holds the program:

```cella file=main.ce
mod hello

ext
{
	puts: fun(text: cstr) -> i32
}

main: fun -> i32
{
	puts("Hello, World!")
	ret 0
}
```

```output
Hello, World!
```

`cella run` builds the program and runs it:

```sh
cd hello
cella run
```

## What the program says

`mod hello` names the module this file belongs to. Every source file starts with a `mod` line, and any number of files can belong to one module.

The `ext` block declares `puts`, a function from the C library. Cella has no built-in way to print; programs call C functions, or a library that wraps them. `cstr` is a pointer to a zero-terminated string, which is what C expects, and a string literal converts to one.

`main: fun -> i32` declares the function the program starts in. Every declaration has this shape: a name, a colon, then what the name is. `fun` makes it a function, and `-> i32` says it returns a 32-bit integer, which becomes the program's exit code.

The body is a block of statements, one per line. Calls look as they do in C, and `ret` returns a value. No semicolons are needed: a new line ends a statement.

`main` doesn't have to return anything. Without a return type, the program exits with code 0:

```cella
mod hello

ext
{
	puts: fun(text: cstr) -> i32
}

main: fun
{
	puts("Hello again!")
}
```

```output
Hello again!
```

## Printing values

`printf` comes from C too. Its declaration ends in `...`, so it takes any number of extra arguments after the format string, and they follow C's rules for variadic calls ([Variadic functions](variadics.md) covers them). `val` declares a named value, covered in [Variables and constants](variables.md):

```cella
mod hello

ext
{
	printf: fun(format: cstr, ...) -> i32
}

main: fun
{
	val year = 2026
	val pi = 3.14159
	printf("%d %.2f\n", year, pi)
}
```

```output
2026 3.14
```

The rest of the documentation prints with `printf`. Examples leave out its `ext` block to stay short, but the copy button copies it along with the rest of the program.

