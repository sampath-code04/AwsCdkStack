from aws_cdk import (
    Stack,
    aws_ec2 as ec2
)
from constructs import Construct

class AwsCdkStackStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create an empty VPC
        vpc = ec2.CfnVPC(self, "MyVpc",
            cidr_block="15.0.0.0/16",
            tags=[{
                "key": "Name",
                "value": "MyVpc"
            }]
        )

        
        # Define subnet configurations
        public_subnet_cidr = "15.0.1.0/24"  # Public subnet CIDR
        private_subnet_cidrs = [f"15.0.{i}.0/24" for i in range(2, 5)]  # Private subnets CIDRs

        # Create the public subnet
        public_subnet = ec2.CfnSubnet(self, "MyPublicSubnet",
            vpc_id=vpc.ref,
            cidr_block=public_subnet_cidr,
            availability_zone="us-east-1a",  # Adjust based on your region
            map_public_ip_on_launch=True,
            tags=[{
                "key": "Name",
                "value": "PubSubnet"
            }]
        )

        # Create private subnets
        private_subnets = []
        for i, cidr in enumerate(private_subnet_cidrs):
            subnet = ec2.CfnSubnet(self, f"MyPrivateSubnet{i + 1}",
                vpc_id=vpc.ref,
                cidr_block=cidr,
                availability_zone=f"us-east-1a",  # Adjust based on your region
                tags=[{
                    "key": "Name",
                    "value": f"PrivSubnet{i + 1}"
                }]
            )
            private_subnets.append(subnet)

        # Create an Internet Gateway
        internet_gateway = ec2.CfnInternetGateway(self, "MyInternetGateway")

        # Attach the Internet Gateway to the VPC
        ec2.CfnVPCGatewayAttachment(self, "MyVPCGatewayAttachment",
            vpc_id=vpc.ref,
            internet_gateway_id=internet_gateway.ref
        )

        # Create an Elastic IP for the NAT Gateway
        eip = ec2.CfnEIP(self, "MyEIP")

        # Create the NAT Gateway
        nat_gateway = ec2.CfnNatGateway(self, "MyNatGateway",
            allocation_id=eip.attr_allocation_id,
            subnet_id=public_subnet.ref
        )

        # Create route tables
        public_route_table = ec2.CfnRouteTable(self, "PubRT",
            vpc_id=vpc.ref
        )

        private_route_table = ec2.CfnRouteTable(self, "PrivRT",
            vpc_id=vpc.ref
        )

        # Create routes in the route tables
        ec2.CfnRoute(self, "PublicRoute",
            route_table_id=public_route_table.ref,
            destination_cidr_block="0.0.0.0/0",
            gateway_id=internet_gateway.ref
        )

        ec2.CfnRoute(self, "PrivateRoute",
            route_table_id=private_route_table.ref,
            destination_cidr_block="0.0.0.0/0",
            nat_gateway_id=nat_gateway.ref
        )

        # Associate the public subnet with the public route table
        ec2.CfnSubnetRouteTableAssociation(self, "PubSubnetRTAssociation",
            subnet_id=public_subnet.ref,
            route_table_id=public_route_table.ref
        )

        # Associate all private subnets with the private route table
        for subnet in private_subnets:
            ec2.CfnSubnetRouteTableAssociation(self, f"PrivSubnetRTAssociation{subnet.node.id}",
                subnet_id=subnet.ref,
                route_table_id=private_route_table.ref
            )
