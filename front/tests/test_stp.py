import pytest
import json
from conftest import MiminetTester
from utils.networks import NodeType, MiminetTestNetwork
from utils.locators import Location
from utils.checkers import TestNetworkComparator
from utils.expected_loader import ExpectedLoader


class TestSTP(ExpectedLoader):

    @pytest.fixture(scope="class")
    def network(self, selenium: MiminetTester):
        network = MiminetTestNetwork(selenium)

        # nodes
        network.add_node(NodeType.Host, 25, 80)  # host 1
        network.add_node(NodeType.Host, 75, 80)  # host 2
        network.add_node(NodeType.Switch, 50, 65)  # switch 1
        network.add_node(NodeType.Switch, 25, 55)  # switch 2
        network.add_node(NodeType.Switch, 75, 55)  # switch 3

        # edges
        network.add_edge(0, 2)  # host 1 -> switch 1
        network.add_edge(1, 2)  # host 2 -> switch 1
        network.add_edge(3, 2)  # switch 2 -> switch 1
        network.add_edge(3, 4)  # switch 2 -> switch 3
        network.add_edge(4, 2)  # switch 3 -> switch 1

        # configure hosts
        host1_config = network.open_node_config(0)
        host1_config.fill_link("192.168.1.1", 24)
        host1_config.add_jobs(
            1,
            {Location.Network.ConfigPanel.Host.Job.PING_FIELD.selector: "192.168.1.2"},
        )
        host1_config.submit()

        host2_config = network.open_node_config(1)
        host2_config.fill_link("192.168.1.2", 24)
        host2_config.submit()

        # config switches
        switch1_config = network.open_node_config(2)
        switch1_config.enable_stp()  # ON stp
        switch1_config.disable_stp()  # OFF stp (just for test)
        switch1_config.submit()
        selenium.refresh()

        switch2_config = network.open_node_config(3)
        switch2_config.enable_stp()  # ON stp
        switch2_config.submit()
        selenium.refresh()

        switch3_config = network.open_node_config(4)
        switch3_config.enable_stp()  # ON stp
        switch3_config.disable_stp()  # OFF stp (just for test)
        switch3_config.submit()

        yield network

        network.delete()

    def test_stp(self, selenium: MiminetTester, network: MiminetTestNetwork):
        assert TestNetworkComparator.compare_nodes(network.nodes, self.expected["nodes"])
        assert TestNetworkComparator.compare_edges(network.edges, self.expected["edges"])
        assert TestNetworkComparator.compare_jobs(network.jobs, self.expected["jobs"])
