import logging

from custom_components.better_thermostat.helpers import convert_decimal

_LOGGER = logging.getLogger(__name__)


def mode_remap(hvac_mode, modes):
	if modes is None:
		return hvac_mode
	if modes.get(hvac_mode) is not None:
		return modes.get(hvac_mode)
	else:
		return hvac_mode

def reverse_modes(modes):
	changed_dict = {}
	for key, value in modes.items():
		changed_dict[value] = key
	return changed_dict


def calibration(self, type):
	if type == 1:
		return temperature_calibration(self)
	if type == 0:
		return default_calibration(self)


def default_calibration(self):
	state = self.hass.states.get(self.heater_entity_id).attributes
	new_calibration = float((float(self._cur_temp) - float(state.get('local_temperature'))) + float(state.get('local_temperature_calibration')))
	return convert_decimal(new_calibration)

def temperature_calibration(self):
	state = self.hass.states.get(self.heater_entity_id).attributes
	new_calibration = abs(float(round((float(self._target_temp) - float(self._cur_temp)) + float(state.get('local_temperature')), 2)))
	if new_calibration < float(self._min_temp):
		new_calibration = float(self._min_temp)
	if new_calibration > float(self._max_temp):
		new_calibration = float(self._max_temp)
	
	return new_calibration
