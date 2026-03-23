import logging
import re
import time
from io import BytesIO
from pathlib import Path

import cv2
import numpy
from PIL import Image
from pyzbar.pyzbar import decode
from surya.detection import DetectionPredictor
from surya.foundation import FoundationPredictor
from surya.recognition import RecognitionPredictor

ORDER_PATTERN = r"\d{8,}-\d{4}-\d"

logger = logging.getLogger(__name__)

foundation = FoundationPredictor()
recognition = RecognitionPredictor(foundation)
detection = DetectionPredictor()


def scan_barcodes(image_bytes: bytes):
    nparr = numpy.frombuffer(image_bytes, numpy.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if image is None:
        logger.error("Can not open image")
        return []

    results = []

    for barcode in decode(image):
        data = barcode.data.decode("utf-8")
        results.append(data)

    detector = cv2.QRCodeDetector()
    data, _, _ = detector.detectAndDecode(image)

    if data and data not in results:
        results.append(data)

    results = [r for r in results if r]

    return results


def ocr_orders(image_bytes: bytes) -> tuple[list[str]]:
    image = Image.open(BytesIO(image_bytes))

    predictions = recognition([image], det_predictor=detection)

    all_text = []
    for line in predictions[0].text_lines:
        all_text.append(line.text)

    text = "\n".join(all_text)
    return re.findall(ORDER_PATTERN, text)


def _rotate_image_bytes_90(image_bytes: bytes) -> bytes:
    image = Image.open(BytesIO(image_bytes))
    image = image.rotate(90, expand=True)

    buf = BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


async def process_photo(image_bytes: bytes) -> tuple[list[str], list[str]]:
    current_bytes = image_bytes

    barcodes = scan_barcodes(current_bytes)
    orders = ocr_orders(current_bytes)

    max_len = 0
    for _ in range(3):
        if not orders:
            logger.debug("Fallback mode")
            current_bytes = _rotate_image_bytes_90(current_bytes)
            orders = ocr_orders(current_bytes)

            best_order = []
            for order in orders:
                logger.debug("Order: %s", order)
                if len(order) > max_len:
                    max_len = len(order)
                    best_order = order
            if best_order:
                orders = [best_order]
        else:
            break

    return barcodes, orders
