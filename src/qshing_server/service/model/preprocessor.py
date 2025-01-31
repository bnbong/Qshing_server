# --------------------------------------------------------------------------
# Preprocessor module
#
# @author bnbong bbbong9@gmail.com
# --------------------------------------------------------------------------
import logging
import re

import torch
from html2text import HTML2Text
from langdetect import detect  # type: ignore
from transformers import BertTokenizer  # type: ignore

from src.qshing_server.service.model.tokenizer import QbertUrlTokenizer
from src.qshing_server.service.parser.html_loader import HTMLLoader

logger = logging.getLogger("main")


class MultimodalDataset(torch.utils.data.Dataset):
    def __init__(self, urls, contents):
        self.urls = urls
        self.contents = contents

    def __len__(self):
        return len(self.urls)

    def __getitem__(self, idx):
        return {
            "url_input_ids": self.urls["input_ids"].squeeze(0),
            "url_attention_mask": self.urls["attention_mask"].squeeze(0),
            "html_input_ids": self.contents["input_ids"].squeeze(0),
            "html_attention_mask": self.contents["attention_mask"].squeeze(0),
        }


class DataPreprocessor:
    def __init__(self, url: str, html: str):
        self.url = url
        self.html = html
        self.html_tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
        self.url_tokenizer = QbertUrlTokenizer()
        self.max_length = 512

    def preprocess(self, device: str = "cpu"):
        converter = HTML2Text()
        converter.ignore_links = True
        converter.ignore_images = True
        converter.ignore_tables = True

        content = converter.handle(self.html)
        sentences = re.split(r"(?<=[.!?]) +", content)

        contents = []
        for s in sentences:
            try:
                if detect(s) == "en":  # 영어로 되어 있는 사이트만 분석.
                    contents.append(s)
            except:
                continue

        text = "[CLS]" + "[SEP]".join(contents)
        html_tokens = self.html_tokenizer(
            text,
            return_tensors="pt",
            padding="max_length",
            max_length=self.max_length,
            truncation=True,
        )

        url_tokens = self.url_tokenizer.tokenize(
            [[self.url]], max_length=self.max_length
        )

        return {
            "url_input_ids": url_tokens["input_ids"].to(device),
            "url_attention_mask": url_tokens["attention_mask"].to(device),
            "html_input_ids": html_tokens["input_ids"].to(device),
            "html_attention_mask": html_tokens["attention_mask"].to(device),
        }
