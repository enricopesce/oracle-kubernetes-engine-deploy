import pulumi
from pulumi_kubernetes.core.v1 import Service
from pulumi_kubernetes.helm.v3 import Chart, ChartOpts
import pulumi_kubernetes as k8s
import pulumi_oci as oci
import ipaddress
import os

# def get_oke_image(source, pattern):
#    return list(filter(lambda x: re.search(pattern, x["source_name"]), source))

# test_node_pool_option = oci.containerengine.get_node_pool_option_output(
#     node_pool_option_id=oke_cluster.id,
#     compartment_id=compartment_id)
# c = test_node_pool_option.sources

# c.apply(lambda images: get_oke_image(images, "Oracle-Linux-8.9.*-OKE-1.29.1.*")).apply(lambda x: pprint(x))



def get_ads(ads, net):
    z = []
    for ad in ads:
        z.append({"availability_domain": str(ad['name']), "subnet_id": net})
    return z


def get_ssh_key(key_path):
    if not os.path.isfile(key_path):
        raise FileNotFoundError(
            f"SSH public key file not found at path: {key_path}")
    with open(key_path, 'r') as public_key_file:
        ssh_key = public_key_file.read()
    return ssh_key


def subnet_cidr(cidr):
    network = ipaddress.ip_network(cidr, strict=False)
    if network.prefixlen > 30:
        raise ValueError(
            "Cannot subnet further, the prefix length is too long.")
    subnets = list(network.subnets(new_prefix=network.prefixlen + 1))
    subnet_strs = [str(subnet) for subnet in subnets]
    return subnet_strs


cidr_block = "10.0.0.0/16"
public_subnet_address, private_subnet_address = subnet_cidr(cidr_block)

cluster_name = "my-oke-cluster"
node_pool_name = "my-node-pool"
node_shape = "VM.Standard.E5.Flex"
kubernetes_version = "v1.29.1"
oke_node_operating_system = "Oracle Linux"
oke_operating_system_version = "8"
oke_min_nodes = "1"
node_image_id = "ocid1.image.oc1.eu-frankfurt-1.aaaaaaaaxhd3lt7dttn22pwvhzyksgcm3mxbksnowz47b3oku5hbc6rlisvq"

# Configuration variables
config = pulumi.Config()
compartment_id = config.require("compartment_ocid")

# Create a VCN
vcn = oci.core.Vcn(
    "myVcn",
    compartment_id=compartment_id,
    cidr_block=cidr_block,
    display_name="my-vcn",
    dns_label="myvcn",
)

# Create an Internet Gateway for the public subnet
internet_gateway = oci.core.InternetGateway(
    "myInternetGateway",
    compartment_id=compartment_id,
    vcn_id=vcn.id,
    display_name="my-ig",
    enabled=True,
)

# Create a NAT Gateway for the private subnet
nat_gateway = oci.core.NatGateway(
    "myNatGateway",
    compartment_id=compartment_id,
    vcn_id=vcn.id,
    display_name="my-nat-gw",
)

# Create a Service Gateway for access to OCI services
service_gateway = oci.core.ServiceGateway("myServiceGateway",
                                          compartment_id=compartment_id,
                                          vcn_id=vcn.id,
                                          services=[oci.core.ServiceGatewayServiceArgs(
                                              service_id=oci.core.get_services(
                                              ).services[0].id
                                          )],
                                          display_name="my-service-gateway")


# Create a separate Security List for the Public Subnet
public_security_list = oci.core.SecurityList(
    "myPublicSecurityList",
    compartment_id=compartment_id,
    vcn_id=vcn.id,
    display_name="my-public-security-list",
    egress_security_rules=[
        {
            "destination": "0.0.0.0/0",
            "protocol": "all",
        }
    ],
    ingress_security_rules=[
        {
            "protocol": "6",
            "source": "0.0.0.0/0",
            "tcp_options": {
                "max": 80,
                "min": 80,
            },
            "description": "accept ingress HTTP protocol from all"
        },
        {
            "protocol": "6",
            "source": "0.0.0.0/0",
            "tcp_options": {
                "max": 443,
                "min": 443,
            },
            "description": "accept ingress HTTPS protocol from all"
        },
        {
            "protocol": "6",
            "source": "0.0.0.0/0",
            "tcp_options": {
                "max": 22,
                "min": 22,
            },
            "description": "accept ingress SSH protocol from all"
        },
        {
            "protocol": "6",
            "source": "0.0.0.0/0",
            "tcp_options": {
                "max": 6443,
                "min": 6443,
            },
            "description": "accept ingress Kubernetes protocol from all"
        },        
    ],
)

# Create a separate Security List for the Private Subnet
private_security_list = oci.core.SecurityList(
    "myPrivateSecurityList",
    compartment_id=compartment_id,
    vcn_id=vcn.id,
    display_name="my-private-security-list",
    egress_security_rules=[
        {
            "destination": oci.core.get_services().services[0].cidr_block,
            "protocol": "all",
            "destination_type": "SERVICE_CIDR_BLOCK",
            "description": "worker to oci services"
        },
        {
            "destination": "0.0.0.0/0",
            "protocol": "all",
            "description": "worker to all networks"
        },
    ],
    ingress_security_rules=[
        {  # Client access to Kubernetes API endpoint
            "protocol": "all",
            "source": "0.0.0.0/0",
            "description": "acceppt all traffic to private subnet"
        },
    ],
)

