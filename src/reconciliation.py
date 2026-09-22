"""Formula-based Excel reconciliation workbooks for illustrative acquisition cases."""
from __future__ import annotations

from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from .atlasre import DealInputs, underwrite_deal
from .governance import default_lineage, model_run_fingerprint, versioned_assumptions

ILLUSTRATIVE_NOTE = "ILLUSTRATIVE — replace all inputs with source-backed values before relying on any output."
_HEADER_FILL = PatternFill("solid", fgColor="17324D")
_SUBHEADER_FILL = PatternFill("solid", fgColor="DCE6F1")


def _title(sheet, title: str, columns: int) -> None:
    sheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=columns)
    cell = sheet.cell(1, 1, f"ILLUSTRATIVE — {title}")
    cell.font = Font(bold=True, color="FFFFFF", size=12)
    cell.fill = _HEADER_FILL
    cell.alignment = Alignment(horizontal="left")
    sheet.freeze_panes = "A4"


def _header(sheet, row: int, values: list[str]) -> None:
    for column, value in enumerate(values, start=1):
        cell = sheet.cell(row, column, value)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = _HEADER_FILL
        cell.alignment = Alignment(horizontal="center")


def _format_columns(sheet, formats: dict[int, str], start: int, end: int) -> None:
    for column, number_format in formats.items():
        for row in range(start, end + 1):
            sheet.cell(row, column).number_format = number_format


def _fit_columns(sheet, widths: dict[int, float]) -> None:
    for column, width in widths.items():
        sheet.column_dimensions[get_column_letter(column)].width = width


def _input_rows(
    deal: DealInputs,
    hurdle_rate: float,
    model_version: str,
    fingerprint: str,
    source_status: str,
) -> list[tuple[str, object, str]]:
    return [
        ("Purchase price", deal.purchase_price, "USD"),
        ("Annual NOI (year 1)", deal.annual_noi, "USD / year"),
        ("Hold years", deal.hold_years, "years"),
        ("Annual NOI growth", deal.annual_noi_growth, "decimal"),
        ("Exit cap rate", deal.exit_cap_rate, "decimal"),
        ("Discount rate", deal.discount_rate, "decimal"),
        ("Acquisition cost", deal.acquisition_cost_pct, "decimal"),
        ("Selling cost", deal.selling_cost_pct, "decimal"),
        ("Leverage", deal.leverage, "decimal"),
        ("Debt rate", deal.debt_rate, "decimal"),
        ("Debt amortization", deal.debt_amortization_years, "years"),
        ("IRR hurdle", hurdle_rate, "decimal; not a core model input"),
        ("Model version", model_version, "text"),
        ("Run fingerprint", fingerprint, "text"),
        ("Source status", source_status, "ILLUSTRATIVE unless independently verified"),
    ]


