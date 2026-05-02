import json
import tempfile
from pathlib import Path
from graphify.build import build_from_json
from graphify.cluster import cluster
from graphify.export import to_json, to_cypher, to_graphml, to_html, to_canvas, to_obsidian

FIXTURES = Path(__file__).parent / "fixtures"

def make_graph():
    return build_from_json(json.loads((FIXTURES / "extraction.json").read_text()))

def test_to_json_creates_file():
    G = make_graph()
    communities = cluster(G)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "graph.json"
        to_json(G, communities, str(out))
        assert out.exists()

def test_to_json_valid_json():
    G = make_graph()
    communities = cluster(G)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "graph.json"
        to_json(G, communities, str(out))
        data = json.loads(out.read_text())
        assert "nodes" in data
        assert "links" in data

def test_to_json_nodes_have_community():
    G = make_graph()
    communities = cluster(G)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "graph.json"
        to_json(G, communities, str(out))
        data = json.loads(out.read_text())
        for node in data["nodes"]:
            assert "community" in node

def test_to_cypher_creates_file():
    G = make_graph()
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "cypher.txt"
        to_cypher(G, str(out))
        assert out.exists()

def test_to_cypher_contains_merge_statements():
    G = make_graph()
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "cypher.txt"
        to_cypher(G, str(out))
        content = out.read_text()
        assert "MERGE" in content

def test_to_graphml_creates_file():
    G = make_graph()
    communities = cluster(G)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "graph.graphml"
        to_graphml(G, communities, str(out))
        assert out.exists()

def test_to_graphml_valid_xml():
    G = make_graph()
    communities = cluster(G)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "graph.graphml"
        to_graphml(G, communities, str(out))
        content = out.read_text()
        assert "<graphml" in content
        assert "<node" in content

def test_to_graphml_has_community_attribute():
    G = make_graph()
    communities = cluster(G)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "graph.graphml"
        to_graphml(G, communities, str(out))
        content = out.read_text()
        assert "community" in content

def test_to_html_creates_file():
    G = make_graph()
    communities = cluster(G)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "graph.html"
        to_html(G, communities, str(out))
        assert out.exists()

def test_to_html_contains_visjs():
    G = make_graph()
    communities = cluster(G)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "graph.html"
        to_html(G, communities, str(out))
        content = out.read_text()
        assert "vis-network" in content

def test_to_html_contains_search():
    G = make_graph()
    communities = cluster(G)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "graph.html"
        to_html(G, communities, str(out))
        content = out.read_text()
        assert "search" in content.lower()

def test_to_html_contains_legend_with_labels():
    G = make_graph()
    communities = cluster(G)
    labels = {cid: f"Group {cid}" for cid in communities}
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "graph.html"
        to_html(G, communities, str(out), community_labels=labels)
        content = out.read_text()
        assert "Group 0" in content

def test_to_html_contains_nodes_and_edges():
    G = make_graph()
    communities = cluster(G)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "graph.html"
        to_html(G, communities, str(out))
        content = out.read_text()
        assert "RAW_NODES" in content
        assert "RAW_EDGES" in content


def test_to_html_member_counts_accepted():
    """to_html accepts member_counts without raising."""
    G = make_graph()
    communities = cluster(G)
    member_counts = {cid: len(members) for cid, members in communities.items()}
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "graph.html"
        to_html(G, communities, str(out), member_counts=member_counts)
        assert out.exists()


def test_to_canvas_file_paths_relative_to_vault():
    """Node file paths in canvas must be vault-root-relative (just fname.md), not hardcoded."""
    G = make_graph()
    communities = cluster(G)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "graph.canvas"
        to_canvas(G, communities, str(out))
        data = json.loads(out.read_text())
        file_nodes = [n for n in data["nodes"] if n.get("type") == "file"]
        assert file_nodes, "canvas should contain file nodes"
        for node in file_nodes:
            assert "/" not in node["file"], f"file path should not contain '/': {node['file']}"
            assert node["file"].endswith(".md")


def test_obsidian_qualified_cpp_names_stay_readable():
    extraction = {
        "nodes": [
            {
                "id": "client",
                "label": "acme::devices::DeviceClientId",
                "file_type": "code",
                "source_file": "client.h",
                "source_location": "L3",
            }
        ],
        "edges": [],
    }
    G = build_from_json(extraction)
    communities = {0: ["client"]}

    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        to_obsidian(G, communities, str(vault), community_labels={0: "Device Client"})
        note = vault / "acme - devices - DeviceClientId.md"
        assert note.exists()
        assert "# acme::devices::DeviceClientId" in note.read_text()
        cluster_notes = list(vault.glob("_GRAPH_CLUSTER_*.md"))
        assert cluster_notes
        assert "# Graph Cluster 0: Device Client" in cluster_notes[0].read_text()


def test_canvas_qualified_cpp_names_stay_readable():
    extraction = {
        "nodes": [
            {
                "id": "client",
                "label": "acme::devices::DeviceClientId",
                "file_type": "code",
                "source_file": "client.h",
                "source_location": "L3",
            }
        ],
        "edges": [],
    }
    G = build_from_json(extraction)
    communities = {0: ["client"]}

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "graph.canvas"
        to_canvas(G, communities, str(out), community_labels={0: "Device Client"})
        data = json.loads(out.read_text())
        assert any(
            n.get("type") == "file" and n.get("file") == "acme - devices - DeviceClientId.md"
            for n in data["nodes"]
        )
        assert any(
            n.get("type") == "group" and n.get("label") == "Graph Cluster 0: Device Client"
            for n in data["nodes"]
        )


def test_obsidian_cluster_notes_do_not_collide_on_duplicate_labels():
    extraction = {
        "nodes": [
            {"id": "a", "label": "A", "file_type": "code", "source_file": "a.py"},
            {"id": "b", "label": "B", "file_type": "code", "source_file": "b.py"},
        ],
        "edges": [],
    }
    G = build_from_json(extraction)
    communities = {3: ["a"], 7: ["b"]}

    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp)
        to_obsidian(G, communities, str(vault), community_labels={3: "Duplicate", 7: "Duplicate"})

        assert (vault / "_GRAPH_CLUSTER_3_Duplicate.md").exists()
        assert (vault / "_GRAPH_CLUSTER_7_Duplicate.md").exists()
