import glob
from pathlib import Path
from typing import Tuple

from sygn.core.context import Context
from sygn.core.modules.config_loader_module import ConfigLoaderModule
from sygn.core.modules.target_loader_module import TargetLoaderModule
from sygn.io.fits_reader import FITSReader
from sygn.util.helpers import FITSDataType


class FITSReaderModule():
    """Class representation of the FITS reader module.
    """

    def __init__(self, input_path: Path, data_type: Tuple[FITSDataType]):
        """Constructor method.

        :param input_path: Input path of the FITS file
        :param data_type: Type of the data to be written to a FITS file
        """
        self._input_path = input_path
        self._data_type = data_type

    def _create_entities_from_fits_header(self, context, data_fits_header) -> Context:
        config_dict = FITSReader._create_config_dict_from_fits_header(data_fits_header)
        context = ConfigLoaderModule(path_to_config_file=None, config_dict=config_dict).apply(context)
        target_dict = FITSReader._create_target_dict_from_fits_header(data_fits_header)
        context = TargetLoaderModule(path_to_context_file=None, config_dict=target_dict).apply(context)
        return context

    def apply(self, context: Context) -> Context:
        """Read the FITS file and load the settings, mission, observatory and photon sources.

        :param context: The context object of the pipeline
        :return: The (updated) context object
        """
        if self._data_type == FITSDataType.SyntheticMeasurement:
            context.data, data_fits_header = FITSReader.read_fits(self._input_path, context)
            self._create_entities_from_fits_header(context, data_fits_header)

        elif self._data_type == FITSDataType.Template:
            fits_files = glob.glob(f"{self._input_path}/*.fits")
            for fits_file in fits_files:
                template, template_fits_header = FITSReader.read_fits(fits_file, context)

                # Check that template properties match data properties
                FITSReader._check_template_fits_header(context, template_fits_header)

                context.templates.append(template)
        return context
