import pulumi
import pulumi_oci as oci

# Configuration variables
config = pulumi.Config()
compartment_id = config.require("compartment_ocid")

# Create a VCN
vcn = oci.core.Vcn(
    "myVcn",
    compartment_id=compartment_id,
    cidr_block="10.0.0.0/16",
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
                                              service_id=oci.core.get_services().services[0].id
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
        },
        {
            "protocol": "6",
            "source": "0.0.0.0/0",
            "tcp_options": {
                "max": 443,
                "min": 443,
            },
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
            "destination": "0.0.0.0/0",
            "protocol": "all",
        }
    ],
    ingress_security_rules=[
        {
            "protocol": "6",
            "source": "10.0.1.0/24",
            "tcp_options": {
                "max": 22,
                "min": 22,
            },
        }
    ],
)

# Create a Public Subnet within the VCN
public_subnet = oci.core.Subnet(
    "myPublicSubnet",
    compartment_id=compartment_id,
    security_list_ids=[public_security_list.id],
    vcn_id=vcn.id,
    cidr_block="10.0.1.0/24",
    display_name="my-public-subnet",
    dns_label="publicsubnet",
    prohibit_public_ip_on_vnic=False,
)

# Create a Private Subnet within the VCN
private_subnet = oci.core.Subnet(
    "myPrivateSubnet",
    compartment_id=compartment_id,
    security_list_ids=[private_security_list.id],
    vcn_id=vcn.id,
    cidr_block="10.0.2.0/24",
    display_name="my-private-subnet",
    dns_label="privatesubnet",
    prohibit_public_ip_on_vnic=True,
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

pulumi.export('vcn_id', vcn.id)
pulumi.export('internet_gateway_id', internet_gateway.id)
pulumi.export('nat_gateway_id', nat_gateway.id)
pulumi.export('service_gateway_id', service_gateway.id)
pulumi.export('public_subnet_id', public_subnet.id)
pulumi.export('private_subnet_id', private_subnet.id)
pulumi.export('public_security_list_id', public_security_list.id)
pulumi.export('private_security_list_id', private_security_list.id)