# Testing

Randovania uses [pytest](https://docs.pytest.org/) for its automated tests. Every test lives under the `test/` folder, which mirrors the layout of the `randovania/` folder it tests.

Opening a pull request runs the entire test suite using GitHub Actions. **These tests must pass before your pull request can be merged.** You can see the result at the bottom of your pull request page. Click through to the failing job to read its log.

## Running Tests

Follow the "In order to run the tests" steps in the [README](../README.md), then run:

```sh
uv run pytest -n auto
```

The full suite is large, so most of the time you only want the part you are working on. Pass a folder or a file:

```sh
uv run pytest test/games/prime2
uv run pytest test/games/prime2/patcher/test_patch_data_generator.py
```

PyCharm and Visual Studio Code can both run tests directly from the editor, which is usually more convenient than the command line.

## Writing Tests

When you run pytest, it first *collects* the tests it is going to run:

- It looks for files named `test_<something>.py`.
- Inside those files, it looks for functions named `def test_something()`.

pytest then calls each of those functions. A test passes if the function returns without raising an error, and fails if it raises one. You check things with Python's built-in `assert`:

```py
def test_addition():
    assert 1 + 1 == 2
```

### Parameters

When the same test should run several times with different values, use `parametrize` instead of copying the function. The name in the decorator becomes an argument of the function:

```py
@pytest.mark.parametrize("has_output_dir", [False, True])
def test_export(has_output_dir):
    ...
```

This counts as two separate tests, so one can fail while the other passes.

### Fixtures

If a test function has an argument that is *not* one of its parameters, pytest treats the name as a *fixture*: a function decorated with `@pytest.fixture` that gets called to produce the value.

```py
@pytest.fixture
def echoes_game_description():
    return default_database.game_description_for(RandovaniaGame.METROID_PRIME_ECHOES)


def test_something(echoes_game_description):
    assert echoes_game_description.game.long_name == "Metroid Prime 2: Echoes"
```

Fixtures exist so that setup code is written once and shared. A fixture placed in a file named `conftest.py` is available to every test in that folder and below it. Most of Randovania's shared fixtures are in `test/conftest.py`.

Two fixtures worth knowing about:

- `mocker`, from [pytest-mock](https://pypi.org/project/pytest-mock/), replaces a function with a fake one, so it returns whatever you want instead of doing its real work. You can then check whether it was called.
- `skip_qtbot` should be present in any test that touches Qt (that is, the graphical interface).

## Acceptance Tests

Some parts of Randovania produce a large result: exporting a game, for example, produces a JSON file with thousands of fields. Asserting on those fields one at a time would be unreadable and nobody would keep it up to date.

Instead, the expected result is stored as a git-tracked reference file in the repository under `test/test_files/`. The test runs the code, then asserts that the result still equals the contents of the reference file.

The comparison is done by the `acceptance_check` fixture, which takes the path of the committed file and the value that should equal it:

```py
def test_create_pickups_dict(test_files_dir, acceptance_check):
    pickups_dict = ...

    acceptance_check(test_files_dir.joinpath("patcher_data", "fusion", "pickups.json"), pickups_dict)
```

The point of these tests is that they fail whenever your change alters the output of the exporter. That failure is not automatically a bug: often the new output is exactly what you intended. It just means the committed files need to be brought up to date, and that you should read the resulting diff to confirm that only what you meant to change actually changed.

### Updating the committed files

Do not edit those files by hand. Instead, run:

```sh
uv run randovania development update-acceptance-tests
```

This regenerates everything in the repository that Randovania itself generates:

- The logic databases, in both the JSON format and human readable text version
- The pickup databases
- Every acceptance test reference file. Think of this action as "accepting" the consequences of a change.

### Adding a new acceptance test

1. Write the test as usual, taking the `acceptance_check` fixture as an argument.
2. Call `acceptance_check(path, value)`, choosing a path inside `test/test_files/`. The file does not have to exist yet.
3. Run `uv run randovania development update-acceptance-tests` to create it, then commit it along with your test.

Note that `acceptance_check` accepts `dict`/`list` which gets stored as JSON, or `bytes` which is stored as-is.
