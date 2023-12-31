from typing import Any

import astropy
import numpy as np
from astropy import units as u
from pydantic import field_validator
from pydantic_core.core_schema import ValidationInfo

from sygn.core.context import Context
from sygn.core.entities.photon_sources.photon_source import PhotonSource
from sygn.io.validators import validate_quantity_units
from sygn.util.blackbody import create_blackbody_spectrum
from sygn.util.grid import get_meshgrid
from sygn.util.helpers import Coordinates


class Star(PhotonSource):
    """Class representation of a star.
    """
    name: str
    temperature: Any
    radius: Any
    mass: Any
    distance: Any
    luminosity: Any
    right_ascension: Any
    declination: Any

    @field_validator('distance')
    def _validate_distance(cls, value: Any, info: ValidationInfo) -> astropy.units.Quantity:
        """Validate the distance input.

        :param value: Value given as input
        :param info: ValidationInfo object
        :return: The distance in units of length
        """
        return validate_quantity_units(value=value, field_name=info.field_name, unit_equivalency=(u.m,))

    @field_validator('luminosity')
    def _validate_luminosity(cls, value: Any, info: ValidationInfo) -> astropy.units.Quantity:
        """Validate the luminosity input.

        :param value: Value given as input
        :param info: ValidationInfo object
        :return: The luminosity in units of luminosity
        """
        return validate_quantity_units(value=value, field_name=info.field_name, unit_equivalency=(u.Lsun,)).to(u.Lsun)

    @field_validator('mass')
    def _validate_mass(cls, value: Any, info: ValidationInfo) -> astropy.units.Quantity:
        """Validate the mass input.

        :param value: Value given as input
        :param info: ValidationInfo object
        :return: The mass in units of weight
        """
        return validate_quantity_units(value=value, field_name=info.field_name, unit_equivalency=(u.kg,))

    @field_validator('radius')
    def _validate_radius(cls, value: Any, info: ValidationInfo) -> astropy.units.Quantity:
        """Validate the radius input.

        :param value: Value given as input
        :param info: ValidationInfo object
        :return: The radius in units of length
        """
        return validate_quantity_units(value=value, field_name=info.field_name, unit_equivalency=(u.m,))

    @field_validator('temperature')
    def _validate_temperature(cls, value: Any, info: ValidationInfo) -> astropy.units.Quantity:
        """Validate the temperature input.

        :param value: Value given as input
        :param info: ValidationInfo object
        :return: The temperature in units of temperature
        """
        return validate_quantity_units(value=value, field_name=info.field_name, unit_equivalency=(u.K,))

    @property
    def angular_radius(self) -> astropy.units.Quantity:
        """Return the solid angle covered by the star on the sky.

        :return: The solid angle
        """
        return ((self.radius.to(u.m) / self.distance.to(u.m)) * u.rad).to(u.arcsec)

    @property
    def habitable_zone_central_angular_radius(self) -> astropy.units.Quantity:
        """Return the central habitable zone radius in angular units.

        :return: The central habitable zone radius in angular units
        """
        return (self.habitable_zone_central_radius / self.distance * u.rad).to(u.arcsec)

    @property
    def habitable_zone_central_radius(self) -> astropy.units.Quantity:
        """Return the central habitable zone radius of the star. Calculated as defined in Kopparapu et al. 2013.

        :return: The central habitable zone radius
        """
        incident_solar_flux_inner, incident_solar_flux_outer = 1.7665, 0.3240
        parameter_a_inner, parameter_a_outer = 1.3351E-4, 5.3221E-5
        parameter_b_inner, parameter_b_outer = 3.1515E-9, 1.4288E-9
        parameter_c_inner, parameter_c_outer = -3.3488E-12, -1.1049E-12
        temperature_difference = self.temperature.value - 5780

        incident_stellar_flux_inner = (incident_solar_flux_inner + parameter_a_inner * temperature_difference
                                       + parameter_b_inner * temperature_difference ** 2 + parameter_c_inner
                                       * temperature_difference ** 3)
        incident_stellar_flux_outer = (incident_solar_flux_outer + parameter_a_outer * temperature_difference
                                       + parameter_b_outer * temperature_difference ** 2 + parameter_c_outer
                                       * temperature_difference ** 3)

        radius_inner = np.sqrt(self.luminosity.value / incident_stellar_flux_inner)
        radius_outer = np.sqrt(self.luminosity.value / incident_stellar_flux_outer)
        return ((radius_outer + radius_inner) / 2 * u.au).to(u.m)

    @property
    def solid_angle(self) -> astropy.units.Quantity:
        """Return the solid angle that the source object covers on the sky.

        :return: The solid angle
        """
        return np.pi * (self.radius.to(u.m) / (self.distance.to(u.m)) * u.rad) ** 2

    def _calculate_sky_coordinates(self, context: Context) -> Coordinates:
        """Return the sky coordinate maps of the source. The intensity responses are calculated in a resolution that
        allows the source to fill the grid, thus, each source needs to define its own sky coordinate map. Add 10% to the
        angular radius to account for rounding issues and make sure the source is fully covered within the map.

        :param time: The time
        :param grid_size: The grid size
        :return: A tuple containing the x- and y-sky coordinate maps
        """
        sky_coordinates = get_meshgrid(2 * (1.05 * self.angular_radius), context.settings.grid_size)
        return Coordinates(sky_coordinates[0], sky_coordinates[1])

    def _calculate_sky_brightness_distribution(self, context: Context) -> np.ndarray:
        sky_brightness_distribution = np.zeros(
            ((len(self.mean_spectral_flux_density),) + self.sky_coordinates.x.shape)) * \
                                      self.mean_spectral_flux_density[0].unit
        radius_map = (np.sqrt(self.sky_coordinates.x ** 2 + self.sky_coordinates.y ** 2) <= self.angular_radius)

        for index_wavelength in range(len(self.mean_spectral_flux_density)):
            sky_brightness_distribution[index_wavelength] = radius_map * self.mean_spectral_flux_density[
                index_wavelength]

        return sky_brightness_distribution

    def _calculate_mean_spectral_flux_density(self, context: Context) -> np.ndarray:
        return create_blackbody_spectrum(self.temperature,
                                         context.observatory.instrument_parameters.wavelength_range_lower_limit,
                                         context.observatory.instrument_parameters.wavelength_range_upper_limit,
                                         context.observatory.instrument_parameters.wavelength_bin_centers,
                                         context.observatory.instrument_parameters.wavelength_bin_widths,
                                         self.solid_angle)

    def get_sky_coordinates(self, index_time: int, index_wavelength: int) -> Coordinates:
        return self.sky_coordinates

    def get_sky_brightness_distribution(self, index_time: int, index_wavelength: int) -> np.ndarray:
        return self.sky_brightness_distribution[index_wavelength]
