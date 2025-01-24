## Release Schedule

### Major and Minor Releases
A Major/Minor release will regularly be released around the 1st of each month. In rare circumstances, a release *may* be skipped if there was nothing done in the month to justify one.
The difference between a major and a minor release, is that a major release contains some considerable big change. For example a new stable game or a big overhaul in some existing system.

### Patch Releases
Patch releases have no restrictions on how often they are released or how many there are.
However, all patch releases in a given X.Y series will always generate the same game given a specific permalink. This effectively means, that patch releases cannot contain any logic changes.

## Releasing for developers
During the whole month, ping beta-testers if there is a feature that should get tested. Do not feel the need to wait until feature freeze.

Creating a major/minor release:
- Ping contributors approximately 1.5 weeks before the 1st of next month. Mention that all Pull Requests should be open 2 days before feature freeze, to still give time for review.
- Make sure stuff we want in is merged and that the changelog is correct and up to date.
- Enter feature freeze approximately 1 week before the 1st of next month and ping beta testers for some testing.
- Hold off merging anything important for now (alternatively we could use a branch).
- Fix things as needed.
- Make `stable` be the commit we're releasing (99% of the time, current main) on the 1st of the month.
- Check the CI works for stable (it's 1% different and likes to fail sometimes). Download a build and do some small testing just to make sure it works.
- Make a (signed) tag, push and wait for CI. This will automatically create a new release.
- Copy-paste the changelog from CHANGELOG.md into the GH Release created by CI.
- Website gets automatically updated. For Flathub, [merge the PR](https://github.com/flathub/io.github.randovania.Randovania/pulls) that will get automatically created.

Creating a patch release:
- Get the fixes to the `stable` branch however you want (commit directly, cherry pick).
- Make sure the changelog is correct.
- Check the build is working
- Make a (signed) tag, push and wait for CI. This will automatically create a new release.
- Copy-paste the changelog from CHANGELOG.md into the GH Release created by CI.
- Website gets automatically updated. For Flathub, [merge the PR](https://github.com/flathub/io.github.randovania.Randovania/pulls) that will get automatically created.
- Make a PR that merges stable into main.

Some other miscellaneous notes:
- The server version always has to be in sync with the client version. For this reason, **never** delete releases, nor keep releases in the pre-release state for longer than they're needed. If you want to delete a release, make a new release that reverts the changes.
- Even if the feature freeze for a major/minor releases is late, the 1st is always when we release (unless of course we decided to skip the release).
