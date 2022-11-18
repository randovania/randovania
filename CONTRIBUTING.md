## How to write a good pull request

- Describe your motivation for your proposed changes
- Describe in detail what you changed
- Describe how you tested the changes
- Describe any follow-up work that is related but outstanding and describe any concerns you might have about your proposed changes

## Target branch

Pull requests should target the `main` branch. If the change is relevant for a hotfix release, make a note in the PR description,
so it can be cherry-picked after merge.

## Adding to CHANGELOG

Changelog entries are to be written within the scope of a specific upcoming release.
In practice, changelog entries should always go under the unreleased section (the first one) of [CHANGELOG.md](CHANGELOG.md).
As such, changelog entries and the specific language used in them must be with respect to the previous release.

If a feature changes multiple times in development, the existing entry should be edited rather than appended if it is still unreleased at the time of writing.

### Example of changes that should have changelog:

- Any database change for a stable game
- Any GUI change (that isn't hidden by `preview mode` or belongs to an experimental game).
- Changes to multiworld, presets, generator or solver that causes visible changes in the result
- Patcher changes affecting gameplay
- Bugfixes and other stability/performance improvements

### Example of changes that should _not_ have a changelog:

- Changes to experimental games
- Anything only visible when running from source
- Code refactoring
- Dependency changes (except for patcher dependencies, since these can change the results!)

## How to write a good Changelog Entry

- Use the full name of areas
- Mention all new tricks/difficulty pair and in which areas.
- It should be discernable which areas are affected when reading the Changelog alone.
It is acceptable if users need to open the Data Visualizer to understand the exact details of what changed in those areas, however.

## Need some help?

Join the [Randovania Discord](https://discord.gg/M23gCxj6fw), grab the `@Dev Chat` role in `#roles` and chat with us in the `dev-talk` channels.

We're always happy to help new people with their changes, be it pointing where to change things, brainstorming how something should be, or anything else!