import dataclasses
from pathlib import Path

from randovania.gui.item_tracker.tracker_structure import TrackerStructure
from randovania.gui.item_tracker.tracker_theme import TrackerTheme


@dataclasses.dataclass(frozen=True)
class TrackerAssetPaths:
    """
    Points at a TrackerStructure file and a TrackerTheme file meant to be used together, plus
    the directory the theme's image paths are relative to.
    """

    structure: Path
    theme: Path
    assets_root: Path

    def load(self) -> tuple[TrackerStructure, TrackerTheme]:
        structure = TrackerStructure.read_json(self.structure)
        theme = TrackerTheme.read_json(self.theme)
        theme.validate_against(structure)
        return structure, theme


@dataclasses.dataclass(frozen=True)
class ThemeSource:
    """A theme file plus the directory its image paths are relative to."""

    path: Path
    assets_root: Path


@dataclasses.dataclass(frozen=True)
class TrackerCatalog:
    """
    Everything available for one game:
    - a set of named layouts (structures)
    - a set of named themes.
    """

    layouts: dict[str, Path]
    themes: dict[str, ThemeSource]

    def resolve(self, layout_name: str, theme_name: str) -> TrackerAssetPaths:
        source = self.themes[theme_name]
        return TrackerAssetPaths(structure=self.layouts[layout_name], theme=source.path, assets_root=source.assets_root)

    def as_named_combos(self) -> dict[str, TrackerAssetPaths]:
        """Flatten every (layout, theme) pair into a single "Theme (Layout)" name.

        Used by consumers that only care about a flat list of ready-to-use trackers,
        not about picking layout and theme independently.
        """
        single_layout = len(self.layouts) == 1
        result: dict[str, TrackerAssetPaths] = {}
        for layout_name in self.layouts:
            for theme_name in self.themes:
                name = theme_name if single_layout else f"{theme_name} ({layout_name})"
                result[name] = self.resolve(layout_name, theme_name)
        return result
