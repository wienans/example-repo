from strictdoc.core.project_config import ProjectConfig


def create_config() -> ProjectConfig:
    return ProjectConfig(
        project_title="Motor control example",
        project_features=[
            "TABLE_SCREEN",
            "TRACEABILITY_SCREEN",
            "DEEP_TRACEABILITY_SCREEN",
            "REQUIREMENT_TO_SOURCE_TRACEABILITY",
            "PROJECT_STATISTICS_SCREEN",
            # make release prints the documents to PDF and the changes since
            # the previous release from the Diff screen.
            "HTML2PDF",
            "DIFF",
        ],
        # Colours the generated test results and coverage by status.
        custom_css_path="tools/strictdoc/site.css",
        include_doc_paths=["/docs/**"],
        exclude_doc_paths=["/docs/api/**"],
        source_root_path=".",
        include_source_paths=["/src/**", "/tests/unit/**", "/tools/**"],
    )
