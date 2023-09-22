import logging
from typing import Callable, Iterable, Tuple

import torch.nn as nn

from ...composition import adjust_tensors_for_parallel_
from ...layer import AdapterLayer
from ...lora import Linear as LoRALinear
from ...model_mixin import EmbeddingAdaptersMixin, InvertibleAdaptersMixin, ModelBaseAdaptersMixin
from ...prefix_tuning import PrefixTuningShim

logger = logging.getLogger(__name__)


class HubertSelfAttentionAdaptersMixin:
    """Adds adapters to the WavLMSelfAttention module."""

    def init_adapters(self, model_config, adapters_config):
        # Wrap layers for LoRA
        print("initialize adapter in hubert MHSA.")

        # fixme: original name -> q_proj, k_proj, v_proj
        self.q_proj = LoRALinear.wrap(self.q_proj, "selfattn", model_config, adapters_config, attn_key="q")
        self.k_proj = LoRALinear.wrap(self.k_proj, "selfattn", model_config, adapters_config, attn_key="k")
        self.v_proj = LoRALinear.wrap(self.v_proj, "selfattn", model_config, adapters_config, attn_key="v")

        # fixme: no need?
        # self.prefix_tuning = PrefixTuningShim(
        #     self.location_key + "_prefix" if self.location_key else None, model_config, adapters_config
        # )


# For backwards compatibility, BertSelfOutput inherits directly from AdapterLayer
class HubertSelfOutputAdaptersMixin(AdapterLayer):
    """Adds adapters to the BertSelfOutput module."""

    def __init__(self):
        super().__init__("mh_adapter")

    def init_adapters(self, model_config, adapters_config):
        self.location_key = "mh_adapter"
        super().init_adapters(model_config, adapters_config)


# For backwards compatibility, BertOutput inherits directly from AdapterLayer
class HubertOutputAdaptersMixin(AdapterLayer):
    """Adds adapters to the BertOutput module."""

    def __init__(self):
        super().__init__("output_adapter")

    def init_adapters(self, model_config, adapters_config):
        self.location_key = "output_adapter"
        super().init_adapters(model_config, adapters_config)


class HubertLayerAdaptersMixin:
    """Adds adapters to the WavLMLayer module."""

    def init_adapters(self, model_config, adapters_config):
        # Wrap layers for LoRA
        # self.intermediate.dense = LoRALinear.wrap(
        #     self.intermediate.dense, "intermediate", model_config, adapters_config
        # )
        # self.output.dense = LoRALinear.wrap(self.output.dense, "output", model_config, adapters_config)

        # Fixme: key might not be "intermediate", "output"
        self.feed_forward.intermediate_dense = LoRALinear.wrap(
            self.feed_forward.intermediate_dense, "intermediate", model_config, adapters_config
        )
        self.feed_forward_output_dense = LoRALinear.wrap(self.feed_forward_output_dense,
                                                         "output", model_config, adapters_config)

        # Set location keys for prefix tuning
        # self.attention.self.location_key = "self"

        # if hasattr(self, "add_cross_attention") and self.add_cross_attention:
        #     self.crossattention.self.location_key = "cross"


class HubertModelAdaptersMixin(EmbeddingAdaptersMixin, InvertibleAdaptersMixin, ModelBaseAdaptersMixin):
    """Adds adapters to the WavLMModel module."""

    def init_adapters(self, model_config, adapters_config):
        super().init_adapters(model_config, adapters_config)

        # Set hook for parallel composition
        for _, layer in self.iter_layers():
            self._set_layer_hook_for_parallel(layer)

    def _set_layer_hook_for_parallel(self, layer: nn.Module):
        def hook(module, input):
            adjust_tensors_for_parallel_(input[0], input[1])
            return input

        layer.register_forward_pre_hook(hook)

    def iter_layers(self) -> Iterable[Tuple[int, nn.Module]]:
        for i, layer in enumerate(self.encoder.layer):
            yield i, layer

    # def hook_after_embeddings(self, hook_fn: Callable):
    #     return self.embeddings.register_forward_hook(hook_fn)
