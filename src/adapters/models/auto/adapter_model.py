from collections import OrderedDict

from transformers.models.auto.auto_factory import _BaseAutoModelClass, auto_class_update
from transformers.models.auto.configuration_auto import CONFIG_MAPPING_NAMES

from .auto_factory import _LazyAdapterModelAutoMapping


# Make sure that children are placed before parents!
ADAPTER_MODEL_MAPPING_NAMES = OrderedDict(
    [
        ("albert", "AlbertAdapterModel"),
        ("bart", "BartAdapterModel"),
        ("beit", "BeitAdapterModel"),
        ("bert", "BertAdapterModel"),
        ("bert-generation", "BertGenerationAdapterModel"),
        ("clip", "CLIPAdapterModel"),
        ("deberta", "DebertaAdapterModel"),
        ("deberta-v2", "DebertaV2AdapterModel"),
        ("distilbert", "DistilBertAdapterModel"),
        ("electra", "ElectraAdapterModel"),
        ("gpt2", "GPT2AdapterModel"),
        ("gptj", "GPTJAdapterModel"),
        ("hubert", "HubertAdapterModel"),
        ("llama", "LlamaAdapterModel"),
        ("mbart", "MBartAdapterModel"),
        ("mert_model", "MertAdapterModel"),
        ("roberta", "RobertaAdapterModel"),
        ("t5", "T5AdapterModel"),
        ("vit", "ViTAdapterModel"),
        ("wavlm","WavLMAdapterModel"),
        ("xlm-roberta", "XLMRobertaAdapterModel"),
        ("xmod", "XmodAdapterModel"),
    ]
)


ADAPTER_MODEL_MAPPING = _LazyAdapterModelAutoMapping(CONFIG_MAPPING_NAMES, ADAPTER_MODEL_MAPPING_NAMES)


class AutoAdapterModel(_BaseAutoModelClass):
    _model_mapping = ADAPTER_MODEL_MAPPING


AutoAdapterModel = auto_class_update(AutoAdapterModel, head_doc="adapters and flexible heads")
