from typing import Optional

from randovania.interface_common import echoes
from randovania.interface_common.options import Options
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.permalink import Permalink
from randovania.lib.status_update_lib import ProgressUpdateCallable, ConstantPercentageCallback

export_busy = False


def generate_layout(options: Options,
                    permalink: Permalink,
                    progress_update: ProgressUpdateCallable,
                    retries: Optional[int] = None,
                    ) -> LayoutDescription:
    """
    Creates a LayoutDescription for the configured permalink
    :param options:
    :param permalink:
    :param progress_update:
    :param retries:
    :return:
    """
    return echoes.generate_description(
        permalink=permalink,
        status_update=ConstantPercentageCallback(progress_update, -1),
        validate_after_generation=options.advanced_validate_seed_after,
        timeout_during_generation=options.advanced_timeout_during_generation,
        attempts=retries,
    )
