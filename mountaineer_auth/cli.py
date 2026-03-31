from mountaineer.cli import handle_build

from mountaineer_auth.plugin import create_plugin

app = create_plugin().to_webserver()


def build():
    handle_build(webcontroller="mountaineer_auth.cli:app")
