from pydantic import BaseModel

# COMMON_METADATA = Metadata(
#    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
#    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
# )


class CommonEmailConfig(BaseModel):
    header_image: str | None
    unsubscribe_url: str
    project_name: str
    project_address: str
