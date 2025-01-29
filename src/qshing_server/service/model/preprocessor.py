# --------------------------------------------------------------------------
# Preprocessor module
#
# @author bnbong bbbong9@gmail.com
# --------------------------------------------------------------------------
import re
import torch
import logging
from tqdm import tqdm  # type: ignore

from transformers import BertTokenizer  # type: ignore
from html2text import HTML2Text
from langdetect import detect  # type: ignore

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
    def __init__(self, url: str):
        self.html_tokenizer = BertTokenizer.from_pretrained(
            "bert-base-uncased", use_fast=True
        )
        self.url_tokenizer = QbertUrlTokenizer()
        self.max_length = 512
        self.urls, self.contents = self.__init_data(url)

    def __init_data(self, url: str):
        urls, html = HTMLLoader.load(url)
        converter = HTML2Text()
        converter.ignore_links = True
        converter.ignore_images = True
        converter.ignore_tables = True

        content = converter.handle(html)
        sentences = re.split(r"(?<=[.!?]) +", content)

        contents = []
        for s in sentences:
            try:
                if detect(s) == "en":
                    contents.append(s)
            except:
                pass

        return urls, contents

    def preprocess(self):
        self.urls = self._tokenize_url(self.urls)
        self.contents = self._tokenize_content(self.contents)

        print(
            self.urls["input_ids"].isnan().any(),
            self.urls["attention_mask"].isnan().any(),
        )
        print(
            self.contents["input_ids"].isnan().any(),
            self.contents["attention_mask"].isnan().any(),
        )

        input_data = MultimodalDataset(self.urls, self.contents)
        return input_data

    def _tokenize_url(self, urls):
        return self.url_tokenizer.tokenize(urls)

    def _tokenize_content(self, contents):
        tokens = ["[CLS]"]
        for sentences in tqdm(contents, desc="content tokenization"):
            token = []
            for idx, s in enumerate(sentences):
                if idx != 0:
                    token.append("[SEP]")
                token.extend(s)
            token = "".join(token)
            tokens.append(token)

        tokenized_output = self.html_tokenizer(
            tokens,
            return_tensors="pt",
            padding="max_length",
            max_length=self.max_length,
            truncation=True,
        )
        return tokenized_output
