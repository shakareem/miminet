import pytest
import json
from conftest import MiminetTester
from utils.networks import NodeConfig, NodeType, MiminetTestNetwork
from utils.locators import Location
from utils.checkers import TestNetworkComparator
from utils.expected_loader import ExpectedLoader


class TestRouterCycle(ExpectedLoader):

    @pytest.fixture(scope="class")
    def network(self, selenium: MiminetTester):
        network = MiminetTestNetwork(selenium)

        # nodes
        network.add_node(NodeType.Host, 25, 50)  # single host
        network.add_node(NodeType.Router, 50, 25)  # router 1
        network.add_node(NodeType.Router, 90, 25)  # router 2
        network.add_node(NodeType.Router, 75, 50)  # router 3

        # edges
        network.add_edge(0, 1)  # host -> router 1
        network.add_edge(1, 2)  # router 1 -> router 2
        network.add_edge(2, 3)  # router 2 -> router 3
        network.add_edge(3, 1)  # router 3 -> router 1

        # host config
        host_config = network.open_node_config(0)
        self.configure_host(host_config)

        # routers config
        router1_config = network.open_node_config(1)
        self.configure_router(
            router1_config,
            ["10.0.0.2:23", "172.16.12.1:24", "169.254.1.1:24"],
            "172.16.12.2",
        )

        router2_config = network.open_node_config(2)
        self.configure_router(
            router2_config, ["172.16.12.2:24", "192.168.1.2:24"], "192.168.1.1"
        )

        router3_config = network.open_node_config(3)
        self.configure_router(
            router3_config, ["192.168.1.1:24", "169.254.1.2:24"], "169.254.1.1"
        )

        yield network

        network.delete()

    def configure_host(self, config: NodeConfig):
        config.fill_link("10.0.0.1", 24)
        config.fill_default_gw("10.0.0.2")
        config.add_jobs(
            1,
            {Location.Network.ConfigPanel.Host.Job.PING_FIELD.selector: "12.34.45.67"},
        )
        config.submit()

    def configure_router(self, config: NodeConfig, ip_mask_links: list[str], gw: str):
        config.fill_links(ip_mask_links)
        config.fill_default_gw(gw)
        config.submit()

    def test_cycle(self, selenium: MiminetTester, network: MiminetTestNetwork):
        assert TestNetworkComparator.compare_nodes(self.expected["nodes"], network.nodes)
        assert TestNetworkComparator.compare_jobs(self.expected["jobs"], network.jobs)
