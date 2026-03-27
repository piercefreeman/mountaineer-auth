from mountaineer.cli import handle_build

from mountaineer_auth.plugin import plugin

app = plugin.to_webserver()


def build():
    handle_build(webcontroller="mountaineer_auth.cli:app")
