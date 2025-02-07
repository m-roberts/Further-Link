import logging
import os
import sys
from json import dumps

import aiohttp_cors
import click
from aiohttp import web

from further_link.endpoint.apt_version import apt_version
from further_link.endpoint.run import run as run_handler
from further_link.endpoint.run_py import run_py
from further_link.endpoint.upload import upload
from further_link.util import vnc
from further_link.util.ssl_context import ssl_context
from further_link.version import __version__

logging.basicConfig(
    stream=sys.stdout,
    level=(logging.DEBUG if os.environ.get("FURTHER_LINK_DEBUG") else logging.INFO),
)


def port():
    return int(os.environ.get("FURTHER_LINK_PORT", 8028))


def create_app():
    app = web.Application()
    cors = aiohttp_cors.setup(
        app,
        defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
            )
        },
    )

    async def status(_):
        return web.Response(text="OK")

    async def version(_):
        return web.Response(text=dumps({"version": __version__}))

    status_resource = cors.add(app.router.add_resource("/status"))
    cors.add(status_resource.add_route("GET", status))

    status_resource = cors.add(app.router.add_resource("/version/apt/{pkg}"))
    cors.add(status_resource.add_route("GET", apt_version))

    status_resource = cors.add(app.router.add_resource("/version"))
    cors.add(status_resource.add_route("GET", version))

    status_resource = cors.add(app.router.add_resource("/upload"))
    cors.add(status_resource.add_route("POST", upload))

    exec_resource = cors.add(app.router.add_resource("/run-py"))
    cors.add(exec_resource.add_route("GET", run_py))

    exec_resource = cors.add(app.router.add_resource("/run"))
    cors.add(exec_resource.add_route("GET", run_handler))

    return app


@click.command()
def main():
    vnc.create_ssl_certificate()
    return web.run_app(
        create_app(),
        port=port(),
        ssl_context=ssl_context(),
        # Default handle_signals=True will ignore sigterm signals whilst there
        # are requests that are not complete. This isn't appropriate for our
        # indefinitely running websockets and can cause device shutdown to hang
        handle_signals=False,
    )


if __name__ == "__main__":
    main(prog_name="further-link")
