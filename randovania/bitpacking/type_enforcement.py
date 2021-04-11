import dataclasses


class DataclassPostInitTypeCheck:
    def __post_init__(self):
        for f in dataclasses.fields(self):
            v = getattr(self, f.name)
            if not isinstance(v, f.type):
                raise ValueError(f"Unexpected type for field {f.name} ({v}): Got {type(v)}, expected {f.type}.")
