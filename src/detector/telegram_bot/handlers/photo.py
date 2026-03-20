import asyncio
from collections import defaultdict
from typing import DefaultDict, List, Tuple

from aiogram import Bot, Router
from aiogram.types import Message, PhotoSize

from detector.helpers import process_photo

photo_router = Router()
photo_album: DefaultDict[str, List[PhotoSize]] = defaultdict(list)


def _progress_bar(done: int, total: int, width: int = 10) -> str:
    if total <= 0:
        total = 1
    filled = int(round(width * done / total))
    filled = min(max(filled, 0), width)
    return f"{'█' * filled}{'░' * (width - filled)}"


def _progress_text(done: int, total: int, finished: bool = False) -> str:
    if finished:
        return f"<b>Обработка завершена</b> ({done}/{total})"
    return f"<b>Обработка</b>: {done}/{total} {_progress_bar(done, total)}"


def _result_text(barcodes: list[str], orders: list[str]) -> str:
    if not barcodes:
        barcodes_text = "QR-коды не найдены"
    else:
        barcodes_text = "QR-коды: " + ", ".join(barcodes)

    if not orders:
        orders_text = "Номера заказов не найдены"
    else:
        orders_text = "Номера заказов: " + ", ".join(orders)

    return f"{barcodes_text}\n{orders_text}"


def _album_text(done: int, total: int, results: list[Tuple[list[str], list[str]]], finished: bool = False) -> str:
    lines: list[str] = [_progress_text(done, total, finished=finished)]
    for idx, (barcodes, orders) in enumerate(results, 1):
        lines.append("")
        lines.append(f"Фото {idx}:")
        lines.append(_result_text(barcodes, orders))
    return "\n".join(lines)


async def get_file_bytes(bot: Bot, file_id: str) -> bytes:
    return (await bot.download_file((await bot.get_file(file_id)).file_path)).read()  # type: ignore


@photo_router.message(lambda m: m.photo)
async def handle_photos(message: Message, bot: Bot) -> None:
    if message.media_group_id:
        photo_album[message.media_group_id].append(message.photo[-1])  # type: ignore

        await asyncio.sleep(0.2)

        if photo_album[message.media_group_id][-1] is not message.photo[-1]:  # type: ignore
            return

        group = photo_album.pop(message.media_group_id, [])
        total = len(group)
        results: list[Tuple[list[str], list[str]]] = []
        progress_msg = await message.answer(
            _progress_text(0, total),
            parse_mode="HTML",
        )
        for i, photo in enumerate(group, 1):
            file_bytes = await get_file_bytes(bot, photo.file_id)
            barcodes, orders = await process_photo(file_bytes)
            results.append((barcodes, orders))
            await progress_msg.edit_text(
                _album_text(i, total, results),
                parse_mode="HTML",
            )

        await progress_msg.edit_text(
            _album_text(total, total, results, finished=True),
            parse_mode="HTML",
        )
        await message.answer(f"Получено {total} фото.")
        return

    file_bytes = await get_file_bytes(bot, message.photo[-1].file_id)  # type: ignore
    progress_msg = await message.answer(
        _progress_text(0, 1),
        parse_mode="HTML",
    )
    barcodes, orders = await process_photo(file_bytes)
    await progress_msg.edit_text(
        _album_text(1, 1, [(barcodes, orders)], finished=True),
        parse_mode="HTML",
    )
    await message.answer("Фото получено.")