def build_reconciliation_workbook(
    deal: DealInputs,
    hurdle_rate: float = 0.12,
    model_version: str = "deterministic-core-v0.10",
    source_status: str = "REVIEW REQUIRED",
    deal_id: str = "ATLAS-001",
) -> bytes:
    """Build an XLSX file with live Excel formulas and Python reconciliation values.

    The workbook mirrors the annual acquisition conventions in ``underwrite_deal``:
    year-one NOI is supplied directly, growth starts in year two, terminal value
    uses final-year NOI divided by exit cap, and debt amortizes monthly. Formula
    cells calculate the model route; the adjacent static columns exist only to
    reconcile the workbook back to the Python output.
    """
    if not 0 <= hurdle_rate <= 1:
        raise ValueError("hurdle_rate must be between 0 and 1")
    result = underwrite_deal(deal)
    assumptions = versioned_assumptions(
        {
            "purchase_price": (deal.purchase_price, "USD"),
            "annual_noi": (deal.annual_noi, "USD / year"),
            "annual_noi_growth": (deal.annual_noi_growth, "%"),
            "exit_cap_rate": (deal.exit_cap_rate, "%"),
            "discount_rate": (deal.discount_rate, "%"),
            "acquisition_cost_pct": (deal.acquisition_cost_pct, "%"),
            "selling_cost_pct": (deal.selling_cost_pct, "%"),
            "leverage": (deal.leverage, "%"),
            "debt_rate": (deal.debt_rate, "%"),
            "debt_amortization_years": (deal.debt_amortization_years, "years"),
            "irr_hurdle": (hurdle_rate, "%"),
        },
        deal_id=deal_id,
        version=1,
        source="Illustrative reconciliation workbook",
    )
    lineage = default_lineage()
    fingerprint = model_run_fingerprint(model_version, assumptions, lineage)

    workbook = Workbook()
    workbook.calculation.fullCalcOnLoad = True
    workbook.calculation.forceFullCalc = True
    control = workbook.active
    control.title = "Control"
    inputs = workbook.create_sheet("Inputs")
    annual_noi = workbook.create_sheet("Annual NOI")
    debt_schedule = workbook.create_sheet("Debt Schedule")
    cash_flows = workbook.create_sheet("Cash Flows")
    reconciliation = workbook.create_sheet("Reconciliation")
    lineage_sheet = workbook.create_sheet("Lineage")

    _title(control, "Workbook control", 3)
    control["A3"] = ILLUSTRATIVE_NOTE
    control["A4"] = "Purpose"
    control["B4"] = "Formula-based reconciliation of the current AtlasRE acquisition case."
    control["A5"] = "Calculation"
    control["B5"] = "Open in Excel or LibreOffice to recalculate live formulas before review."
    control["A6"] = "Model version"
    control["B6"] = model_version
    control["A7"] = "Run fingerprint"
    control["B7"] = fingerprint
    control["A8"] = "Source status"
    control["B8"] = source_status
    control["A9"] = "Workbook scope"
    control["B9"] = "Acquisition underwriting only; no tax, refinancing, lease, or market-data model."
    _fit_columns(control, {1: 22, 2: 106, 3: 18})

    _title(inputs, "Inputs", 3)
    _header(inputs, 3, ["Input", "Workbook value", "Unit / note"])
    for row, values in enumerate(_input_rows(deal, hurdle_rate, model_version, fingerprint, source_status), start=4):
        for column, value in enumerate(values, start=1):
            inputs.cell(row, column, value)
    _format_columns(
        inputs,
        {2: '$#,##0.00;[Red]-$#,##0.00', 3: '@'},
        4,
        5,
    )
    for row in [7, 14, 15, 16]:
        inputs.cell(row, 2).number_format = "0.0%"
    inputs["B6"].number_format = "0"
    inputs["B13"].number_format = "0"
    _fit_columns(inputs, {1: 28, 2: 30, 3: 45})

    _title(annual_noi, "Annual NOI and terminal value", 7)
    _header(
        annual_noi,
        3,
        ["Year", "NOI", "Exit value", "Selling cost", "Unlevered operating CF", "Debt service", "DSCR"],
    )
    annual_start = 4
    annual_end = annual_start + deal.hold_years - 1
    monthly_end = 3 + deal.hold_years * 12
    for row in range(annual_start, annual_end + 1):
        year = row - annual_start + 1
        annual_noi.cell(row, 1, year)
        annual_noi.cell(row, 2, f"=Inputs!$B$5*(1+Inputs!$B$7)^(A{row}-1)")
        annual_noi.cell(row, 3, f"=IF(A{row}=Inputs!$B$6,B{row}/Inputs!$B$8,0)")
        annual_noi.cell(row, 4, f"=C{row}*Inputs!$B$11")
        annual_noi.cell(row, 5, f"=B{row}+C{row}-D{row}")
        annual_noi.cell(
            row,
            6,
            f"=SUMIFS('Debt Schedule'!$F$4:$F${monthly_end},'Debt Schedule'!$B$4:$B${monthly_end},A{row})",
        )
        annual_noi.cell(row, 7, f'=IF(F{row}=0,"",B{row}/F{row})')
    _format_columns(annual_noi, {2: '$#,##0.00', 3: '$#,##0.00', 4: '$#,##0.00', 5: '$#,##0.00', 6: '$#,##0.00', 7: '0.00x'}, annual_start, annual_end)
    _fit_columns(annual_noi, {1: 10, 2: 18, 3: 18, 4: 18, 5: 25, 6: 18, 7: 12})

    _title(debt_schedule, "Monthly debt schedule", 10)
    _header(
        debt_schedule,
        3,
        [
            "Month",
            "Year",
            "Beginning balance",
            "Monthly rate",
            "Interest (IPMT)",
            "Payment (PMT)",
            "Principal (PPMT)",
            "Ending balance",
            "Balloon payoff",
            "Annual debt service",
        ],
    )
    for row in range(4, monthly_end + 1):
        month = row - 3
        debt_schedule.cell(row, 1, month)
        debt_schedule.cell(row, 2, f"=ROUNDUP(A{row}/12,0)")
        debt_schedule.cell(row, 3, "=Inputs!$B$4*Inputs!$B$12" if row == 4 else f"=H{row - 1}")
        debt_schedule.cell(row, 4, "=Inputs!$B$13/12")
        debt_schedule.cell(row, 5, f"=IF(A{row}<=Inputs!$B$14*12,-IPMT(D{row},A{row},Inputs!$B$14*12,Inputs!$B$4*Inputs!$B$12),0)")
        debt_schedule.cell(row, 6, f"=IF(A{row}<=Inputs!$B$14*12,-PMT(D{row},Inputs!$B$14*12,Inputs!$B$4*Inputs!$B$12),0)")
        debt_schedule.cell(row, 7, f"=IF(A{row}<=Inputs!$B$14*12,-PPMT(D{row},A{row},Inputs!$B$14*12,Inputs!$B$4*Inputs!$B$12),0)")
        debt_schedule.cell(row, 8, f"=MAX(0,C{row}-G{row})")
        debt_schedule.cell(row, 9, f"=IF(A{row}=Inputs!$B$6*12,H{row},0)")
        debt_schedule.cell(row, 10, f"=SUMIFS($F$4:$F${monthly_end},$B$4:$B${monthly_end},B{row})")
    _format_columns(
        debt_schedule,
        {3: '$#,##0.00', 4: '0.0000%', 5: '$#,##0.00', 6: '$#,##0.00', 7: '$#,##0.00', 8: '$#,##0.00', 9: '$#,##0.00', 10: '$#,##0.00'},
        4,
        monthly_end,
    )
    _fit_columns(debt_schedule, {1: 10, 2: 10, 3: 20, 4: 14, 5: 18, 6: 18, 7: 20, 8: 20, 9: 18, 10: 22})

    _title(cash_flows, "Annual levered and unlevered cash flows", 4)
    _header(cash_flows, 3, ["Period", "Unlevered cash flow", "Levered cash flow", "Detail"])
    cash_start = 4
    cash_end = cash_start + deal.hold_years
    for row in range(cash_start, cash_end + 1):
        period = row - cash_start
        cash_flows.cell(row, 1, period)
        if period == 0:
            cash_flows.cell(row, 2, "=-Inputs!$B$4*(1+Inputs!$B$10)")
            cash_flows.cell(row, 3, "=B4+Inputs!$B$4*Inputs!$B$12")
            cash_flows.cell(row, 4, "Acquisition and initial equity")
        else:
            annual_row = annual_start + period - 1
            cash_flows.cell(row, 2, f"='Annual NOI'!E{annual_row}")
            cash_flows.cell(row, 3, f"=B{row}-'Annual NOI'!F{annual_row}")
            if period == deal.hold_years:
                cash_flows.cell(row, 3, f"=B{row}-'Annual NOI'!F{annual_row}-'Debt Schedule'!I{monthly_end}")
            cash_flows.cell(row, 4, f"Year {period}")
    metrics_start = cash_end + 2
    cash_flows.cell(metrics_start, 1, "Unlevered IRR")
    cash_flows.cell(metrics_start, 2, f"=IRR(B{cash_start}:B{cash_end})")
    cash_flows.cell(metrics_start + 1, 1, "Levered IRR")
    cash_flows.cell(metrics_start + 1, 2, f"=IRR(C{cash_start}:C{cash_end})")
    cash_flows.cell(metrics_start + 2, 1, "Unlevered NPV")
    cash_flows.cell(metrics_start + 2, 2, f"=B{cash_start}+NPV(Inputs!$B$9,B{cash_start + 1}:B{cash_end})")
    cash_flows.cell(metrics_start + 3, 1, "Equity multiple")
    cash_flows.cell(metrics_start + 3, 2, f'=SUMIF(C{cash_start}:C{cash_end},">0",C{cash_start}:C{cash_end})/-SUMIF(C{cash_start}:C{cash_end},"<0",C{cash_start}:C{cash_end})')
    for row in range(metrics_start, metrics_start + 4):
        cash_flows.cell(row, 1).font = Font(bold=True)
        cash_flows.cell(row, 2).fill = _SUBHEADER_FILL
    _format_columns(cash_flows, {2: '$#,##0.00', 3: '$#,##0.00'}, cash_start, cash_end)
    cash_flows.cell(metrics_start, 2).number_format = "0.00%"
    cash_flows.cell(metrics_start + 1, 2).number_format = "0.00%"
    cash_flows.cell(metrics_start + 2, 2).number_format = '$#,##0.00;[Red]-$#,##0.00'
    cash_flows.cell(metrics_start + 3, 2).number_format = "0.00x"
    _fit_columns(cash_flows, {1: 20, 2: 23, 3: 23, 4: 32})

    _title(reconciliation, "Formula-to-model reconciliation", 5)
    reconciliation["A2"] = "Difference is workbook formula less static Python model output. Amounts should be approximately zero after recalculation."
    _header(reconciliation, 3, ["Metric", "Excel formula result", "Model output", "Difference", "Tolerance"])
    output_rows: list[tuple[str, str, float, str]] = [
        ("Entry cap rate", "=Inputs!$B$5/Inputs!$B$4", float(result["entry_cap_rate"]), "0.00000001"),
        ("Exit value", f"='Annual NOI'!C{annual_end}", float(result["exit_value"]), "0.01"),
        ("Remaining debt at exit", f"='Debt Schedule'!H{monthly_end}", float(result["remaining_debt_at_exit"]), "0.01"),
        ("Minimum DSCR", f"=MIN('Annual NOI'!G{annual_start}:G{annual_end})", float(result["minimum_dscr"]), "0.00000001"),
        ("Unlevered IRR", f"='Cash Flows'!B{metrics_start}", float(result["unlevered_irr"]), "0.00000001"),
        ("Levered IRR", f"='Cash Flows'!B{metrics_start + 1}", float(result["levered_irr"]), "0.00000001"),
        ("Unlevered NPV", f"='Cash Flows'!B{metrics_start + 2}", float(result["unlevered_npv"]), "0.01"),
        ("Equity multiple", f"='Cash Flows'!B{metrics_start + 3}", float(result["equity_multiple"]), "0.00000001"),
    ]
    for row, (metric, formula, model_output, tolerance) in enumerate(output_rows, start=4):
        reconciliation.cell(row, 1, metric)
        reconciliation.cell(row, 2, formula)
        reconciliation.cell(row, 3, model_output)
        reconciliation.cell(row, 4, f"=B{row}-C{row}")
        reconciliation.cell(row, 5, float(tolerance))
    _format_columns(reconciliation, {2: '0.00000000', 3: '0.00000000', 4: '0.00000000', 5: '0.00000000'}, 4, 11)
    for row in [5, 6, 10]:
        for column in [2, 3, 4, 5]:
            reconciliation.cell(row, column).number_format = '$#,##0.00;[Red]-$#,##0.00'
    for row in [4, 7, 8, 9]:
        for column in [2, 3, 4, 5]:
            reconciliation.cell(row, column).number_format = "0.00000000"
    reconciliation["F3"] = "Status"
    reconciliation["F3"].font = Font(bold=True, color="FFFFFF")
    reconciliation["F3"].fill = _HEADER_FILL
    for row in range(4, 12):
        reconciliation.cell(row, 6, f'=IF(ABS(D{row})<=E{row},"PASS","REVIEW")')
    _fit_columns(reconciliation, {1: 30, 2: 22, 3: 22, 4: 18, 5: 16, 6: 14})

    _title(lineage_sheet, "Assumption and lineage register", 7)
    _header(lineage_sheet, 3, list(assumptions.columns))
    for row_index, (_, row) in enumerate(assumptions.iterrows(), start=4):
        for column, value in enumerate(row.tolist(), start=1):
            lineage_sheet.cell(row_index, column, value)
    lineage_start = 4 + len(assumptions) + 2
    lineage_sheet.cell(lineage_start, 1, "Lineage records")
    lineage_sheet.cell(lineage_start, 1).font = Font(bold=True)
    lineage_headers = ["Output", "Value", "Inputs", "Method", "Source references", "Assumption version"]
    _header(lineage_sheet, lineage_start + 1, lineage_headers)
    for row_index, record in enumerate(lineage, start=lineage_start + 2):
        lineage_sheet.cell(row_index, 1, record["output"])
        lineage_sheet.cell(row_index, 2, str(record["value"]))
        lineage_sheet.cell(row_index, 3, ", ".join(record["inputs"]))
        lineage_sheet.cell(row_index, 4, record["method"])
        lineage_sheet.cell(row_index, 5, ", ".join(record["source_refs"]))
        lineage_sheet.cell(row_index, 6, record["assumption_version"])
    _fit_columns(lineage_sheet, {1: 28, 2: 30, 3: 38, 4: 50, 5: 32, 6: 20, 7: 28})

    for sheet in workbook.worksheets:
        sheet.sheet_view.showGridLines = False
        sheet.auto_filter.ref = sheet.dimensions
        sheet.freeze_panes = "A4"

    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


__all__ = ["ILLUSTRATIVE_NOTE", "build_reconciliation_workbook"]
