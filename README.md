# pymly - Python-augmented YAML Templates

`pymly` is a simple framework for mix-and-matching YAML and Python files as `pyml` files. A `pyml` is a regular YAML file, but containing easily user-readable Python code snippets, that are executed **within the context of the file**, i.e. using the YAML context as their Python "`globals`". (*)

Since the Python code is executed within the context, it can be used to generate or process the YAML objects within the same file as the original structure, but can also be used to generate completely new files based on some predefined structures and rules.

(\*) `pymly` can currently only execute the Python statements *after* processing the file and only at the top level of the YAML. We consider running within *local* context as wanted, but not yet implemented.

## `pyml` syntax
Since the `pyml` files must be legal YAML files, the regular YAML rules apply. Internally we use [PyYAML](https://pyyaml.org/) as loader, with  `CLoader` as the default loader.

Python statements are lines that start with `#!>` and can be continued in lines starting with `#!.`.

```yaml
# This is a regular yaml object:
foo:
    - bar
    - baz
#!> # This is a Python statement
#!. def foo2(x):
#!.     print(x[0])

# The following is another Python statement
#!> foo2(foo)
```

Currently you can insert gaps between the statement and continuation lines, but this may break line numbering as the Python parser/compiler assume the lines are in a contiguous block, i.e.:

```
$ cat test.pyml
#!> # In this file all Python statements are folded into a single block
foo:
    - bar
    - baz
#!. def foo2(x):
#!.     print(x[0])
# And now for a syntax error:
#!. foo3 = 3 + %;

$ python3 -m pymly test.pyml
Traceback (most recent call last):
  File "/usr/lib/python3.10/runpy.py", line 196, in _run_module_as_main
    return _run_code(code, main_globals, None,
  ...
  File "/usr/lib/python3.10/ast.py", line 50, in parse
    return compile(source, filename, mode, flags,
  File "test.pyml", line 4
    - baz
         ^
SyntaxError: invalid syntax
```

`pymly` can otherwise follow line numbers, as long as there are no gaps before continuation (`#!.`) lines:

```
$ cat test.pyml
# In this file all Python statements properly separated
foo:
    - bar
    - baz
#!> def foo2(x):
#!.     print(x[0])
# And now for a syntax error:
#!> foo3 = 3 + %;

$ python3 -m pymly test.pyml
Traceback (most recent call last):
  File "/usr/lib/python3.10/runpy.py", line 196, in _run_module_as_main
    return _run_code(code, main_globals, None,
  ...
  File "/usr/lib/python3.10/ast.py", line 50, in parse
    return compile(source, filename, mode, flags,
  File "est.pyml", line 8
    foo3 = 3 + %;
               ^
SyntaxError: invalid syntax
```

As you can see, the syntax is *super* easy and also *super* powerful.

## Using `pyml`/`pymly`
There are two primary use-cases for `pyml` and `pymly`:
* As a module
* As a script runner

When used as a module we assume a case where the `pyml` file is to be processed like a normal YAML file, returning the parsed object. There are two main functions for this: `process_stream` and `process_file`:

```python
def process_stream(f: FileLike | Buffer | str,
                   g: Optional[Dict[str, Any]] = None,
                   *,
                   encoding: Optional[str],
                   Loader = yaml.CLoader,
                   verbose: bool = False):
    ...

def process_file(name: str,
                 g: Optional[Dict[str, Any]] = None,
                 **...):
    ...
```

The only differences between the functions is that `process_stream` works on raw `Readable` objects (like an opened `file`, `sys.stdin`, etc.), strings or `bytes`-like objects (`bytearray`, `memoryview`), while `process_file` opens the file first and populates the `__file__` global s.t. i.a. Python traceback can properly report file locations.

In both interfaces `g` is the optional initial global state (before even processing the YAML part) which is then expanded with the YAML, and in which the latter Python execution takes place. It can be used to pre-inject code, or to control configuration, e.g.:

```python
g = {'extract_foo': True, 'extract_bar': False}
process_stream("""
some_yaml:
    foo: The quick brown fox
    bar: 99 bottles of beer on the wall

#!> if extract_foo: print(some_yaml['foo'])
#!> if extract_bar: print(some_yaml['bar'])
""", g)
```
Yields:
```
The quick brown fox
g == {'extract_foo': True, 'extract_bar': False, 'some_yaml': ...}
```

You may notice, however, that the resulting yaml has become extremely polluted with Python builtins, e.g.:
```python
>>> print(g)
{'extract_foo': True, 'extract_bar': False, 'some_yaml': {'foo': 'The quick brown fox', 'bar': '99 bottles of beer on the wall'}, '__builtins__': {'__name__': 'builtins', '__doc__': "Built-in functions, exceptions, and other objects.\n\nNoteworthy: None is the `nil' object; Ellipsis represents `...' in slices.", '__package__': '', '__loader__': <class '_frozen_importlib.BuiltinImporter'>, ...
```

This is an unfortunate consequence of using it as the global context and we might consider changing it in the future.

`encoding` parameter is only ever used when the input source is `bytes`-like, or a file opened as binary, or as the `encoding` parameter to `open(...)` when using the `process_file` interface.

`Loader` is equivalent to `yaml.load(x, Loader=...)` argument, see [PyYAML documentation](https://pyyaml.org/wiki/PyYAMLDocumentation).

`verbose`, when set to `True`, will cause the parser to print every Python statement before execution. This can be helpful in debugging raw string inputs, where line info is less helpful.

---

When used as a script runner, `pymly` will read the provided file (or `sys.stdin` if no file or '`-`' was provided) and execute an appropriate `process_*` function, ignoring the output.

### Inserted globals:
The `process_*` functions will insert the following global symbols before processing the Python inserts, but will also remove them before returning the parsed object to the caller:

* `__root__` - points to the top-level YAML object within the file.
* `__file__` (`process_file` only) - contains the first `process_file` argument, i.e. the name of the processed file.


## Known limitations
1.  `pymly` can currently only execute the Python statements *after* processing the file and only at the top level of the YAML. We consider running within *local* context as wanted, but not yet implemented.
2.  `pymly` can handle `!!python/` syntax as part of the `PyYAML` loader, but will not explicitly interact with objects created this way. All `pymly` execution takes place **after** the YAML has been parsed and so the following will not work (yet):
    ```yml
    #!> class Dog:
    #!.     def __init__(self, name):
    #!.         self.name = name
    !!python/object:__main__.Dog
    name: Danny
    ```
3. Some `pymly`-provided utilities (`deep_split`, `deep_format`) will only work on simple JSON-like structure types, i.e. `dict`, `list`, `str` and will lump numbers with other, potentially more complex types. As a consequence, they don't work e.g. on sets, even though sets can be created with `!!set`
4. `pymly` by default assumes the top-level YAML object is a `dict`. There is a fallback logic for a `list` in which case the it is converted to a `dict` using element numbers as keys (via `dict(enumerate(g))`). An empty output (null) is also supported and falls back to an empty `dict`(`{}`). No other support is currently planned.
