# --------------------------------------------------------------------------
# AI Model Load module
#
# @author bnbong bbbong9@gmail.com
# --------------------------------------------------------------------------
import torch
import torch.nn as nn
import logging
from torch.utils.data import DataLoader

from src.qshing_server.core.exceptions import AIException
from src.qshing_server.service.model.preprocessor import DataPreprocessor
from src.qshing_server.service.model.qbert import QsingBertModel

logger = logging.getLogger("main")


class PhishingDetection:
    def __init__(self, model_path: str):
        self.device = torch.device("cpu")
        self.model = QsingBertModel()
        try:
            save_state = torch.load(model_path, map_location=self.device)
            self.model.load_state_dict(save_state["model"])
            self.model.to(self.device)
            self.model.eval()
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            raise AIException(e)

    def __to_tensor(self, url: str):
        preprocessor = DataPreprocessor(url)
        input_data = preprocessor.preprocess()
        print(input_data)

        dataloader = DataLoader(input_data, batch_size=1, shuffle=False)
        return next(iter(dataloader))

    def predict(self, url: str):
        logger.info(f"Predicting URL: {url}")
        tensor_input = self.__to_tensor(url)

        with torch.no_grad():
            y_hat, y_prob = self.model(tensor_input)

        predicted_label = (y_prob >= 0.5).long()

        logger.info(f"Prediction result: {predicted_label}")

        return {"result": predicted_label, "confidence": y_prob}
