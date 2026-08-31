from __future__ import annotations

import pytest

from randovania.gui.item_tracker.tracker_structure import LabelTrackerElement, TrackerStructure
from randovania.gui.item_tracker.tracker_theme import DEFAULT_LABELS, TrackerTheme


def _label_element(name: str, resources: list[str], text: str | None = None) -> LabelTrackerElement:
    return LabelTrackerElement.model_validate(
        {
            "name": name,
            "row": 0,
            "column": 0,
            "resources": resources,
            "kind": "label",
            "text": text,
        }
    )


def _label_structure(resources: list[str]) -> TrackerStructure:
    return TrackerStructure.model_validate(
        {
            "game": "prime2",
            "elements": [
                {
                    "name": "Capacity with Maximum",
                    "row": 0,
                    "column": 0,
                    "resources": resources,
                    "kind": "label",
                }
            ],
        }
    )


def test_label_for_uses_default_when_theme_has_no_entry():
    theme = TrackerTheme.model_validate({})
    element = _label_element("Capacity with Maximum", ["Dark Agon Key 1"])

    label = theme.label_for(element)

    assert label == DEFAULT_LABELS["Capacity with Maximum"]


def test_label_for_prefers_theme_entry_over_default():
    theme = TrackerTheme.model_validate(
        {"labels": {"Capacity with Maximum": {"text": "{capacity}", "style": "font:18pt;"}}}
    )
    element = _label_element("Capacity with Maximum", ["Dark Agon Key 1"])

    label = theme.label_for(element)

    assert label.text == "{capacity}"
    assert label.style == "font:18pt;"


def test_label_for_prefers_embedded_text_over_theme_and_default():
    theme = TrackerTheme.model_validate({"labels": {"Object Count": {"text": "should not be used"}}})
    element = _label_element("Object Count", ["Object Count"], text="x {amount}/{capacity} objects")

    label = theme.label_for(element)

    assert label.text == "x {amount}/{capacity} objects"
    assert label.style is None


def test_label_for_raises_for_unknown_name():
    theme = TrackerTheme.model_validate({})
    element = _label_element("Not A Real Label", ["Missile"])

    with pytest.raises(KeyError):
        theme.label_for(element)


def test_validate_against_accepts_default_label_with_no_theme_entry():
    theme = TrackerTheme.model_validate({})
    structure = _label_structure(["Dark Agon Key 1", "Dark Agon Key 2", "Dark Agon Key 3"])

    theme.validate_against(structure)  # does not raise


def test_validate_against_accepts_embedded_label_with_no_theme_entry():
    theme = TrackerTheme.model_validate({})
    structure = TrackerStructure.model_validate(
        {
            "game": "prime2",
            "elements": [
                {
                    "name": "Object Count",
                    "row": 0,
                    "column": 0,
                    "resources": ["Object Count"],
                    "kind": "label",
                    "text": "x {amount}/{capacity} objects",
                }
            ],
        }
    )

    theme.validate_against(structure)  # does not raise


def test_validate_against_rejects_unknown_label_name():
    theme = TrackerTheme.model_validate({})
    structure = TrackerStructure.model_validate(
        {
            "game": "prime2",
            "elements": [
                {
                    "name": "Some Custom Label",
                    "row": 0,
                    "column": 0,
                    "resources": ["Missile"],
                    "kind": "label",
                }
            ],
        }
    )

    with pytest.raises(ValueError, match="Some Custom Label"):
        theme.validate_against(structure)
