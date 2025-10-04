import pytest
import json
from conftest import MiminetTester
from utils.networks import NodeConfig, NodeType, MiminetTestNetwork
from utils.locators import Location
from typing import Tuple
from utils.checkers import TestNetworkComparator
from utils.expected_loader import ExpectedLoader


class TestTcpUdp(ExpectedLoader):
    """
    This test build complex network,
    using switch, hub, tcp server and host.

    It checks not only the TCP/UDP connection setup,
    but also the default gateway settings.
    """

    @pytest.fixture(scope="class", params=["tcp", "udp"])
    def protocol_and_network(self, selenium: MiminetTester, request):
        protocol = request.param
        network = MiminetTestNetwork(selenium)

        # nodes
        network.add_node(NodeType.Host, x=20, y=50)
        network.add_node(NodeType.Switch, x=35, y=75)
        network.add_node(NodeType.Router, x=50, y=50)
        network.add_node(NodeType.Hub, x=65, y=75)
        network.add_node(NodeType.Server, x=80, y=50)

        # edges
        network.add_edge(0, 1)  # host -> switch
        network.add_edge(1, 2)  # switch -> router
        network.add_edge(2, 3)  # switch -> hub
        network.add_edge(3, 4)  # hub -> server

        # config host
        host_config: NodeConfig = network.open_node_config(0)
        host_config.fill_link("192.168.1.1", 24)
        host_config.fill_default_gw("192.168.1.2")
        job_params = ("65535", "10.0.0.1", "3000")

        if protocol == "tcp":
            host_config.add_jobs(
                4,
                {
                    Location.Network.ConfigPanel.Host.Job.TCP_VOLUME_IN_BYTES_FIELD.selector: job_params[
                        0
                    ],
                    Location.Network.ConfigPanel.Host.Job.TCP_IP_FIELD.selector: job_params[
                        1
                    ],
                    Location.Network.ConfigPanel.Host.Job.TCP_PORT_FIELD.selector: job_params[
                        2
                    ],
                },
            )
        elif protocol == "udp":
            host_config.add_jobs(
                3,
                {
                    Location.Network.ConfigPanel.Host.Job.UDP_VOLUME_IN_BYTES_FIELD.selector: job_params[
                        0
                    ],
                    Location.Network.ConfigPanel.Host.Job.UDP_IP_FIELD.selector: job_params[
                        1
                    ],
                    Location.Network.ConfigPanel.Host.Job.UDP_PORT_FIELD.selector: job_params[
                        2
                    ],
                },
            )
        else:
            raise ValueError(f"Got unsupported protocol: {protocol}.")

        host_config.submit()

        # config router
        router_config: NodeConfig = network.open_node_config(2)
        router_config.fill_link("192.168.1.2", 24, link_id=0)
        router_config.fill_link("10.0.0.2", 24, link_id=1)
        router_config.submit()

        # config server
        server_config: NodeConfig = network.open_node_config(4)
        server_config.fill_link("10.0.0.1", 24)
        server_config.fill_default_gw("10.0.0.2")

        if protocol == "tcp":
            server_config.add_jobs(
                201,
                {
                    Location.Network.ConfigPanel.Server.Job.TCP_IP_FIELD.selector: job_params[
                        1
                    ],
                    Location.Network.ConfigPanel.Server.Job.TCP_PORT_FIELD.selector: job_params[
                        2
                    ],
                },
            )
        elif protocol == "udp":
            server_config.add_jobs(
                200,
                {
                    Location.Network.ConfigPanel.Server.Job.UDP_IP_FIELD.selector: job_params[
                        1
                    ],
                    Location.Network.ConfigPanel.Server.Job.UDP_PORT_FIELD.selector: job_params[
                        2
                    ],
                },
            )
        else:
            raise ValueError(f"Got unsupported protocol: {protocol}.")

        server_config.submit()

        # finish
        yield (protocol, network)

        network.delete()

    def test_tcp_udp(
        self,
        selenium: MiminetTester,
        protocol_and_network: Tuple[str, MiminetTestNetwork],
    ):
        protocol = protocol_and_network[0]
        network = protocol_and_network[1]

        assert TestNetworkComparator.compare_nodes(self.expected["nodes"], network.nodes)
        assert TestNetworkComparator.compare_edges(self.expected["edges"], network.edges)

        if protocol == "udp":
            assert TestNetworkComparator.compare_jobs(
                self.expected["udp_jobs"], network.jobs
            )
        elif protocol == "tcp":
            assert TestNetworkComparator.compare_jobs(
                self.expected["tcp_jobs"], network.jobs
            )
        else:
            raise ValueError(f"Got unsupported protocol: {protocol}.")
