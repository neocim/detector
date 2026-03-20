import asyncio
from collections import defaultdict
from typing import DefaultDict, List

from aiogram import Bot, Router
from aiogram.types import Message, PhotoSize

from detector.helpers import extract_order_number, scan_barcodes

photo_router = Router()
photo_album: DefaultDict[str, List[PhotoSize]] = defaultdict(list)


@photo_router.message(lambda m: m.photo)
async def handle_photos(message: Message, bot: Bot) -> None:
    if message.media_group_id:
        photo_album[message.media_group_id].append(message.photo[-1])  # type: ignore

        await asyncio.sleep(0.2)

        if photo_album[message.media_group_id][-1] is not message.photo[-1]:  # type: ignore
            return

        group = photo_album.pop(message.media_group_id, [])
        for _, photo in enumerate(group, 1):
            b = await get_file_bytes(bot, photo.file_id)
            await process_photo(b)

        await message.answer(f"Получено {len(group)} фото.")
        return

    b = await get_file_bytes(bot, message.photo[-1].file_id)  # type: ignore
    await process_photo(b)
    await message.answer("Фото получено.")


async def process_photo(image_bytes: bytes) -> None:
    print(scan_barcodes(image_bytes))
    print(extract_order_number(image_bytes))


async def get_file_bytes(bot: Bot, file_id: str) -> bytes:
    return (await bot.download_file((await bot.get_file(file_id)).file_path)).read()  # type: ignore
