def patch_fastapi_model_field_type() -> None:
    """
    Mountaineer's current client parser expects FastAPI's compatibility ModelField
    objects to expose `.type_`. Newer FastAPI versions only keep the annotation on
    `field_info`, so we restore the attribute for build-time introspection.
    """

    try:
        from fastapi._compat.v2 import ModelField
    except ImportError:
        return

    if hasattr(ModelField, "type_"):
        return

    @property
    def type_(self):  # type: ignore[no-redef]
        return self.field_info.annotation

    ModelField.type_ = type_  # type: ignore[attr-defined]
