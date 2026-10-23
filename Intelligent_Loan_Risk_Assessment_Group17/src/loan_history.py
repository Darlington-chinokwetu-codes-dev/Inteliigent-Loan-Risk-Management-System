"""Aggregate historical loan outcomes for privacy-conscious portfolio charts."""

import csv
import math
from pathlib import Path

INCOME_BINS = 10
LOAN_BINS = 8
MIN_CELL_COUNT = 10
MIN_BAND_COUNT = 20
LOAN_TO_INCOME_BANDS = (
    (0.0, 0.2, "Under 20%"),
    (0.2, 0.4, "20 to <40%"),
    (0.4, 0.6, "40 to <60%"),
    (0.6, 0.8, "60 to <80%"),
    (0.8, math.inf, "80% or more"),
)


def load_loan_history(path: Path) -> dict:
    """Return aggregate portfolio patterns without returning individual records."""
    required_columns = {"person_income", "loan_amnt", "loan_status"}
    records = []

    with path.open(newline="", encoding="utf-8") as history_file:
        reader = csv.DictReader(history_file)
        missing_columns = required_columns - set(reader.fieldnames or ())
        if missing_columns:
            raise ValueError(
                "Historical loan data is missing required column(s): "
                + ", ".join(sorted(missing_columns))
            )

        for row_number, row in enumerate(reader, start=2):
            try:
                income = float(row["person_income"])
                loan_amount = float(row["loan_amnt"])
                loan_status_value = float(row["loan_status"])
            except (TypeError, ValueError) as error:
                raise ValueError(
                    f"Invalid historical loan data on row {row_number}."
                ) from error

            if (
                not math.isfinite(income)
                or not math.isfinite(loan_amount)
                or not math.isfinite(loan_status_value)
                or income <= 0
                or loan_amount <= 0
                or loan_status_value not in (0.0, 1.0)
            ):
                raise ValueError(
                    f"Invalid historical loan data on row {row_number}."
                )
            loan_status = int(loan_status_value)
            records.append((income, loan_amount, loan_status))

    if not records:
        raise ValueError(f"No historical loan records found in {path}.")

    log_incomes = [math.log10(record[0]) for record in records]
    log_loans = [math.log10(record[1]) for record in records]
    income_min, income_max = min(log_incomes), max(log_incomes)
    loan_min, loan_max = min(log_loans), max(log_loans)
    income_span = income_max - income_min
    loan_span = loan_max - loan_min

    cells = {}
    bands = [
        {"label": label, "loan_count": 0, "defaults": 0}
        for _, _, label in LOAN_TO_INCOME_BANDS
    ]
    defaults = 0

    for income, loan_amount, loan_status in records:
        income_position = (
            (math.log10(income) - income_min) / income_span
            if income_span
            else 0.5
        )
        loan_position = (
            (math.log10(loan_amount) - loan_min) / loan_span
            if loan_span
            else 0.5
        )
        income_bin = min(int(income_position * INCOME_BINS), INCOME_BINS - 1)
        loan_bin = min(int(loan_position * LOAN_BINS), LOAN_BINS - 1)
        cell = cells.setdefault(
            (income_bin, loan_bin), {"count": 0}
        )
        cell["count"] += 1

        loan_to_income = loan_amount / income
        for index, (lower, upper, _) in enumerate(LOAN_TO_INCOME_BANDS):
            if lower <= loan_to_income < upper:
                bands[index]["loan_count"] += 1
                bands[index]["defaults"] += loan_status
                break
        defaults += loan_status

    return {
        "record_count": len(records),
        "default_rate": round(defaults / len(records) * 100, 1),
        "income_min": 10**income_min,
        "income_max": 10**income_max,
        "loan_min": 10**loan_min,
        "loan_max": 10**loan_max,
        "cells": [
            {
                "x": (income_bin + 0.5) / INCOME_BINS,
                "y": (loan_bin + 0.5) / LOAN_BINS,
                "count": cell["count"],
            }
            for (income_bin, loan_bin), cell in cells.items()
            if cell["count"] >= MIN_CELL_COUNT
        ],
        "loan_to_income_bands": [
            {
                "label": band["label"],
                "loan_count": band["loan_count"],
                "default_rate": (
                    round(band["defaults"] / band["loan_count"] * 100, 1)
                    if band["loan_count"] >= MIN_BAND_COUNT
                    else None
                ),
            }
            for band in bands
        ],
    }


def chart_position(income: float, loan_amount: float, history: dict) -> dict:
    """Map the current applicant to the historical chart's log-scaled axes."""
    x_min, x_max = math.log10(history["income_min"]), math.log10(history["income_max"])
    y_min, y_max = math.log10(history["loan_min"]), math.log10(history["loan_max"])
    x_span, y_span = x_max - x_min, y_max - y_min
    x_value = (math.log10(income) - x_min) / x_span if x_span else 0.5
    y_value = (math.log10(loan_amount) - y_min) / y_span if y_span else 0.5
    return {
        "x": min(max(x_value, 0.0), 1.0),
        "y": min(max(y_value, 0.0), 1.0),
        "outside_history": not (0 <= x_value <= 1 and 0 <= y_value <= 1),
    }
