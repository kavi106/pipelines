import asyncio
from prefect import flow, unmapped, tags, get_client

import ursgal
from ursgal.uhelpers.prefect import run_unode, simplify_output_names


async def create_concurency_limit(tag, limit):
    async with get_client() as client:
        limit_id = await client.create_concurrency_limit(
            tag=tag, concurrency_limit=limit
        )
    return limit_id


async def delete_concurrency_limit(flow, flow_run, state):
    tag = flow_run.name.replace("ursgal-", "parallelism_")
    async with get_client() as client:
        await client.delete_concurrency_limit_by_tag(tag=tag)
    return None


@flow(
    name="TecQC Pipeline",
    flow_run_name="ursgal-{wid}",
    on_crashed=[delete_concurrency_limit],
    on_failure=[delete_concurrency_limit],
    on_completion=[delete_concurrency_limit],
    on_cancellation=[delete_concurrency_limit],
)
def run_pipeline(wid, input_json):
    urd = ursgal.URunDict(input_json["urun_dict"])
    urd.wid = wid
    loop = asyncio.get_event_loop()
    loop.run_until_complete(create_concurency_limit(tag=f"parallelism_{wid}", limit=30))
    loop.close()
    creds = input_json.get("credentials_lookup", {})
    config = input_json.get("config", {})
    original_storage_base = ursgal.UFile(
        uri=input_json["files"]["fcs"][0]
    ).as_storage_base_uri()
    with tags(f"parallelism_{wid}"):
        qced_fcs_files = run_unode.with_options(name="CytoCluster QC 1.2.3").map(
            input_json["files"]["fcs"],
            unmapped(urd),
            unmapped("cytocluster_qc_1_2_3"),
            unmapped(creds),
            unmapped(config),
        )
        outputs = simplify_output_names.with_options(
            name=f"Upload annotated FCSs to MyLabData"
        ).map(
            qced_fcs_files,
            unmapped(creds),
            unmapped(config),
            unmapped(input_json["files"]["fcs"]),
            unmapped("ursgal/"),
            unmapped("_annotated.fcs"),
            unmapped(original_storage_base),
        )
        query_strings = (
            "`flowAI_passed` == 1.",
            "`flowCut_passed` == 1.",
            "`peacoQC_passed` == 1.",
        )
        for qs in query_strings:
            engine_name = qs.split("_")[0].rstrip("`")[1:]
            custom_urd = ursgal.URunDict(
                {
                    "parameters": {"pandas_query_string": qs},
                    "unode_parameters": urd.unode_parameters,
                }
            )
            custom_urd.wid = urd.wid
            filter_per_run = run_unode.with_options(
                name=f"Filter FCS {engine_name}"
            ).map(
                qced_fcs_files,
                unmapped(custom_urd),
                unmapped("filter_fcs_1_0_1"),
                unmapped(creds),
                unmapped(config),
            )
            outputs = simplify_output_names.with_options(
                name=f"Upload {engine_name} FCSs to MyLabData"
            ).map(
                filter_per_run,
                unmapped(creds),
                unmapped(config),
                unmapped(input_json["files"]["fcs"]),
                unmapped("ursgal/"),
                unmapped(f"_{engine_name}.fcs"),
                unmapped(original_storage_base),
            )
    filter_all = run_unode.with_options(name="CytoCluster QC Summary 1.2.3").map(
        [qced_fcs_files],
        unmapped(urd),
        unmapped("cytocluster_qc_summary_1_2_3"),
        unmapped(creds),
        unmapped(config),
    )
    return None
