from typing import Callable, Iterable, Optional, Tuple

import torch
import torch.nn as nn

from ...composition import adjust_tensors_for_parallel
from ...layer import AdapterLayer
from ...lora import Linear as LoRALinear
from ...model_mixin import (
    EmbeddingAdaptersMixin,
    EmbeddingAdaptersWrapperMixin,
    InvertibleAdaptersMixin,
    InvertibleAdaptersWrapperMixin,
    ModelBaseAdaptersMixin,
)
from ...prefix_tuning import PrefixTuningShim


class BartAttentionAdaptersMixin:
    """Adds adapters to the BartAttention module."""

    def init_adapters(self, model_config, adapters_config):
        # Wrap layers for LoRA
        self.k_proj = LoRALinear.wrap(self.k_proj, "selfattn", model_config, adapters_config, attn_key="k")
        self.v_proj = LoRALinear.wrap(self.v_proj, "selfattn", model_config, adapters_config, attn_key="v")
        self.q_proj = LoRALinear.wrap(self.q_proj, "selfattn", model_config, adapters_config, attn_key="q")

        self.prefix_tuning = PrefixTuningShim(
            self.location_key + "_prefix" if self.location_key else None, model_config, adapters_config
        )


class BartEncoderLayerAdaptersMixin:
    """Adds adapters to the BartEncoderLayer module of BART."""

    def init_adapters(self, model_config, adapters_config):
        # Wrap layers for LoRA
        self.fc1 = LoRALinear.wrap(self.fc1, "intermediate", model_config, adapters_config)
        self.fc2 = LoRALinear.wrap(self.fc2, "output", model_config, adapters_config)

        # Set attention layer location key for prefix tuning
        self.self_attn.location_key = "encoder"
        self.attention_adapters = AdapterLayer("mh_adapter")
        self.output_adapters = AdapterLayer("output_adapter")


class BartDecoderLayerAdaptersMixin(BartEncoderLayerAdaptersMixin):
    """Adds adapters to the BartDecoderLayer module of BART."""

    def init_adapters(self, model_config, adapters_config):
        super().init_adapters(model_config, adapters_config)
        # Set attention layer location key for prefix tuning
        self.self_attn.location_key = "self"
        self.encoder_attn.location_key = "cross"
        self.cross_attention_adapters = AdapterLayer("cross_adapter")


class BartEncoderAdaptersMixin(InvertibleAdaptersMixin):
    """Adds adapters to the BartEncoder module of BART."""

    def hook_after_embeddings(self, hook_fn: Callable):
        return self.layernorm_embedding.register_forward_hook(hook_fn)


class BartDecoderAdaptersMixin:
    """Adds adapters to the BartDecoder module of BART."""

    def forward(
        self, input_ids: torch.LongTensor = None, encoder_hidden_states: Optional[torch.FloatTensor] = None, **kwargs
    ):
        (input_ids,) = adjust_tensors_for_parallel(encoder_hidden_states, input_ids)
        return super().forward(input_ids=input_ids, encoder_hidden_states=encoder_hidden_states, **kwargs)


class BartModelAdaptersMixin(EmbeddingAdaptersMixin, InvertibleAdaptersWrapperMixin, ModelBaseAdaptersMixin):
    """Adds adapters to the BartModel class."""

    invertible_adapters_base_name = "encoder"

    def iter_layers(self) -> Iterable[Tuple[int, nn.Module]]:
        if hasattr(self, "encoder"):
            for i, layer in enumerate(self.encoder.layers):
                yield i, layer
            for i, layer in enumerate(self.decoder.layers, start=len(self.encoder.layers)):
                yield i, layer
        else:
            for i, layer in enumerate(self.decoder.layers):
                yield i, layer


class BartDecoderWrapperAdaptersMixin(EmbeddingAdaptersWrapperMixin, ModelBaseAdaptersMixin):
    """Adds adapters to the BartDecoderWrapper class."""

    def iter_layers(self) -> Iterable[Tuple[int, nn.Module]]:
        for i, layer in enumerate(self.decoder.layers):
            yield i, layer

    def get_input_embeddings(self):
        return self.decoder.get_input_embeddings()
