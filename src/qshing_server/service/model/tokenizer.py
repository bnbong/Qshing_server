# --------------------------------------------------------------------------
# QBERT tokenizer
#
# refer (준철님 구현체) : https://github.com/capston-qrcode/capstone-qshing-ml-jck/blob/master/preprocessor/tokenizer.py
#
# @author bnbong bbbong9@gmail.com
# --------------------------------------------------------------------------
from collections import Counter
from random import random
from itertools import chain
from typing import Any
from tqdm import tqdm  # type: ignore

import torch


class QbertUrlTokenizer:
    def __init__(
        self,
        pretrained_path=None,
        special_tokens=["[PAD]", "[UNK]", "[MASK]", "[CLS]", "[SEP]"],
    ):
        self.idx_to_token = {}
        self.token_to_idx = {}

        special_chars = [
            " ",
            "!",
            '"',
            "#",
            "$",
            "%",
            "&",
            "'",
            "(",
            ")",
            "*",
            "+",
            ",",
            "-",
            ".",
            ";",
            "<",
            "=",
            ">",
            "?",
            "@",
            "[",
            "\\",
            "]",
            "^",
            "_",
            "`",
            "{",
            "|",
            "}",
        ]

        custom_tokens = {
            ":": 92,
            "/": 93,
            "[PAD]": 94,
            "[NONE]": 95,
            "[CLS]": 96,
            "[SEP]": 97,
        }

        self.token_to_idx.update({char: i for i, char in enumerate(special_chars)})
        self.token_to_idx.update(
            {chr(char): i + 30 for i, char in enumerate(range(48, 58))}
        )
        self.token_to_idx.update(
            {chr(char): i + 40 for i, char in enumerate(range(65, 91))}
        )
        self.token_to_idx.update(
            {chr(char): i + 66 for i, char in enumerate(range(97, 123))}
        )
        self.token_to_idx.update(custom_tokens)

        for k, v in self.token_to_idx.items():
            self.idx_to_token[v] = k

    def tokenize(self, url_list, max_length=None, masking_ratio=0.0):
        # 문자 하나씩 분해 후 토큰 인덱스 변환
        token_ids = []
        mask = []
        for urls in tqdm(url_list, desc="url token"):
            url_item = []
            mask_item = []
            for idx, url in enumerate(urls):
                print(url)
                tokens = [
                    self.token_to_idx.get(ch, self.token_to_idx["[NONE]"]) for ch in url
                ]
                if len(tokens) == 0:
                    continue
                url_item.append(
                    self.token_to_idx["[CLS]"]
                    if idx == 0
                    else self.token_to_idx["[SEP]"]
                )
                url_item.extend(tokens)
            mask_item = [1] * len(url_item)

            if max_length is not None:
                if len(url_item) > max_length:
                    url_item = url_item[:max_length]  # 자르기
                    mask_item = mask_item[:max_length]
                elif len(url_item) < max_length:
                    # 패딩
                    url_item += [self.token_to_idx["[PAD]"]] * (
                        max_length - len(url_item)
                    )
                    mask_item += [0] * (max_length - len(mask_item))
            token_ids.append(url_item)
            mask.append(mask_item)
        # print(len(token_ids), len(token_ids[0]), len(mask), len(mask[0]))
        # print(token_ids[0])
        # print(mask[0])

        # max_length 처리: truncate & pad
        # if max_length is not None:
        #     if len(token_ids) > max_length:
        #         token_ids = token_ids[:max_length]  # 자르기
        #         mask = mask[:max_length]
        #     elif len(token_ids) < max_length:
        #         # 패딩
        #         token_ids += [self.pad_idx] * (max_length - len(token_ids))
        #         mask += [0] * (max_length - len(token_ids))

        # 마스킹 처리
        # 마스킹 대상: PAD, MASK, UNK, 특수 토큰 제외 가능
        # 여기서는 PAD, MASK, UNK, 그리고 스페셜 토큰들은 마스킹 안 한다고 가정
        # 스페셜 토큰 인덱스 구하기
        # special_token_ids = {self.token_to_idx[tok] for tok in self.special_tokens}

        # if masking_ratio > 0 and max_length is not None:
        #     # 마스킹 개수
        #     num_to_mask = int((len(token_ids) - token_ids.count(self.pad_idx)) * masking_ratio)

        #     # 마스킹 가능한 인덱스들 (스페셜 토큰, PAD 토큰 제외)
        #     candidate_indices = [i for i, t in enumerate(token_ids) if t not in special_token_ids]

        #     # 랜덤 샘플
        #     random.shuffle(candidate_indices)
        #     mask_indices = candidate_indices[:num_to_mask]

        #     # 해당 인덱스 [MASK] 토큰으로 교체
        #     for i in mask_indices:
        #         token_ids[i] = self.mask_idx

        return {
            "input_ids": torch.tensor(token_ids),
            "attention_mask": torch.tensor(mask),
        }

    def decode(self, token_ids):
        # 인덱스를 다시 문자로 복원
        return "".join(
            [
                self.idx_to_token[idx]
                for idx in token_ids
                if idx < len(self.idx_to_token)
                and self.idx_to_token[idx] not in self.special_tokens
            ]
        )

    def __len__(self):
        return len(self.idx_to_token)
