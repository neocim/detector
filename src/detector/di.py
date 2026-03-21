from aiogram import Router
from dishka import AsyncContainer, BaseScope, Provider, Scope, from_context, make_async_container, provide
from dishka.integrations.aiogram import ContainerMiddleware, inject_router
from gspread import Spreadsheet, service_account

from detector.config import BotConfig, Config, GoogleConfig


class ConfigProvider(Provider):
    scope: BaseScope | None = Scope.APP
    configs = from_context(Config) + from_context(GoogleConfig) + from_context(BotConfig)


class SheetProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_sheet(self, config: GoogleConfig) -> Spreadsheet:
        return service_account(config.json_key_path).open_by_key(config.table_key)


def get_async_container(config: Config) -> AsyncContainer:
    providers = [ConfigProvider(), SheetProvider()]
    context = {Config: config, GoogleConfig: config.google, BotConfig: config.telegram_bot}

    return make_async_container(*providers, context=context)


def setup_di(
    container: AsyncContainer,
    router: Router,
    *,
    auto_inject: bool = False,
) -> None:
    middleware = ContainerMiddleware(container)

    for observer in router.observers.values():
        observer.middleware(middleware)

    if auto_inject:
        router.startup.register(lambda: inject_router(router=router))
