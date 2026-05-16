from __future__ import annotations

import argparse
import math
import random
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset, Sampler
from tqdm import tqdm
from transformers import AutoModelForSequenceClassification, AutoTokenizer, BertConfig, BertForSequenceClassification, get_linear_schedule_with_warmup

from .io import normalize_label, read_jsonl
from .metrics import evaluate_records, write_metric_report


class JsonlDataset(Dataset):
    def __init__(self, records: list[dict[str, Any]]):
        self.records = records

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int) -> dict[str, Any]:
        return self.records[index]


class HashTokenizer:
    def __init__(self, vocab_size: int = 4096):
        self.vocab_size = vocab_size
        self.pad_token_id = 0
        self.cls_token_id = 1
        self.sep_token_id = 2
        self.unk_token_id = 3

    def __call__(
        self,
        texts: list[str],
        padding: bool,
        truncation: bool,
        max_length: int,
        return_tensors: str,
    ) -> dict[str, torch.Tensor]:
        encoded: list[list[int]] = []
        for text in texts:
            tokens = [self.cls_token_id]
            for word in text.lower().split():
                tokens.append(4 + (hash(word) % (self.vocab_size - 4)))
            tokens.append(self.sep_token_id)
            if truncation:
                tokens = tokens[:max_length]
            encoded.append(tokens)

        width = max(len(tokens) for tokens in encoded) if padding else max_length
        width = min(width, max_length)
        input_ids = []
        attention_mask = []
        for tokens in encoded:
            tokens = tokens[:width]
            mask = [1] * len(tokens)
            if padding and len(tokens) < width:
                pad_len = width - len(tokens)
                tokens = tokens + [self.pad_token_id] * pad_len
                mask = mask + [0] * pad_len
            input_ids.append(tokens)
            attention_mask.append(mask)
        return {
            "input_ids": torch.tensor(input_ids, dtype=torch.long),
            "attention_mask": torch.tensor(attention_mask, dtype=torch.long),
        }

    def save_pretrained(self, output_dir: str | Path) -> None:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        (Path(output_dir) / "hash_tokenizer.txt").write_text(
            f"vocab_size={self.vocab_size}\n",
            encoding="utf-8",
        )


class GroupedBatchSampler(Sampler[list[int]]):
    def __init__(self, records: list[dict[str, Any]], max_records: int, seed: int):
        if max_records < 1:
            raise ValueError("max_records must be positive")
        self.max_records = max_records
        self.seed = seed
        self.epoch = 0
        groups: dict[str, list[int]] = defaultdict(list)
        for index, record in enumerate(records):
            groups[str(record.get("base_id", record.get("id")))].append(index)
        self.groups = list(groups.values())

    def __iter__(self):
        rng = random.Random(self.seed + self.epoch)
        self.epoch += 1
        groups = [list(group) for group in self.groups]
        rng.shuffle(groups)
        batch: list[int] = []
        for group in groups:
            rng.shuffle(group)
            if batch and len(batch) + len(group) > self.max_records:
                yield batch
                batch = []
            if len(group) > self.max_records:
                for start in range(0, len(group), self.max_records):
                    yield group[start : start + self.max_records]
            else:
                batch.extend(group)
        if batch:
            yield batch

    def __len__(self) -> int:
        batches = 0
        batch_size = 0
        for group in self.groups:
            if batch_size and batch_size + len(group) > self.max_records:
                batches += 1
                batch_size = 0
            if len(group) > self.max_records:
                batches += math.ceil(len(group) / self.max_records)
            else:
                batch_size += len(group)
        if batch_size:
            batches += 1
        return batches


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train PACT safety classifier.")
    parser.add_argument("--train-jsonl", required=True)
    parser.add_argument("--valid-jsonl", required=True)
    parser.add_argument("--model-name", default="microsoft/deberta-v3-large")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--eval-batch-size", type=int, default=16)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--lr", type=float, default=3e-5)
    parser.add_argument("--weight-decay", type=float, default=0.01)
    parser.add_argument("--warmup-ratio", type=float, default=0.06)
    parser.add_argument("--consistency-weight", type=float, default=0.2)
    parser.add_argument("--calibration-alpha", type=float, default=0.0)
    parser.set_defaults(detach_calibration_prior=True)
    parser.add_argument("--detach-calibration-prior", dest="detach_calibration_prior", action="store_true")
    parser.add_argument("--trainable-calibration-prior", dest="detach_calibration_prior", action="store_false")
    parser.add_argument("--disable-grouped-batches", action="store_true")
    parser.add_argument("--grad-accum-steps", type=int, default=1)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--fp16", action="store_true")
    parser.add_argument("--max-train-records", type=int, default=0)
    parser.add_argument("--max-valid-records", type=int, default=0)
    parser.add_argument("--random-tiny-model", action="store_true", help="Engineering smoke only: no pretrained weights.")
    return parser.parse_args()


