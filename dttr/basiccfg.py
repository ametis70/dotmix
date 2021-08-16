from pydantic.main import BaseModel

from .abstractcfg import AbstractConfig, BaseSchema
from .utils import deep_merge, load_toml_cfg_model, print_key_values


class BasicConfig(AbstractConfig[BaseSchema, BaseModel]):
    def load_cfg(self):
        self.cfg = load_toml_cfg_model(self.cfg_file, BaseSchema)

    def compute_data(self):
        if not self.cfg.custom:
            self.data = BaseModel.construct(**{})
            return

        if not self.cfg.extends:
            self.data = BaseModel.construct(**self.cfg.custom)

        data_dict = {}
        for parent in reversed(self.parents):
            data_dict = deep_merge(data_dict, parent.cfg.custom)

        self.data = BaseModel.construct(**data_dict)

    def print_data(self):
        print_key_values(self.data.dict())
