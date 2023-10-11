import apache_beam as beam

import os
import sys
import ursgal
import ursgal.uhelpers.beam as ubeam
from send_email import render_template, send_email

# import logging
# import os
# import tempfile


def main(argv=None, save_main_session=True):
    """
    Runs CytoCluster flow cytometry pipeline.

    Args:
        input_json (str): path to configuration json file

    Returns:
        None
    """
    # pipeline_options, urd, input_json = ubeam.parse_inputs(
    #     argv=argv, save_main_session=save_main_session
    # )


    input_json = {}
    input_json["requesterName"] = "Kavi"
    input_json["resultRecipient"] = [{"email":"kavi.seewoogoolam@gmail.com"}, {"email":"kavi@seewoogoolam.com"}]
    input_json["requesterEmail"] = "kavi.x.seewoogoolam@gsk.com"
    input_json["wid"] = "u_noisy_trade_conceives_majestic_eyes"
    input_json["fcs_files"] = ["file1","file2","file3","file4"]
    input_json["myLabDataTaskId"] = '23-10001016-H6'






    name = input_json["requesterName"]
    fcs_files = ', '.join(input_json["fcs_files"])
    wid = input_json["wid"]
    html = render_template('start.html', **locals())

    recipients = (
        [i["email"] for i in input_json["resultRecipient"]]
        if 'requesterEmail' in input_json
        else []
    )
    recipients.append(input_json["requesterEmail"])
    send_email(
        recipients, 
        cc="", 
        bcc="", 
        subject=input_json["myLabDataTaskId"] + " - Pipeline Started", 
        body=html
    ) 


    os.remove(sys.argv[1].split("=")[1])
    os.remove(__file__)


    ############################


    html = render_template('end.html', **locals())

    recipients = (
        [i["email"] for i in input_json["resultRecipient"]]
        if 'requesterEmail' in input_json
        else []
    )
    recipients.append(input_json["requesterEmail"])
    send_email(
        recipients, 
        cc="", 
        bcc="", 
        subject=input_json["myLabDataTaskId"] + " - Pipeline Completed", 
        body=html
    ) 

    # with beam.Pipeline(options=pipeline_options) as search_pipeline:
    #     fcs_pcol = search_pipeline | "Create FCS input" >> beam.Create(
    #         [
    #             (f"fcs_{i}", [fastq])
    #             for i, fastq in enumerate(input_json["files"]["fcs"])
    #         ]
    #     )
    #     qced_fcs_pcol = (
    #         fcs_pcol
    #         | "CytoCluster QC: Perform QC (PeacoQC, flowAI)"
    #         >> beam.ParDo(
    #             ubeam.UrsgalNodeExecutor(
    #                 unode="cytocluster_qc_1_2_0",
    #                 urd=urd,
    #                 ucredentials=input_json["credentials_lookup"],
    #                 config=input_json["config"],
    #             )
    #         )
    #     )
    #     annotated_fcs_pcol = qced_fcs_pcol | "Filter annotated FCS files" >> beam.ParDo(
    #         ubeam.FilterByUftype(),
    #         uftypes=[ursgal.uftypes.flow_cytometry.FCS],
    #         mode="keep",
    #     )
    #     annotated_renamed_pcol = (
    #         annotated_fcs_pcol
    #         | "Export annotated FCS"
    #         >> beam.ParDo(
    #             ubeam.OutputRenamer(),
    #             source_pcol=beam.pvalue.AsList(fcs_pcol),
    #             prefix="ursgal_new/",
    #             suffix="_annotated.fcs",
    #         )
    #     )
    #     flowcut_urd = ursgal.URunDict(
    #         {
    #             "parameters": {"pandas_query_string": "`flowCut_passed` == 1."},
    #             "unode_parameters": urd.unode_parameters,
    #         }
    #     )
    #     flowcut_urd.wid = urd.wid
    #     flowcut_fcs_pcol = qced_fcs_pcol | "Extract flowCut FCS" >> beam.ParDo(
    #         ubeam.UrsgalNodeExecutor(
    #             unode="filter_fcs_1_0_1",
    #             urd=flowcut_urd,
    #             ucredentials=input_json["credentials_lookup"],
    #             config=input_json["config"],
    #         )
    #     )
    #     flowcut_renamed_pcol = flowcut_fcs_pcol | "Export flowCut FCS" >> beam.ParDo(
    #         ubeam.OutputRenamer(),
    #         source_pcol=beam.pvalue.AsList(fcs_pcol),
    #         prefix="ursgal_new/",
    #         suffix="_flowcut.fcs",
    #     )
    #     flowai_urd = ursgal.URunDict(
    #         {
    #             "parameters": {"pandas_query_string": "`flowAI_passed` == 1."},
    #             "unode_parameters": urd.unode_parameters,
    #         }
    #     )
    #     flowai_urd.wid = urd.wid
    #     flowai_fcs_pcol = qced_fcs_pcol | "Extract flowAI FCS" >> beam.ParDo(
    #         ubeam.UrsgalNodeExecutor(
    #             unode="filter_fcs_1_0_1",
    #             urd=flowai_urd,
    #             ucredentials=input_json["credentials_lookup"],
    #             config=input_json["config"],
    #         )
    #     )
    #     flowai_renamed_pcol = flowai_fcs_pcol | "Export flowAI FCS" >> beam.ParDo(
    #         ubeam.OutputRenamer(),
    #         source_pcol=beam.pvalue.AsList(fcs_pcol),
    #         prefix="ursgal_new/",
    #         suffix="_flowai.fcs",
    #     )
    #     peacoqc_urd = ursgal.URunDict(
    #         {
    #             "parameters": {"pandas_query_string": "`peacoQC_passed` == 1."},
    #             "unode_parameters": urd.unode_parameters,
    #         }
    #     )
    #     peacoqc_urd.wid = urd.wid
    #     peacoqc_fcs_pcol = qced_fcs_pcol | "Extract peacoQC FCS" >> beam.ParDo(
    #         ubeam.UrsgalNodeExecutor(
    #             unode="filter_fcs_1_0_1",
    #             urd=peacoqc_urd,
    #             ucredentials=input_json["credentials_lookup"],
    #             config=input_json["config"],
    #         )
    #     )
    #     peacoqc_renamed_pcol = peacoqc_fcs_pcol | "Export peacoQC FCS" >> beam.ParDo(
    #         ubeam.OutputRenamer(),
    #         source_pcol=beam.pvalue.AsList(fcs_pcol),
    #         prefix="ursgal_new/",
    #         suffix="_peacoQC.fcs",
    #     )

    #     flat_qced_fcs_pcol = qced_fcs_pcol | "Group QC results" >> beam.CombineGlobally(
    #         ubeam.flatten_to_list
    #     )
    #     summary_qc_pcol = flat_qced_fcs_pcol | "CytoCluster QC Summary" >> beam.ParDo(
    #         ubeam.UrsgalNodeExecutor(
    #             unode="cytocluster_qc_summary_1_2_0",
    #             urd=urd,
    #             ucredentials=input_json["credentials_lookup"],
    #             config=input_json["config"],
    #         )
    #     )




if __name__ == "__main__":
    main()
