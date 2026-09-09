"""Real Great Expectations quality gate for the Silver Delta table."""

import json
from pathlib import Path

import great_expectations as gx
import great_expectations.expectations as gxe
from deltalake import DeltaTable


class DataQualityError(RuntimeError):
    """Raised only after a real GX validation result has been persisted."""


def _build_validation_definition():
    context = gx.get_context(mode="ephemeral")

    datasource = context.data_sources.add_pandas(name="aqualens_silver_dataframe")
    asset = datasource.add_dataframe_asset(name="aqualens_silver_water_distribution")
    batch_definition = asset.add_batch_definition_whole_dataframe("whole_silver_table")

    suite = gx.ExpectationSuite(name="aqualens_silver_quality_suite")
    suite = context.suites.add(suite)
    suite.add_expectation(gxe.ExpectTableRowCountToBeBetween(min_value=1))
    for column in ("year", "region", "source", "volume_m3"):
        suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column=column))
    suite.add_expectation(
        gxe.ExpectColumnValuesToBeBetween(column="volume_m3", min_value=0)
    )
    suite.add_expectation(
        gxe.ExpectCompoundColumnsToBeUnique(
            column_list=["year", "region", "source"]
        )
    )

    validation = gx.ValidationDefinition(
        name="aqualens_silver_quality_validation",
        data=batch_definition,
        suite=suite,
    )
    return context.validation_definitions.add(validation)


def validate_silver(silver_path: Path, evidence_path: Path) -> dict:
    """Validate Silver with real GX and fail hard after recording the result."""
    table = DeltaTable(str(silver_path))
    dataframe = table.to_pandas()

    validation = _build_validation_definition()
    result = validation.run(batch_parameters={"dataframe": dataframe})

    payload = result.to_json_dict()
    payload["aqualens"] = {
        "silver_path": str(silver_path),
        "row_count": int(len(dataframe)),
        "business_key": ["year", "region", "source"],
        "gate_success": bool(result.success),
    }

    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )

    failed = [row for row in payload.get("results", []) if not row.get("success")]
    summary = {
        "success": bool(result.success),
        "row_count": int(len(dataframe)),
        "failed_expectation_count": len(failed),
        "evidence_path": str(evidence_path),
    }
    print(json.dumps({"action": "gx_quality_gate", **summary}), flush=True)

    if not result.success:
        failed_types = [
            row.get("expectation_config", {}).get("type", "unknown")
            for row in failed
        ]
        raise DataQualityError(
            "Great Expectations quality gate failed: " + ", ".join(failed_types)
        )

    return summary
