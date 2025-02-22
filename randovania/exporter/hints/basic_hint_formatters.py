from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from randovania.exporter.hints.hint_formatters import FeaturalFormatter, RelativeAreaFormatter, TemplatedFormatter
from randovania.exporter.hints.relative_item_formatter import RelativeItemFormatter
from randovania.game_description.hint import HintLocationPrecision

if TYPE_CHECKING:
    from collections.abc import Callable

    from randovania.exporter.hints.hint_formatters import LocationFormatter
    from randovania.exporter.hints.hint_namer import HintNamer
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.hint_features import HintFeature
    from randovania.interface_common.players_configuration import PlayersConfiguration


def basic_hint_formatters(
    namer: HintNamer,
    location_hint_template: str,
    patches: GamePatches,
    distance_painter: Callable[[str, bool], str],
    players_config: PlayersConfiguration,
    featural_hint_template: str | None = None,
    with_region: bool = True,
    upper_pickup: bool = False,
) -> dict[HintLocationPrecision | HintFeature, LocationFormatter]:
    """Returns a standard set of hint formatters useful as a baseline for most games."""

    if featural_hint_template is None:
        featural_hint_template = "{determiner.title}{pickup} can be found {node}."
    basic_formatter = TemplatedFormatter(location_hint_template, namer, with_region, upper_pickup)
    feature_formatter = FeaturalFormatter(featural_hint_template, namer, upper_pickup)

    location_formatters: dict[HintLocationPrecision | HintFeature, LocationFormatter] = defaultdict(
        lambda: feature_formatter
    )
    location_formatters.update(
        {
            HintLocationPrecision.DETAILED: basic_formatter,
            HintLocationPrecision.REGION_ONLY: basic_formatter,
            HintLocationPrecision.RELATIVE_TO_AREA: RelativeAreaFormatter(patches, distance_painter),
            HintLocationPrecision.RELATIVE_TO_INDEX: RelativeItemFormatter(
                patches,
                distance_painter,
                players_config,
            ),
        }
    )
    return location_formatters
