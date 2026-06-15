import networkx as nx
import pytest

from sagittarius import Register, SagittariusValidationError


def _coords(register):
    return [(atom.x, atom.y, atom.z) for atom in register.atoms]


def test_register_chain_constructor_records_topology():
    reg = Register.chain(4, spacing=0.5, C6=2.0, origin=(1.0, 2.0, 3.0), axis="x")

    assert _coords(reg) == [
        (1.0, 2.0, 3.0),
        (1.5, 2.0, 3.0),
        (2.0, 2.0, 3.0),
        (2.5, 2.0, 3.0),
    ]
    assert reg.C6 == 2.0
    assert reg.topology == {"kind": "chain", "n": 4, "spacing": 0.5, "axis": "x", "origin": [1.0, 2.0, 3.0]}


def test_register_square_lattice_constructor_uses_register_order():
    reg = Register.square_lattice(2, 3, spacing=2.0, plane="xy")

    assert _coords(reg) == [
        (0.0, 0.0, 0.0),
        (0.0, 2.0, 0.0),
        (0.0, 4.0, 0.0),
        (2.0, 0.0, 0.0),
        (2.0, 2.0, 0.0),
        (2.0, 4.0, 0.0),
    ]
    assert reg.topology["kind"] == "square_lattice"
    assert reg.topology["rows"] == 2
    assert reg.topology["cols"] == 3


def test_register_udg_constructor_accepts_points_and_reports_edges():
    reg = Register.udg([(0.0, 0.0), (0.5, 0.0), (2.0, 0.0)], blockade_radius=1.0)

    assert _coords(reg) == [(0.0, 0.0, 0.0), (0.5, 0.0, 0.0), (2.0, 0.0, 0.0)]
    assert reg.topology == {"kind": "udg", "n": 3, "blockade_radius": 1.0}
    summary = reg.geometry_summary(blockade_radius=1.0)
    assert summary["blockade_edge_count"] == 1
    assert summary["blockade_edges"] == [[0, 1]]

    compact_summary = reg.geometry_summary(blockade_radius=1.0, include_edges=False)
    assert compact_summary["blockade_edge_count"] == 1
    assert "blockade_edges" not in compact_summary


def test_register_udg_constructor_accepts_networkx_graph_node_order():
    graph = nx.Graph()
    graph.add_node("b", pos=(1.0, 0.0))
    graph.add_node("a", pos=(0.0, 0.0))

    reg = Register.from_udg_graph(graph, blockade_radius=1.5)

    assert _coords(reg) == [(1.0, 0.0, 0.0), (0.0, 0.0, 0.0)]
    assert reg.topology["node_order"] == ["b", "a"]
    assert reg.topology["position_attr"] == "pos"


def test_register_constructor_validation_is_normalized():
    with pytest.raises(SagittariusValidationError) as excinfo:
        Register.chain(0)

    assert excinfo.value.issue.code == "VALIDATION_REGISTER_SIZE_VALUE"
    assert "at least one atom" in excinfo.value.issue.remediation
