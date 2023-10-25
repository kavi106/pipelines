from prefect import flow, unmapped
import ursgal
from ursgal.uhelpers.prefect import run_unode, parse_inputs


@flow(name="TecQC Pipeline", flow_run_name="ursgal-{urd.wid}")
def run_pipeline(urd, input_json):
    qced_fcs_files = run_unode.with_options(name="CytoCluster QC 1.2.0").map(
        input_json["files"]["fcs"], unmapped(urd), unmapped("cytocluster_qc_1_2_0")
    )
    query_strings = (
        "`flowAI_passed` == 1.",
        "`flowCut_passed` == 1.",
        "`peacoQC_passed` == 1.",
    )
    for qs in query_strings:
        custom_urd = ursgal.URunDict(
            {
                "parameters": {"pandas_query_string": qs},
                "unode_parameters": urd.unode_parameters,
            }
        )
        custom_urd.wid = urd.wid
        filter_per_run = run_unode.with_options(
            name=f"Filter FCS {qs.split('_')[0].rstrip('`')}"
        ).map(qced_fcs_files, unmapped(custom_urd), unmapped("filter_fcs_1_0_1"))
    filter_all = run_unode.with_options(name="CytoCluster QC Summary 1.2.0")(
        qced_fcs_files, urd, "cytocluster_qc_summary_1_2_0"
    )
    return None


if __name__ == "__main__":
    urd, input_json = parse_inputs(
        {
            "files": {
                "fcs": [
                    "azure://a-launch-i.gsk.com/fcs-test?uftype=.flow_cytometry.fcs#20230627_20230123-ICS-14dPII_A05_070.fcs"
                ]
            },
            "config": {
                "hash_algorithm": "md5",
                "logging_level": "INFO",
                "certificates": {"mylabdata-files.uat.corpnet2.com": False},
                "umeta": "sqlite3",
            },
            "urun_dict": {
                "parameters": {},
                "unode_parameters": {},
            },
            "pipeline_configuration": {},
        },
    )
    run_pipeline(urd, input_json)
