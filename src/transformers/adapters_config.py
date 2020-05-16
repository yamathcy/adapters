from enum import Enum
import json
from os.path import isfile
import copy


# TODO add more default configs here
ADAPTER_CONFIG_MAP = {
    'pfeiffer': {
        'LN_after': False,
        'LN_before': False,
        'MH_Adapter': False,
        'Output_Adapter': True,
        'adapter_residual_before_ln': False,
        'attention_type': 'sent-lvl-dynamic',
        'new_attention_norm': False,
        'non_linearity': 'relu',
        'original_ln_after': True,
        'original_ln_before': True,
        'reduction_factor': 16,
        'residual_before_ln': True
    }
}

DEFAULT_ADAPTER_CONFIG = 'pfeiffer'


class AdapterType(str, Enum):
    """Models all currently available model adapter types."""

    text_task = "text_task"
    text_lang = "text_lang"
    vision_task = "vision_task"

    @classmethod
    def has(cls, value):
        return value in cls.__members__.values()

    def __repr__(self):
        return self.value


class AdapterConfig:
    def __init__(self, **kwargs):
        self.adapters = kwargs.pop("adapters", {})
        self.config_map = kwargs.pop("config_map", {})

    def adapter_list(self, adapter_type: AdapterType) -> list:
        return [
            k for k, v in self.adapters.items() if v['type'] == adapter_type
        ]

    def get_type(self, adapter_name: str) -> AdapterType:
        if adapter_name in self.adapters:
            return self.adapters[adapter_name]['type']
        else:
            return None

    def get(self, adapter_name: str) -> dict:
        if adapter_name in self.adapters:
            adapter = self.adapters[adapter_name]
            config = adapter['config']
            if not config:
                config = self.config_map[adapter['type']]
            elif isinstance(config, str):
                config = ADAPTER_CONFIG_MAP[config]
            return config
        else:
            return None

    def add(self, adapter_name: str, adapter_type: AdapterType, config=None):
        assert adapter_name not in self.adapters, "An adapter with the same name has already been added."
        # TODO temporary, remove when multiple adapter configs are supported (!)
        assert config is None, "All adapters of one type must have the same config."
        self.adapters[adapter_name] = {
            'type': adapter_type,
            'config': config
        }

    def get_config(self, adapter_type: AdapterType) -> dict:
        config = self.config_map.get(adapter_type, None)
        if isinstance(config, str) and config in ADAPTER_CONFIG_MAP:
            return ADAPTER_CONFIG_MAP[config]
        return config

    def set_config(self, adapter_type: AdapterType, config):
        """Sets the adapter configuration of this adapter type.

        Args:
            adapter_config (str or dict): adapter configuration, can be either:
                - a string identifying a pre-defined adapter configuration
                - a dictionary representing the adapter configuration
                - the path to a file containing the adapter configuration
        """
        assert len(self.adapter_list(adapter_type)) < 1, "Can only set new config if no adapters have been added."
        if isinstance(config, dict) or config in ADAPTER_CONFIG_MAP:
            self.config_map[adapter_type] = config
        elif isfile(config):
            with open(config, 'r', encoding='utf-8') as f:
                self.config_map[adapter_type] = json.load(f)
        else:
            raise ValueError("Unable to identify {} as a valid adapter config.".format(config))

    def to_dict(self):
        output_dict = {}
        output_dict['adapters'] = copy.deepcopy(self.adapters)
        output_dict['config_map'] = copy.deepcopy(self.config_map)
        return output_dict