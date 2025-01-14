from typing import Optional

import torch

from transformers.models.hubert.modeling_hubert import (
    HUBERT_INPUTS_DOCSTRING,
    HUBERT_START_DOCSTRING,
    HubertModel,
    HubertPreTrainedModel
)

from transformers.utils import add_start_docstrings, add_start_docstrings_to_model_forward

from ...context import AdapterSetup
from ...heads import ModelWithFlexibleHeadsAdaptersMixin
from ...wrappers import init


@add_start_docstrings(
    """Hubert Model transformer with the option to add multiple flexible heads on top.""",
    HUBERT_START_DOCSTRING,
)
class MertAdapterModel(ModelWithFlexibleHeadsAdaptersMixin, HubertPreTrainedModel):
    def __init__(self, config):
        super().__init__(config)

        self.Hubert = HubertModel(config)
        init(self.Hubert)

        self._init_head_modules()

        self.init_weights()

        # # Initialize weights and apply final processing
        # self.post_init()

    @add_start_docstrings_to_model_forward(HUBERT_INPUTS_DOCSTRING)
    def forward(self, input_values: Optional[torch.Tensor], attention_mask: Optional[torch.Tensor] = None,
                mask_time_indices: Optional[torch.FloatTensor] = None, output_attentions: Optional[bool] = None,
                output_hidden_states: Optional[bool] = None, return_dict: Optional[bool] = None, head=None,
                output_adapter_gating_scores=False,
                output_adapter_fusion_attentions=False,
                **kwargs):
        return_dict = return_dict if return_dict is not None else self.config.use_return_dict
        outputs = self.Hubert(input_values, attention_mask=attention_mask, mask_time_indices=mask_time_indices,
                              output_attentions=output_attentions, output_hidden_states=output_hidden_states,
                              return_dict=return_dict, )

        if not return_dict:
            head_inputs = (outputs[0],) + outputs[2:]
        else:
            head_inputs = outputs
        pooled_output = outputs[1]

        if head or AdapterSetup.get_context_head_setup() or self.active_head:
            head_outputs = self.forward_head(
                head_inputs,
                head_name=head,
                attention_mask=attention_mask,
                return_dict=return_dict,
                pooled_output=pooled_output,
                **kwargs,
            )
            return head_outputs
        else:
            # in case no head is used just return the output of the base model (including pooler output)
            return outputs
