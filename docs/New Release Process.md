For Major/Minor releases:
- Ping contributors approximately 1.5 weeks before the 1st of next month
- Make sure stuff we want in is merged
- Make sure the changelog is correct and up to date
- Enter feature freeze approximately 1 week before the 1st of next month and ping beta testers for some testing
- Hold off merging anything important for now (alternatively we could use a branch)
- Fix things as needed
- Make `stable` be the commit we're releasing (99% of the time, current main)
- Check the CI works for stable (it's 1% different and likes to fail sometimes)
- Make (signed) tag, push. wait for CI
- Copy paste from changelog into notes in the GH Release
- Website gets automatically updated. For Flathub, [merge the PR](https://github.com/flathub/io.github.randovania.Randovania/pulls) that will get automatically created

For Patch releases:
- Get the fixes to the `stable` branch however you want (commit directly, cherry pick)
- Make sure the changelog is correct
- Check the build is working
- Make a (signed) tag, push. wait for CI
- Copy paste from changelog into notes in the GH Release
- Website gets automatically updated. For Flathub, [merge the PR](https://github.com/flathub/io.github.randovania.Randovania/pulls) that will get automatically created
- Merge stable into main
