from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import FSInputFile, Message

start_router = Router()


@start_router.message(CommandStart())
async def start(event: Message) -> None:
    await event.answer_photo(
        photo=FSInputFile("example1.png"),
        caption="Привет! Отправь фото подобное фото, и я извлеку из него QR-код и номер заказа",
    )