def make_collate(tokenizer, max_length: int):
    def collate(batch: list[dict[str, Any]]) -> dict[str, Any]:
        texts = [record["text"] for record in batch]
        encoded = tokenizer(texts, padding=True, truncation=True, max_length=max_length, return_tensors="pt")
        labels = torch.tensor([normalize_label(record["label"]) for record in batch], dtype=torch.long)
        pressure_texts = [record.get("pressure_only_text") or "" for record in batch]
        pressure_encoded = tokenizer(
            pressure_texts,
            padding=True,
            truncation=True,
            max_length=max_length,
            return_tensors="pt",
        )
        return {
            "encoded": encoded,
            "labels": labels,
            "pressure_encoded": pressure_encoded,
            "base_ids": [str(record.get("base_id", record.get("id"))) for record in batch],
            "records": batch,
        }

    return collate


def move_to_device(batch: dict[str, torch.Tensor], device: str) -> dict[str, torch.Tensor]:
    return {key: value.to(device) for key, value in batch.items()}


def pair_consistency_loss(logits: torch.Tensor, base_ids: list[str]) -> torch.Tensor:
    groups: dict[str, list[int]] = defaultdict(list)
    for index, base_id in enumerate(base_ids):
        groups[base_id].append(index)

    losses: list[torch.Tensor] = []
    log_probs = F.log_softmax(logits, dim=-1)
    probs = log_probs.exp()
    for indices in groups.values():
        if len(indices) < 2:
            continue
        idx = torch.tensor(indices, device=logits.device)
        group_probs = probs.index_select(0, idx)
        mean_prob = group_probs.mean(dim=0, keepdim=True).clamp_min(1e-8)
        group_log_probs = log_probs.index_select(0, idx)
        losses.append(F.kl_div(group_log_probs, mean_prob.expand_as(group_probs), reduction="batchmean"))

    if not losses:
        return logits.new_tensor(0.0)
    return torch.stack(losses).mean()


@torch.no_grad()
def predict_probs(model, tokenizer, records: list[dict[str, Any]], args: argparse.Namespace) -> list[float]:
    model.eval()
    loader = DataLoader(
        JsonlDataset(records),
        batch_size=args.eval_batch_size,
        shuffle=False,
        collate_fn=make_collate(tokenizer, args.max_length),
    )
    probs: list[float] = []
    for batch in loader:
        encoded = move_to_device(batch["encoded"], args.device)
        logits = model(**encoded).logits
        if args.calibration_alpha > 0:
            pressure_encoded = move_to_device(batch["pressure_encoded"], args.device)
            pressure_logits = model(**pressure_encoded).logits
            logits = logits - args.calibration_alpha * pressure_logits
        if logits.shape[-1] == 1:
            batch_probs = torch.sigmoid(logits.squeeze(-1))
        else:
            batch_probs = torch.softmax(logits, dim=-1)[:, 1]
        probs.extend(float(value) for value in batch_probs.cpu())
    return probs


