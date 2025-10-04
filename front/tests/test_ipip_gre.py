import pytest
import json
from conftest import MiminetTester
from utils.networks import NodeType, MiminetTestNetwork
from utils.locators import Location
from typing import Tuple
from utils.checkers import TestNetworkComparator
from utils.expected_loader import ExpectedLoader


class TestIPIPGre(ExpectedLoader):

    @pytest.fixture(scope="class", params=["ipip", "gre"])
    def protocol_and_network(self, selenium: MiminetTester, request):
        protocol = request.param
        network = MiminetTestNetwork(selenium)

        network.add_node(NodeType.Host, 25, 90)  # left host
        network.add_node(NodeType.Host, 75, 90)  # right host
        network.add_node(NodeType.Router, 25, 60)  # left router
        network.add_node(NodeType.Router, 75, 60)  # right router
        network.add_node(NodeType.Router, 50, 30)  # main router

        network.add_edge(0, 2)  # left host -> left router
        network.add_edge(1, 3)  # right host -> right router
        network.add_edge(2, 4)  # left router -> main router
        network.add_edge(3, 4)  # right router -> main router

        # configure hosts
        left_host_config = network.open_node_config(0)
        left_host_config.fill_link("192.168.1.2", 24)
        left_host_config.fill_default_gw("192.168.1.1")
        left_host_config.add_jobs(
            1, {Location.Network.ConfigPanel.Host.Job.PING_FIELD.selector: "10.0.0.2"}
        )
        left_host_config.submit()

        right_host_config = network.open_node_config(1)
        right_host_config.fill_link("10.0.0.2", 24)
        right_host_config.fill_default_gw("10.0.0.1")
        right_host_config.submit()

        # configure main router
        server_config = network.open_node_config(4)
        server_config.fill_link("212.220.12.2", 30, link_id=0)
        server_config.fill_link("212.220.12.6", 30, link_id=1)
        server_config.submit()

        # configure routers

        # - left
        left_router = network.open_node_config(2)
        left_router.fill_link("192.168.1.1", 24)
        left_router.fill_link("212.220.12.1", 30, link_id=1)
        left_router.fill_default_gw("212.220.12.2")
        left_router.submit()  # extra submit because job should select iface below

        left_iface_ip = network.nodes[2]["interface"][1]["ip"]

        if protocol == "ipip":
            left_router.add_jobs(
                105,
                {
                    Location.Network.ConfigPanel.Router.Job.IPIP_END_IP_FIELD.selector: "212.220.12.5",
                    Location.Network.ConfigPanel.Router.Job.IPIP_IFACE_IP_FIELD.selector: "1.1.1.1",
                    Location.Network.ConfigPanel.Router.Job.IPIP_NAME_IFACE_FIELD.selector: "tun1",
                    Location.Network.ConfigPanel.Router.Job.IPIP_IFACE_SELECT.selector: left_iface_ip,
                },
            )
        elif protocol == "gre":
            left_router.add_jobs(
                106,
                {
                    Location.Network.ConfigPanel.Router.Job.GRE_END_IP_FIELD.selector: "212.220.12.5",
                    Location.Network.ConfigPanel.Router.Job.GRE_IFACE_IP_FIELD.selector: "1.1.1.1",
                    Location.Network.ConfigPanel.Router.Job.GRE_NAME_IFACE_FIELD.selector: "gre1",
                    Location.Network.ConfigPanel.Router.Job.GRE_IFACE_SELECT.selector: left_iface_ip,
                },
            )
        else:
            raise ValueError(f"Unsupported protocol: {protocol}.")

        left_router.submit()

        left_router.add_jobs(
            102,
            {
                Location.Network.ConfigPanel.Router.Job.ADD_ROUTE_IP_FIELD.selector: "10.0.0.0",
                Location.Network.ConfigPanel.Router.Job.ADD_ROUTE_MASK_FIELD.selector: "24",
                Location.Network.ConfigPanel.Router.Job.ADD_ROUTE_IP_GW_FIELD.selector: "1.1.1.1",
            },
        )

        left_router.submit()

        # - right

        right_router = network.open_node_config(3)
        right_router.fill_link("10.0.0.1", 24)
        right_router.fill_link("212.220.12.5", 30, link_id=1)
        right_router.fill_default_gw("212.220.12.6")
        right_router.submit()

        right_iface_ip = network.nodes[3]["interface"][1]["ip"]

        if protocol == "ipip":
            right_router.add_jobs(
                105,
                {
                    Location.Network.ConfigPanel.Router.Job.IPIP_END_IP_FIELD.selector: "212.220.12.1",
                    Location.Network.ConfigPanel.Router.Job.IPIP_IFACE_IP_FIELD.selector: "2.2.2.2",
                    Location.Network.ConfigPanel.Router.Job.IPIP_NAME_IFACE_FIELD.selector: "tun1",
                    Location.Network.ConfigPanel.Router.Job.IPIP_IFACE_SELECT.selector: right_iface_ip,
                },
            )
        elif protocol == "gre":
            right_router.add_jobs(
                106,
                {
                    Location.Network.ConfigPanel.Router.Job.GRE_END_IP_FIELD.selector: "212.220.12.1",
                    Location.Network.ConfigPanel.Router.Job.GRE_IFACE_IP_FIELD.selector: "2.2.2.2",
                    Location.Network.ConfigPanel.Router.Job.GRE_NAME_IFACE_FIELD.selector: "gre1",
                    Location.Network.ConfigPanel.Router.Job.GRE_IFACE_SELECT.selector: right_iface_ip,
                },
            )
        else:
            raise ValueError(f"Unsupported protocol: {protocol}.")

        right_router.submit()

        right_router.add_jobs(
            102,
            {
                Location.Network.ConfigPanel.Router.Job.ADD_ROUTE_IP_FIELD.selector: "192.168.1.0",
                Location.Network.ConfigPanel.Router.Job.ADD_ROUTE_MASK_FIELD.selector: "24",
                Location.Network.ConfigPanel.Router.Job.ADD_ROUTE_IP_GW_FIELD.selector: "2.2.2.2",
            },
        )

        right_router.submit()

        # end configure

        yield (protocol, network)

        # network.delete()

    def test_ipip_gre(
        self,
        selenium: MiminetTester,
        protocol_and_network: Tuple[str, MiminetTestNetwork],
    ):
        protocol: str = protocol_and_network[0]
        network: MiminetTestNetwork = protocol_and_network[1]

        assert TestNetworkComparator.compare_nodes(self.expected["nodes"], network.nodes)
        assert TestNetworkComparator.compare_edges(self.expected["edges"], network.edges)

        if protocol == "ipip":
            assert TestNetworkComparator.compare_jobs(
                self.expected["ipip_jobs"], network.jobs
            )
        elif protocol == "gre":
            assert TestNetworkComparator.compare_jobs(
                self.expected["gre_jobs"], network.jobs
            )
        else:
            raise ValueError(f"Got unsupported protocol: {protocol}.")
