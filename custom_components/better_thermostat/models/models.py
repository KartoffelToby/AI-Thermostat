"""Device model handing and quirk detection."""

import logging
import math
import os
from pathlib import Path
from homeassistant.components.climate.const import (HVAC_MODE_HEAT, HVAC_MODE_OFF)
from homeassistant.util import yaml
from .utils import calibration, mode_remap, reverse_modes

_LOGGER = logging.getLogger(__name__)


def convert_inbound_states(self, state):
	"""Convert inbound thermostat state to HA state."""
	get_device_model(self)
	
	config_file = os.path.dirname(os.path.realpath(__file__)) + '/devices/' + self.model.replace("/", "_") + '.yaml'
	
	if state.get('system_mode') is not None:
		hvac_mode = state.get('system_mode')
	else:
		hvac_mode = HVAC_MODE_HEAT
	
	current_heating_setpoint = self._target_temp
	
	if Path(config_file).is_file():
		config = yaml.load_yaml(config_file)
		self.calibration_type = config.get('calibration_type')
		if config.get('calibration_type') == 1:
			if state.get('current_heating_setpoint') == 5:
				hvac_mode = HVAC_MODE_OFF
		if config.get('mode_map') is not None and state.get('system_mode') is not None:
			hvac_mode = mode_remap(hvac_mode, reverse_modes(config.get('mode_map')))
	
	return {"current_heating_setpoint": current_heating_setpoint, "local_temperature": state.get('local_temperature'), "local_temperature_calibration": state.get('local_temperature_calibration'),
		"system_mode"                 : hvac_mode}


def get_device_model(self):
	"""Fetches the device model from HA."""
	
	if self.model is None:
		try:
			if self.hass.states.get(self.heater_entity_id).attributes.get('device') is not None:
				self.model = self.hass.states.get(self.heater_entity_id).attributes.get('device').get('model')
			else:
				raise ValueError
		except (RuntimeError, ValueError, AttributeError, KeyError, TypeError, NameError, IndexError) as e:
			_LOGGER.error("better_thermostat %s: can't read the device model of TVR. enable include_device_information in z2m or checkout issue #1", self.name)
	else:
		return self.model


def convert_outbound_states(self, hvac_mode):
	"""Convert HA state to outbound thermostat state."""
	get_device_model(self)
	
	state = self.hass.states.get(self.heater_entity_id).attributes
	
	config_file = os.path.dirname(os.path.realpath(__file__)) + '/devices/' + self.model.replace("/", "_") + '.yaml'
	
	current_heating_setpoint = None
	
	if Path(config_file).is_file():
		config = yaml.load_yaml(config_file)
		local_temperature_calibration = calibration(self, config.get('calibration_type'))
		self.calibration_type = config.get('calibration_type')
		if config.get('calibration_round'):
			local_temperature_calibration = int(math.ceil(local_temperature_calibration))
		if config.get('calibration_type') == 0:
			current_heating_setpoint = state.get('current_heating_setpoint')
		elif config.get('calibration_type') == 1:
			current_heating_setpoint = local_temperature_calibration
		
		if state.get('system_mode') is not None:
			if config.get('mode_map') is not None:
				hvac_mode = mode_remap(hvac_mode, config.get('mode_map'))
		else:
			if hvac_mode == HVAC_MODE_OFF:
				current_heating_setpoint = 5
	
	else:
		current_heating_setpoint = self._target_temp
		local_temperature_calibration = int(math.ceil(calibration(self, 0)))
	
	return {
		"current_heating_setpoint"     : current_heating_setpoint,
		"local_temperature"            : state.get('local_temperature'),
		"system_mode"                  : hvac_mode,
		"local_temperature_calibration": local_temperature_calibration
	}