def main() -> None:
    args = parse_args()
    set_seed(args.seed)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    train_records = read_jsonl(args.train_jsonl)
    valid_records = read_jsonl(args.valid_jsonl)
    if args.max_train_records > 0:
        train_records = train_records[: args.max_train_records]
    if args.max_valid_records > 0:
        valid_records = valid_records[: args.max_valid_records]

    if args.random_tiny_model:
        tokenizer = HashTokenizer()
        config = BertConfig(
            vocab_size=tokenizer.vocab_size,
            hidden_size=64,
            num_hidden_layers=2,
            num_attention_heads=2,
            intermediate_size=128,
            max_position_embeddings=max(args.max_length, 256),
            num_labels=2,
        )
        model = BertForSequenceClassification(config)
    else:
        tokenizer = AutoTokenizer.from_pretrained(args.model_name, use_fast=True)
        model = AutoModelForSequenceClassification.from_pretrained(args.model_name, num_labels=2)
    model.to(args.device)

    collate = make_collate(tokenizer, args.max_length)
    train_dataset = JsonlDataset(train_records)
    if args.disable_grouped_batches:
        train_loader = DataLoader(
            train_dataset,
            batch_size=args.batch_size,
            shuffle=True,
            collate_fn=collate,
        )
    else:
        train_loader = DataLoader(
            train_dataset,
            batch_sampler=GroupedBatchSampler(train_records, max_records=args.batch_size, seed=args.seed),
            collate_fn=collate,
        )

    no_decay = ("bias", "LayerNorm.weight")
    optimizer_grouped_parameters = [
        {
            "params": [p for n, p in model.named_parameters() if not any(nd in n for nd in no_decay)],
            "weight_decay": args.weight_decay,
        },
        {
            "params": [p for n, p in model.named_parameters() if any(nd in n for nd in no_decay)],
            "weight_decay": 0.0,
        },
    ]
    optimizer = torch.optim.AdamW(optimizer_grouped_parameters, lr=args.lr)
    total_steps = math.ceil(len(train_loader) / args.grad_accum_steps) * args.epochs
    warmup_steps = int(total_steps * args.warmup_ratio)
    scheduler = get_linear_schedule_with_warmup(optimizer, warmup_steps, total_steps)
    scaler = torch.cuda.amp.GradScaler(enabled=args.fp16 and args.device.startswith("cuda"))

    best_f1 = -1.0
    global_step = 0
    for epoch in range(1, args.epochs + 1):
        model.train()
        optimizer.zero_grad(set_to_none=True)
        progress = tqdm(train_loader, desc=f"epoch-{epoch}")
        for step, batch in enumerate(progress, start=1):
            encoded = move_to_device(batch["encoded"], args.device)
            labels = batch["labels"].to(args.device)
            with torch.cuda.amp.autocast(enabled=args.fp16 and args.device.startswith("cuda")):
                logits = model(**encoded).logits
                train_logits = logits
                if args.calibration_alpha > 0:
                    pressure_encoded = move_to_device(batch["pressure_encoded"], args.device)
                    pressure_logits = model(**pressure_encoded).logits
                    if args.detach_calibration_prior:
                        pressure_logits = pressure_logits.detach()
                    train_logits = logits - args.calibration_alpha * pressure_logits
                ce_loss = F.cross_entropy(train_logits, labels)
                consistency = pair_consistency_loss(train_logits, batch["base_ids"])
                loss = ce_loss + args.consistency_weight * consistency
                loss = loss / args.grad_accum_steps

            scaler.scale(loss).backward()
            should_step = step % args.grad_accum_steps == 0 or step == len(train_loader)
            if should_step:
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                scaler.step(optimizer)
                scaler.update()
                scheduler.step()
                optimizer.zero_grad(set_to_none=True)
                global_step += 1
            progress.set_postfix({"loss": f"{float(loss.detach().cpu()):.4f}"})

        probs = predict_probs(model, tokenizer, valid_records, args)
        valid_predictions = [
            {**record, "prob_unsafe": prob, "prediction": "unsafe" if prob >= 0.5 else "safe"}
            for record, prob in zip(valid_records, probs)
        ]
        report = evaluate_records(valid_predictions)
        write_metric_report(output_dir / f"epoch_{epoch}", report)
        f1 = report.get("overall", {}).get("f1", 0.0)
        if f1 > best_f1:
            best_f1 = f1
            model.save_pretrained(output_dir / "best")
            tokenizer.save_pretrained(output_dir / "best")

    model.save_pretrained(output_dir / "last")
    tokenizer.save_pretrained(output_dir / "last")
    (output_dir / "train_args.txt").write_text(str(vars(args)) + "\n", encoding="utf-8")
    print(f"Training complete. Best validation F1={best_f1:.4f}. Saved to {output_dir}")


if __name__ == "__main__":
    main()