# Create a Route Table for the private subnet with a route via the NAT Gateway
private_route_table = oci.core.RouteTable(
    "myPrivateRouteTable",
    compartment_id=compartment_id,
    vcn_id=vcn.id,
    display_name="my-private-rt",
    route_rules=[
        oci.core.RouteTableRouteRuleArgs(
            destination="0.0.0.0/0",
            network_entity_id=nat_gateway.id,
        ),
        oci.core.RouteTableRouteRuleArgs(
            destination=oci.core.get_services().services[0].cidr_block,
            destination_type="SERVICE_CIDR_BLOCK",
            network_entity_id=service_gateway.id,
        ),
    ],
)

# Create a Route Table for the public subnet with a route via the Internet Gateway
public_route_table = oci.core.RouteTable(
    "myPublicRouteTable",
    compartment_id=compartment_id,
    vcn_id=vcn.id,
    display_name="my-public-rt",
    route_rules=[
        oci.core.RouteTableRouteRuleArgs(
            destination="0.0.0.0/0",
            network_entity_id=internet_gateway.id,
        )
    ],
)

# Create a Public Subnet within the VCN
public_subnet = oci.core.Subnet(
    "myPublicSubnet",
    compartment_id=compartment_id,
    security_list_ids=[public_security_list.id],
    vcn_id=vcn.id,
    cidr_block=public_subnet_address,
    display_name="my-public-subnet",
    dns_label="publicsubnet",
    prohibit_public_ip_on_vnic=False,
    route_table_id=public_route_table
)

# Create a Private Subnet within the VCN
private_subnet = oci.core.Subnet(
    "myPrivateSubnet",
    compartment_id=compartment_id,
    security_list_ids=[private_security_list.id],
    vcn_id=vcn.id,
    cidr_block=private_subnet_address,
    display_name="my-private-subnet",
    dns_label="privatesubnet",
    prohibit_public_ip_on_vnic=True,
    route_table_id=private_route_table
)

# Create the OKE cluster
oke_cluster = oci.containerengine.Cluster(
    "myOkeCluster",
    compartment_id=compartment_id,
    name=cluster_name,
    kubernetes_version=kubernetes_version,
    options=oci.containerengine.ClusterOptionsArgs(
        service_lb_subnet_ids=[public_subnet.id],
        kubernetes_network_config=oci.containerengine.ClusterOptionsKubernetesNetworkConfigArgs(
            pods_cidr="10.2.0.0/16",
            services_cidr="10.3.0.0/16",
        )),
    cluster_pod_network_options=[oci.containerengine.ClusterClusterPodNetworkOptionArgs(
        cni_type="OCI_VCN_IP_NATIVE",
    )],
    type="BASIC_CLUSTER",
    vcn_id=vcn.id,
    endpoint_config=oci.containerengine.ClusterEndpointConfigArgs(
        subnet_id=public_subnet,
        is_public_ip_enabled=True
    )
)

# get_ad_names = oci.identity.get_availability_domains_output(
#     compartment_id=compartment_id)
# ads = get_ad_names.availability_domains


# # Create a node pool
# node_pool = oci.containerengine.NodePool(
#     "oke_node_pool_1",
#     cluster_id=oke_cluster.id,
#     compartment_id=compartment_id,
#     kubernetes_version=kubernetes_version,
#     name=node_pool_name,
#     node_config_details=oci.containerengine.NodePoolNodeConfigDetailsArgs(
#         placement_configs=ads.apply(
#             lambda ads: get_ads(ads, private_subnet.id)),
#         size=oke_min_nodes,
#         node_pool_pod_network_option_details=oci.containerengine.NodePoolNodeConfigDetailsNodePoolPodNetworkOptionDetailsArgs(
#             cni_type="OCI_VCN_IP_NATIVE",
#             pod_subnet_ids=[private_subnet.id]
#         ),
#     ),
#     node_shape=node_shape,
#     node_shape_config=oci.containerengine.NodePoolNodeShapeConfigArgs(
#         memory_in_gbs=16,
#         ocpus=2
#     ),
#     node_source_details=oci.containerengine.NodePoolNodeSourceDetailsArgs(
#         image_id=node_image_id,
#         source_type="IMAGE",
#     ),
#     ssh_public_key=get_ssh_key("./id_dsa.key.pub")
# )

# kubeconfig = oci.containerengine.get_cluster_kube_config_output(cluster_id=oke_cluster.id).apply(
#     lambda kube_config: kube_config.content)

pulumi.export('vcn_id', vcn.id)
pulumi.export('internet_gateway_id', internet_gateway.id)
pulumi.export('nat_gateway_id', nat_gateway.id)
pulumi.export('service_gateway_id', service_gateway.id)
pulumi.export('public_subnet_id', public_subnet.id)
pulumi.export('private_subnet_id', private_subnet.id)
pulumi.export('public_security_list_id', public_security_list.id)
pulumi.export('private_security_list_id', private_security_list.id)
pulumi.export("cluster_id", oke_cluster.id)
# pulumi.export("node_pool_id", node_pool.id)
# pulumi.export("kubeconfig", kubeconfig)