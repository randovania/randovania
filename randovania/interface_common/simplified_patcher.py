from randovania.interface_common import echoes
from randovania.interface_common.options import Options
from randovania.layout.generator_parameters import GeneratorParameters
from randovania.layout.layout_description import LayoutDescription
from randovania.lib.status_update_lib import ProgressUpdateCallable, ConstantPercentageCallback

export_busy = False


def generate_layout(options: Options,
                    parameters: GeneratorParameters,
                    progress_update: ProgressUpdateCallable,
                    retries: int | None = None,
                    ) -> LayoutDescription:
    """
    Creates a LayoutDescription for the configured permalink
    :param options:
    :param parameters:
    :param progress_update:
    :param retries:
    :return:
    """
    return echoes.generate_description(
        parameters=parameters,
        status_update=ConstantPercentageCallback(progress_update, -1),
        validate_after_generation=options.advanced_validate_seed_after,
        timeout_during_generation=options.advanced_timeout_during_generation,
        attempts=retries,
    )
