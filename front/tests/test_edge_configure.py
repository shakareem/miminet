import pytest
from conftest import MiminetTester
from utils.checkers import TestNetworkComparator
from utils.networks import MiminetTestNetwork, NodeType
from utils.expected_loader import ExpectedLoader


class TestEdgeConfigure(ExpectedLoader):

    @pytest.fixture(scope="class")
    def network(self, selenium: MiminetTester):
        network = MiminetTestNetwork(selenium)

        source_id = network.add_node(NodeType.Host)
        target_id = network.add_node(NodeType.Host)

        network.add_edge(source_id, target_id)

        source_config = network.open_node_config(source_id)
        source_config.fill_link("10.0.0.1", 24)
        source_config.submit()

        target_config = network.open_node_config(target_id)
        target_config.fill_link("10.0.0.2", 24)
        target_config.submit()

        yield network
        network.delete()

    def test_edge_loss_percentage_change(
        self, selenium: MiminetTester, network: MiminetTestNetwork
    ):
        edge = network.edges[0]

        edge_config = network.open_edge_config(edge)

        # Set to non-zero
        edge_config.set_loss_percentage(50)
        edge_config.submit()

        assert TestNetworkComparator.compare_nodes(
            self.expected["nodes_enabled"], network.nodes
        )
        assert TestNetworkComparator.compare_edges(
            self.expected["edges_enabled_50_loss"], network.edges
        )

        # Set to zero
        edge_config.set_loss_percentage(0)
        edge_config.submit()

        assert TestNetworkComparator.compare_nodes(
            self.expected["nodes_enabled"], network.nodes
        )
        assert TestNetworkComparator.compare_edges(
            self.expected["edges_enabled_0_loss"], network.edges
        )

    def test_edge_disable_and_enable(
        self, selenium: MiminetTester, network: MiminetTestNetwork
    ):
        edge = network.edges[0]

        edge_config = network.open_edge_config(edge)

        # Disable edge
        edge_config.disable()
        edge_config.submit()

        assert TestNetworkComparator.compare_nodes(
            self.expected["nodes_disabled"], network.nodes
        )
        assert TestNetworkComparator.compare_edges(
            self.expected["edges_disabled"], network.edges
        )

        # Enable edge back
        edge_config.enable()
        edge_config.submit()

        assert TestNetworkComparator.compare_nodes(
            self.expected["nodes_enabled"], network.nodes
        )
        assert TestNetworkComparator.compare_edges(
            self.expected["edges_enabled_0_loss"], network.edges
        )
