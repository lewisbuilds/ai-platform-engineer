# Container Analysis Workflow (v1)

1. Validate that the Dockerfile path exists.
2. Execute local analysis with `aci --dockerfile <path>`.
3. If report file output is needed, add `--output <file>`.
4. Review findings ordered by severity and location.
5. Run targeted tests when logic or CLI behavior changes:
   - `pytest tests/unit/test_dockerfile_review.py tests/unit/test_pipeline.py tests/integration/test_cli_local.py`
6. Use full `pytest` when model contracts or report normalization changes.
