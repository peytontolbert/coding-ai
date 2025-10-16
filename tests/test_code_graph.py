from tools.code_graph import CodeGraph


def test_code_graph_builds():
    g = CodeGraph.load_or_build("./repo", ignore_cache=True)
    assert isinstance(g.indexed_files, list)
    assert isinstance(g.modules, dict)
    # Should at least scan zero or more files; existence of dict ensures build ran
    assert g.calls is not None
