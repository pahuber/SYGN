from typing import Any, Tuple

import astropy
import numpy as np
from astropy import units as u
from pydantic import field_validator
from pydantic_core.core_schema import ValidationInfo

from sygn.core.modules.target_system.source import Source
from sygn.io.validators import validate_quantity_units
from sygn.util.grid import get_index_of_closest_value, get_meshgrid


class Planet(Source):
    """Class representation of a planet.
    """
    name: str
    temperature: Any
    radius: Any
    mass: Any
    star_separation_x: Any
    star_separation_y: Any
    star_distance: Any
    number_of_wavelength_bins: int
    grid_size: int
    mean_spectral_flux_density: Any = None

    @field_validator('radius')
    def _validate_radius(cls, value: Any, info: ValidationInfo) -> astropy.units.Quantity:
        """Validate the radius input.

        :param value: Value given as input
        :param info: ValidationInfo object
        :return: The radius in units of length
        """
        return validate_quantity_units(value=value, field_name=info.field_name, unit_equivalency=u.m)

    @field_validator('mass')
    def _validate_mass(cls, value: Any, info: ValidationInfo) -> astropy.units.Quantity:
        """Validate the mass input.

        :param value: Value given as input
        :param info: ValidationInfo object
        :return: The mass in units of weight
        """
        return validate_quantity_units(value=value, field_name=info.field_name, unit_equivalency=u.kg)

    @field_validator('star_separation_x')
    def _validate_star_separation_x(cls, value: Any, info: ValidationInfo) -> astropy.units.Quantity:
        """Validate the star separation x input.

        :param value: Value given as input
        :param info: ValidationInfo object
        :return: The star separation x in units of length
        """
        return validate_quantity_units(value=value, field_name=info.field_name, unit_equivalency=u.m)

    @field_validator('star_separation_y')
    def _validate_star_separation_y(cls, value: Any, info: ValidationInfo) -> astropy.units.Quantity:
        """Validate the star separation y input.

        :param value: Value given as input
        :param info: ValidationInfo object
        :return: The star separation y in units of length
        """
        return validate_quantity_units(value=value, field_name=info.field_name, unit_equivalency=u.m)

    @field_validator('star_distance')
    def _validate_star_distance(cls, value: Any, info: ValidationInfo) -> astropy.units.Quantity:
        """Validate the star distance input.

        :param value: Value given as input
        :param info: ValidationInfo object
        :return: The star distance in units of length
        """
        return validate_quantity_units(value=value, field_name=info.field_name, unit_equivalency=u.m)

    @property
    def solid_angle(self) -> astropy.units.Quantity:
        """Return the solid angle covered by the planet on the sky.

        :return: The solid angle
        """
        return np.pi * (self.radius.to(u.m) / (self.star_distance.to(u.m)) * u.rad) ** 2

    @property
    def star_angular_separation_x(self) -> astropy.units.Quantity:
        """Return the angular star separation x.

        :return: The angular star separation x
        """
        return ((self.star_separation_x.to(u.m) / self.star_distance.to(u.m)) * u.rad).to(u.arcsec)

    @property
    def star_angular_separation_y(self) -> astropy.units.Quantity:
        """Return the angular star separation y.

        :return: The angular star separation y
        """
        return ((self.star_separation_y.to(u.m) / self.star_distance.to(u.m)) * u.rad).to(u.arcsec)

    def get_sky_coordinate_maps(self) -> Tuple[np.ndarray, np.ndarray]:
        if self.star_angular_separation_x >= self.star_angular_separation_y:
            return get_meshgrid(2 * (1.05 * self.star_angular_separation_x), self.grid_size)
        return get_meshgrid(2 * (1.05 * self.star_angular_separation_y), self.grid_size)

    def get_shape_map(self) -> np.ndarray:
        position_map = np.zeros(self.sky_coordinate_maps[0].shape)

        # TODO: implement planet position correctly
        index_x = get_index_of_closest_value(self.sky_coordinate_maps[0][0, :], self.star_angular_separation_x)
        index_y = get_index_of_closest_value(self.sky_coordinate_maps[1][:, 0], self.star_angular_separation_y)

        position_map[index_y][index_x] = 1
        return position_map
