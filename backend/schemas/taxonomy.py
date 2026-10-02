"""Fixed return-reason taxonomy. The model may return only these labels."""

from typing import Literal

Label = Literal[
    "fit_too_small",
    "fit_too_large",
    "fit_too_tight",
    "fit_too_loose",
    "size_chart_mismatch",
    "quality_fabric",
    "quality_stitching_or_damage",
    "colour_image_mismatch",
    "description_or_look_mismatch",
    "insufficient_evidence",
    "not_a_product_issue",
]

LABELS: tuple[Label, ...] = (
    "fit_too_small",
    "fit_too_large",
    "fit_too_tight",
    "fit_too_loose",
    "size_chart_mismatch",
    "quality_fabric",
    "quality_stitching_or_damage",
    "colour_image_mismatch",
    "description_or_look_mismatch",
    "insufficient_evidence",
    "not_a_product_issue",
)

LABEL_TITLES: dict[str, str] = {
    "fit_too_small": "Fit · too small",
    "fit_too_large": "Fit · too large",
    "fit_too_tight": "Fit · too tight",
    "fit_too_loose": "Fit · too loose",
    "size_chart_mismatch": "Fit · size chart",
    "quality_fabric": "Quality · fabric",
    "quality_stitching_or_damage": "Quality · stitch or damage",
    "colour_image_mismatch": "Colour · image mismatch",
    "description_or_look_mismatch": "Expectation · look or copy",
    "insufficient_evidence": "Not enough evidence",
    "not_a_product_issue": "Not a product issue",
}

AUTO_APPROVE_AT = 0.75

ACTIONS: dict[str, str] = {
    "fit_too_small": "Review this vendor’s size chart for this SKU.",
    "fit_too_large": "Review this vendor’s size chart for this SKU.",
    "fit_too_tight": "Review this vendor’s size chart for this SKU.",
    "fit_too_loose": "Review this vendor’s size chart for this SKU.",
    "size_chart_mismatch": "Review this vendor’s size chart for this SKU.",
    "colour_image_mismatch": "Compare the listing images with these quotes.",
    "quality_fabric": "Raise fabric with the vendor. Do not edit the listing automatically.",
    "quality_stitching_or_damage": "Raise stitch or damage with the vendor. Do not edit the listing automatically.",
    "description_or_look_mismatch": "Review the product copy against these quotes.",
    "insufficient_evidence": "No catalogue action.",
    "not_a_product_issue": "No catalogue action. This is delivery, a courier, or a wrong item.",
}


def suggested_action(label: str | None) -> str:
    if not label:
        return "No catalogue action until a person sets a label."
    return ACTIONS.get(label, "No catalogue action.")
