# --------------------------------------------------------------------------
# AI Model Load module
#
# @author bnbong bbbong9@gmail.com
# --------------------------------------------------------------------------
import logging
from typing import Any

import torch
from transformers import BertTokenizer

from src.qshing_server.core.exceptions import AIException
from src.qshing_server.service.model.preprocessor import DataPreprocessor
from src.qshing_server.service.model.qbert import QsingBertModel
from src.qshing_server.service.model.tokenizer import QbertUrlTokenizer
from src.qshing_server.service.parser.html_loader import HTMLLoader

logger = logging.getLogger("main")


class PhishingDetector:
    def __init__(self, model_path: str):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = QsingBertModel().to(self.device)

        try:
            checkpoint = torch.load(model_path, map_location=self.device)
            self.model.load_state_dict(checkpoint["model"])
            self.model.eval()
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            raise AIException(e)

        self.url_tokenizer = QbertUrlTokenizer()
        self.bert_tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
        self.html_loader = HTMLLoader.get_instance()

    def predict(self, url: str) -> dict[str, Any]:
        logger.info(f"Predicting URL: {url}")

        html = self.html_loader.load(url)
        if not html:
            return {"result": None, "confidence": None}

        preprocessor = DataPreprocessor(url, html)
        inputs = preprocessor.preprocess(self.device)

        with torch.no_grad():
            _, prob = self.model(inputs)

        return {"result": float(prob) >= 0.5, "confidence": float(prob)}
