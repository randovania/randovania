from __future__ import annotations

from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration
from randovania.gui.preset_settings.dock_rando_tab import PresetDockRando
from randovania.layout.base.dock_rando_configuration import DockRandoMode


class PresetEchoesDockRando(PresetDockRando):
    def _on_mode_changed(self, value: DockRandoMode):
        super()._on_mode_changed(value)
        if value != DockRandoMode.VANILLA:
            with self._editor as editor:
                assert isinstance(editor.configuration, EchoesConfiguration)
                editor.set_configuration_field("use_new_patcher", True)
