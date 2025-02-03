# Featural Hints
The featural hint system gives designers a high degree of freedom when it comes to designing and balancing hints for their game, while being easy to implement.

## Assigning Hint Features
### Locations
Locations can be assigned Features in the database editor. There are two ways to assign Features: to `Area`s, and to `PickupNode`s.

Most of the time, you'll want to assign to `Area`s. `Area` Features are automatically applied to all `PickupNode`s they contain.

`PickupNode` features are useful when an `Area` has multiple `PickupNode`s, but they don't all have the same Features. For instance, perhaps you have a Feature for "submerged in water", but only one of the two `PickupNode`s in an `Area` is underwater.

### Pickups
Pickups can be assigned Features by editing `pickup-database.json`.

## Balancing your Features
### Adjusting the precision distributions
Each Feature has a "precision" - a semi-arbitrary percentage measurement of how much information a particular Feature gives you. A precision of 1.0 means it can only be a single pickup or location, and a precision of 0.0 means it could be any of them.

Features are chosen according to a Gaussian random variable, where the Feature with the closest precision to the Gaussian random variable is assigned to the hint. The distribution can be adjusted by changing the results of `location_feature_distribution()` and `item_feature_distribution()` in your subclass of `HintDistributor`.

If you're unfamiliar with Gaussian distributions, they're fairly straightforward: the *mean* determines how precise your hints will be, on average. The *standard deviation* determines how far away from the average any given hint is likely to be, in either direction.

### Selecting appropriate Features
Ultimately, it's up to you what you want your Features to be. That said, we do have a way to gather some useful information about your features.

When running Randovania in debug mode (e.g. via `tools/start_debug_client`), there's some detailed debug output about Features during hint placement. A full list of each valid Feature's precision, as well as information about how accurately the Gaussian distribution is choosing precisions.

There's also the CLI command: `python -m randovania database features-per-node`. This provides some information about the distribution of Features across your `PickupNode`s.
