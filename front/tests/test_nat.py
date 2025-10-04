import pytest
import json
from conftest import MiminetTester
from utils.networks import NodeConfig, NodeType, MiminetTestNetwork
from utils.locators import Location
from utils.checkers import TestNetworkComparator
from utils.expected_loader import ExpectedLoader


class TestNat(ExpectedLoader):

    @pytest.fixture(scope="class")
    def network(self, selenium: MiminetTester):
        network = MiminetTestNetwork(selenium)

        # nodes
        network.add_node(NodeType.Host, 25, 30)  # top host
        network.add_node(NodeType.Host, 25, 70)  # bottom host
        network.add_node(NodeType.Router, 50, 30)  # top router
        network.add_node(NodeType.Router, 50, 70)  # bottom router
        network.add_node(NodeType.Router, 70, 50)  # center router
        network.add_node(NodeType.Server, 90, 50)  # server

        # edges
        network.add_edge(0, 2)  # top host -> top router
        network.add_edge(1, 3)  # bottom host -> bottom router
        network.add_edge(2, 4)  # top router -> center router
        network.add_edge(3, 4)  # bottom router -> center router
        network.add_edge(4, 5)  # center router -> server

        # configure hosts
        # - top host
        top_host_config = network.open_node_config(0)
        self.configure_client_host(top_host_config)

        # - bottom host
        bottom_host_config = network.open_node_config(1)
        self.configure_client_host(bottom_host_config)

        # configure routers
        # - top router
        top_router_config = network.open_node_config(2)
        self.configure_client_router(
            top_router_config,
            "172.16.0.1",
            "172.16.0.2",
            network.nodes[2]["interface"][1]["id"],
        )

        # - bottom router
        bottom_router_config = network.open_node_config(3)
        self.configure_client_router(
            bottom_router_config,
            "172.16.1.1",
            "172.16.1.2",
            network.nodes[3]["interface"][1]["id"],
        )

        # configure center router
        center_router_config = network.open_node_config(4)
        center_router_config.fill_link("172.16.0.2", 24, 0)
        center_router_config.fill_link("172.16.1.2", 24, 1)
        center_router_config.fill_link("10.0.0.2", 24, 2)

        center_router_config.submit()

        # configure server
        server_config = network.open_node_config(5)
        server_config.fill_link("10.0.0.1", 24)
        server_config.fill_default_gw("10.0.0.2")
        server_config.submit()

        yield network

        network.delete()

    def configure_client_host(self, config: NodeConfig):
        config.fill_link("192.168.1.1", 24)
        config.fill_default_gw("192.168.1.2")
        config.add_jobs(
            1,
            {Location.Network.ConfigPanel.Host.Job.PING_FIELD.selector: "10.0.0.1"},
        )
        config.submit()

    def configure_client_router(
        self, config: NodeConfig, out_ip: str, out_gw: str, iface_id: str
    ):
        config.fill_link("192.168.1.2", 24, link_id=0)
        config.fill_link(out_ip, 24, link_id=1)
        config.fill_default_gw(out_gw)
        config.add_jobs(
            101,
            {
                Location.Network.ConfigPanel.Router.Job.NAT_LINK_SELECT.selector: iface_id
            },
        )

        config.submit()

    def test_nat(self, selenium: MiminetTester, network: MiminetTestNetwork):
        assert TestNetworkComparator.compare_nodes(network.nodes, self.expected["nodes"])
        assert TestNetworkComparator.compare_edges(network.edges, self.expected["edges"])
        assert TestNetworkComparator.compare_jobs(network.jobs, self.expected["jobs"])
