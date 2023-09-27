import apache_beam as beam

import ursgal
import ursgal.uhelpers.beam as ubeam


def main(argv=None, save_main_session=True):
    """
    Runs CytoCluster flow cytometry pipeline.

    Args:
        input_json (str): path to configuration json file

    Returns:
        None
    """
    pipeline_options, urd, input_json = ubeam.parse_inputs(
        argv=argv, save_main_session=save_main_session
    )
    with beam.Pipeline(options=pipeline_options) as search_pipeline:
        fcs_pcol = search_pipeline | "Create FCS input" >> beam.Create(
            [
                (f"fcs_{i}", [fastq])
                for i, fastq in enumerate(input_json["files"]["fcs"])
            ]
        )
        gating_strat_pcol = (
            search_pipeline
            | "Create gating strategy input"
            >> beam.Create(
                [
                    (f"gating_strat_{i}", [fastq])
                    for i, fastq in enumerate(
                        input_json["files"]["gating_strategy_csv"]
                    )
                ]
            )
        )
        qced_fcs_pcol = (
            fcs_pcol
            | "CytoCluster QC: Perform QC (PeacoQC, flowAI)"
            >> beam.ParDo(
                ubeam.UrsgalNodeExecutor(
                    unode="cytocluster_qc_1_2_0",
                    urd=urd,
                    ucredentials=input_json["credentials_lookup"],
                    config=input_json["config"],
                )
            )
        )
        annotated_fcs_pcol = qced_fcs_pcol | "Filter annotated FCS files" >> beam.ParDo(
            ubeam.FilterByUftype(),
            uftypes=[ursgal.uftypes.flow_cytometry.FCS],
            mode="keep",
        )
        # annotated_renamed_pcol = (
        #     annotated_fcs_pcol
        #     | "Export annotated FCS"
        #     >> beam.ParDo(
        #         ubeam.OutputRenamer(),
        #         source_pcol=beam.pvalue.AsList(annotated_fcs_pcol),
        #         prefix="ursgal_new/",
        #         suffix="_annotated.fcs",
        #     )
        # )
        flowcut_urd = ursgal.URunDict(
            {
                "parameters": {"pandas_query_string": "`flowCut_passed` == 1."},
                "unode_parameters": urd.unode_parameters,
            }
        )
        flowcut_urd.wid = urd.wid
        flowcut_fcs_pcol = qced_fcs_pcol | "Extract flowCut FCS" >> beam.ParDo(
            ubeam.UrsgalNodeExecutor(
                unode="filter_fcs_1_0_1",
                urd=flowcut_urd,
                ucredentials=input_json["credentials_lookup"],
                config=input_json["config"],
            )
        )
        # flowcut_renamed_pcol = flowcut_fcs_pcol | "Export flowCut FCS" >> beam.ParDo(
        #     ubeam.OutputRenamer(),
        #     source_pcol=beam.pvalue.AsList(qced_fcs_pcol),
        #     prefix="ursgal_new/",
        #     suffix="_flowcut.fcs",
        # )
        flowai_urd = ursgal.URunDict(
            {
                "parameters": {"pandas_query_string": "`flowAI_passed` == 1."},
                "unode_parameters": urd.unode_parameters,
            }
        )
        flowai_urd.wid = urd.wid
        flowai_fcs_pcol = qced_fcs_pcol | "Extract flowAI FCS" >> beam.ParDo(
            ubeam.UrsgalNodeExecutor(
                unode="filter_fcs_1_0_1",
                urd=flowai_urd,
                ucredentials=input_json["credentials_lookup"],
                config=input_json["config"],
            )
        )
        # flowai_renamed_pcol = flowai_fcs_pcol | "Export flowAI FCS" >> beam.ParDo(
        #     ubeam.OutputRenamer(),
        #     source_pcol=beam.pvalue.AsList(qced_fcs_pcol),
        #     prefix="ursgal_new/",
        #     suffix="_flowai.fcs",
        # )
        peacoqc_urd = ursgal.URunDict(
            {
                "parameters": {"pandas_query_string": "`peacoQC_passed` == 1."},
                "unode_parameters": urd.unode_parameters,
            }
        )
        peacoqc_urd.wid = urd.wid
        peacoqc_fcs_pcol = qced_fcs_pcol | "Extract peacoQC FCS" >> beam.ParDo(
            ubeam.UrsgalNodeExecutor(
                unode="filter_fcs_1_0_1",
                urd=peacoqc_urd,
                ucredentials=input_json["credentials_lookup"],
                config=input_json["config"],
            )
        )
        # peacoqc_renamed_pcol = peacoqc_fcs_pcol | "Export peacoQC FCS" >> beam.ParDo(
        #     ubeam.OutputRenamer(),
        #     source_pcol=beam.pvalue.AsList(qced_fcs_pcol),
        #     prefix="ursgal_new/",
        #     suffix="_peacoQC.fcs",
        # )

        flat_qced_fcs_pcol = qced_fcs_pcol | "Group QC results" >> beam.CombineGlobally(
            ubeam.flatten_to_list
        )
        summary_qc_pcol = flat_qced_fcs_pcol | "CytoCluster QC Summary" >> beam.ParDo(
            ubeam.UrsgalNodeExecutor(
                unode="cytocluster_qc_summary_1_2_0",
                urd=urd,
                ucredentials=input_json["credentials_lookup"],
                config=input_json["config"],
            )
        )


if __name__ == "__main__":
    main()