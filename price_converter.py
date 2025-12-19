import re
from typing import Optional

import pandas as pd


class PriceConverter:
    def __init__(self, hh_df: pd.DataFrame, olx_df: pd.DataFrame):
        # Default conversion rate (UZS per 1 USD). Update if you need a newer rate.
        self.UZS_PER_USD = 12500
        self.TAX_RATE = 0.12  # 12% income tax
        self.hh_df = hh_df
        self.olx_df = olx_df

    def _extract_digits(self, value: str) -> Optional[int]:
        """Return the numeric part of the price string as an int, or None if missing."""
        digits_only = re.sub(r"[^\d]", "", value)
        return int(digits_only) if digits_only else None

    def price_to_usd(self, value) -> Optional[int]:
        """
        Convert a raw OLX price value to USD as an integer.
        Prices marked with 'сум' are treated as UZS; everything else is treated as USD.
        """
        if pd.isna(value):
            return None

        text = str(value).lower()
        amount = self._extract_digits(text)
        if amount is None:
            return None

        is_uzs = "сум" in text or "sum" in text
        if is_uzs:
            return int(round(amount / self.UZS_PER_USD))
        return amount

    def _avg_numeric_parts(self, text: str) -> Optional[int]:
        """Average numeric parts (handles ranges like 'от 3 000 до 4 000')."""
        numbers = re.findall(r"\d[\d\s]*", text)
        cleaned = [int(re.sub(r"[^\d]", "", n)) for n in numbers if re.sub(r"[^\d]", "", n)]
        if not cleaned:
            return None
        return int(round(sum(cleaned) / len(cleaned)))

    def salary_to_usd_after_tax(self, value) -> Optional[int]:
        """
        Convert HH salary text to USD after tax as an integer.
        - Detects currency by '$' (USD) vs 'so'm/сум' (UZS assumed).
        - If marked 'до вычета налогов' apply tax_rate deduction; otherwise keep as-is.
        - For ranges, uses the average of the numeric values.
        """
        if pd.isna(value):
            return None

        text = str(value)
        text_lower = text.lower()
        amount = self._avg_numeric_parts(text)
        if amount is None:
            return None

        is_pre_tax = "до вычета" in text_lower
        is_usd = "$" in text_lower or "usd" in text_lower or "y.e" in text_lower
        after_tax_amount = amount * (1 - self.TAX_RATE) if is_pre_tax else amount

        if not is_usd:
            after_tax_amount = after_tax_amount / self.UZS_PER_USD

        return int(round(after_tax_amount))

    def convert_olx_prices(self
                           ) -> pd.DataFrame:
        """
        Read OLX data, normalize the Price column to USD integers, and save to a new Excel file.
        Returns the converted DataFrame.
        """
        olx_df = self.olx_df
        olx_df["Price"] = (
            olx_df["Price"]
            .apply(lambda val: self.price_to_usd(val))
            .astype("Int64")
        )
        return olx_df

    def convert_hh_salaries(self
                            ) -> pd.DataFrame:
        """
        Read HH data, convert Salary to USD after-tax integers, and save to a new Excel file.
        Returns the converted DataFrame.
        """
        hh_df = self.hh_df
        hh_df["Salary"] = (
            hh_df["Salary"]
            .apply(lambda val: self.salary_to_usd_after_tax(val))
            .astype("Int64")
        )
        return hh_df

    def get_olx_data(self) -> pd.DataFrame:
        return self.convert_olx_prices()

    def get_hh_data(self) -> pd.DataFrame:
        return self.convert_hh_salaries()

