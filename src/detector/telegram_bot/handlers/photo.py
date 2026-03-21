import asyncio
from collections import defaultdict
from datetime import datetime
from itertools import zip_longest
from typing import DefaultDict, List, Tuple

from aiogram import Bot, Router
from aiogram.enums import ParseMode
from aiogram.types import Message, PhotoSize
from dishka import FromDishka
from gspread import Spreadsheet

from detector.helpers import process_photo

photo_router = Router()
photo_album: DefaultDict[str, List[Tuple[PhotoSize, Message]]] = defaultdict(list)


@photo_router.message(lambda m: m.photo)
async def handle_photos(message: Message, bot: Bot, table: FromDishka[Spreadsheet]) -> None:
    if message.media_group_id:
        photo_album[message.media_group_id].append((message.photo[-1], message))  # type: ignore

        await asyncio.sleep(0.2)
        if photo_album[message.media_group_id][-1][0] is not message.photo[-1]:  # type: ignore
            return

        group = photo_album.pop(message.media_group_id, [])
        total = len(group)

        progress_msg = await message.answer(
            _progress_text(0, total),
            parse_mode=ParseMode.HTML,
        )

        results = []
        for i, (photo, photo_msg) in enumerate(group, 1):
            barcodes, orders = await process_photo(await get_file_bytes(bot, photo.file_id))

            results.append((barcodes, orders))
            await _append_rows(table, _sheet_rows(photo_msg, barcodes, orders))

            await progress_msg.edit_text(
                _album_text(i, total, results),
                parse_mode=ParseMode.HTML,
            )

        await progress_msg.edit_text(
            _album_text(total, total, results, finished=True),
            parse_mode=ParseMode.HTML,
        )
        return

    progress_msg = await message.answer(
        _progress_text(0, 1),
        parse_mode=ParseMode.HTML,
    )

    barcodes, orders = await process_photo(await get_file_bytes(bot, message.photo[-1].file_id))  # type: ignore
    await _append_rows(table, _sheet_rows(message, barcodes, orders))

    await progress_msg.edit_text(
        _album_text(1, 1, [(barcodes, orders)], finished=True),
        parse_mode=ParseMode.HTML,
    )


def _progress_bar(done: int, total: int, width: int = 10) -> str:
    if total <= 0:
        total = 1
    filled = int(round(width * done / total))
    filled = min(max(filled, 0), width)
    return f"{'█' * filled}{'░' * (width - filled)}"


def _progress_text(done: int, total: int, finished: bool = False) -> str:
    if finished:
        return f"<b>Обработка завершена</b> ({done}/{total})"
    return f"<b>Обработка...</b> ({done}/{total})\n{_progress_bar(done, total)}"


def _result_text(barcodes: list[str], orders: list[str]) -> str:
    barcodes_text = "QR-коды не найдены" if not barcodes else "QR-коды: " + ", ".join(barcodes)
    orders_text = "Номера заказов не найдены" if not orders else "Номера заказов: " + ", ".join(orders)

    return f"{barcodes_text}\n{orders_text}"


def _album_text(done: int, total: int, results: list[Tuple[list[str], list[str]]], finished: bool = False) -> str:
    lines: list[str] = [_progress_text(done, total, finished=finished)]
    for idx, (barcodes, orders) in enumerate(results, 1):
        lines.append("")
        lines.append(f"Фото {idx}:")
        lines.append(_result_text(barcodes, orders))
    return "\n".join(lines)


def _message_link(message: Message) -> str:
    if message.chat.username:
        return f"https://t.me/{message.chat.username}/{message.message_id}"

    chat_id = message.chat.id
    if chat_id < 0:
        chat_id_str = str(chat_id)
        if chat_id_str.startswith("-100"):
            chat_id_str = chat_id_str[4:]
        else:
            chat_id_str = chat_id_str[1:]
        return f"https://t.me/c/{chat_id_str}/{message.message_id}"

    return ""


def _sheet_rows(message: Message, barcodes: list[str], orders: list[str]) -> list[list[str]]:
    processed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    username = ""
    if message.from_user and message.from_user.username:
        username = f"@{message.from_user.username}"
    elif message.sender_chat and message.sender_chat.username:
        username = f"@{message.sender_chat.username}"
    elif message.from_user:
        username = f"id:{message.from_user.id}"
    elif message.sender_chat:
        username = f"id:{message.sender_chat.id}"

    link = _message_link(message)

    rows = []
    for order, barcode in zip_longest(orders, barcodes):
        if not order and not barcode:
            continue

        rows.append([processed_at, username, order or "", barcode or "", link])

    return rows


async def _append_rows(table: Spreadsheet, rows: list[list[str]]) -> None:
    if not rows:
        return

    await asyncio.to_thread(table.sheet1.append_rows, rows)


async def get_file_bytes(bot: Bot, file_id: str) -> bytes:
    return (await bot.download_file((await bot.get_file(file_id)).file_path)).read()  # type: ignore
