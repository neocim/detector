import logging
import re

import cv2
from PIL import Image
from pyzbar.pyzbar import decode
from surya.detection import DetectionPredictor
from surya.foundation import FoundationPredictor
from surya.recognition import RecognitionPredictor

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

ORDER_PATTERN = r"\d{8}-\d{4}-\d"


def scan_barcodes(image_path: str):
    img = cv2.imread(image_path)

    if img is not None:
        results = []
        for barcode in decode(img):
            data = barcode.data.decode("utf-8")
            results.append(data)

        if not results:
            detector = cv2.QRCodeDetector()
            data, _, _ = detector.detectAndDecode(img)
            results.append(data)

        return results
    logger.error(f"Can not open image `{image_path}`")


def extract_order_number(image_path: str):
    image = Image.open(image_path)

    foundation = FoundationPredictor()
    recognition = RecognitionPredictor(foundation)
    detection = DetectionPredictor()

    predictions = recognition([image], det_predictor=detection)

    all_text = []
    for line in predictions[0].text_lines:
        all_text.append(line.text)

    full_text = "\n".join(all_text)

    logger.info("RAW OCR:")
    logger.info(full_text)

    orders = re.findall(ORDER_PATTERN, full_text)

    return orders


def main() -> None:
    orders = extract_order_number("1.png")
    results = scan_barcodes("1.png")

    print(results)
    print("\nFOUND ORDERS:")
    for o in orders:
        print(o)
