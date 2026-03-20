import logging
import re
from io import BytesIO

import cv2
import numpy
from PIL import Image
from pyzbar.pyzbar import decode
from surya.detection import DetectionPredictor
from surya.foundation import FoundationPredictor
from surya.recognition import RecognitionPredictor

ORDER_PATTERN = r"\d{8}-\d{4}-\d"

logging.basicConfig(level=logging.DEBUG)
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

    if data not in results:
        results.append(data)

    return results


def extract_order_number(image_bytes: bytes):
    image = Image.open(BytesIO(image_bytes))

    predictions = recognition([image], det_predictor=detection)

    all_text = []
    for line in predictions[0].text_lines:
        all_text.append(line.text)

    print(all_text)

    return re.findall(ORDER_PATTERN, "\n".join(all_text))
