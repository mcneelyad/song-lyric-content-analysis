from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True, str_strip_whitespace=True, alias_generator=to_camel
    )