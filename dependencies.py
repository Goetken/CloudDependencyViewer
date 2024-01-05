import boto3
import networkx as nx
import matplotlib.pyplot as plt


class Dependencies:
    """
    Base class for managing dependencies.
    """
    def __init__(self):
        """
        Constructor method. Calls the method to get all dependencies.
        """
        self.get_all_dependencies()

    def get_all_dependencies(self):
        """
        Placeholder method to get all dependencies. To be implemented in subclasses.
        """
        pass

    def create_graph(self):
        """
        Placeholder method to create a graph of dependencies. To be implemented in subclasses.
        """
        pass


class DependencyGraph:
    """
    Class for creating and managing a graph of dependencies.
    """
    def __init__(self):
        """
        Constructor method. Initializes an empty graph.
        """
        self.graph = nx.Graph()

    def add_node(self, node, color='lightgrey', style='filled'):
        """
        Adds a node to the graph.

        Args:
            node (str): The name of the node.
            color (str, optional): The color of the node. Defaults to 'lightgrey'.
            style (str, optional): The style of the node. Defaults to 'filled'.
        """
        node_name = self.sanitize_name(node)
        self.graph.add_node(node_name, color=color, style=style)

    def add_edge(self, node1, node2):
        """
        Adds an edge between two nodes in the graph.

        Args:
            node1 (str): The name of the first node.
            node2 (str): The name of the second node.
        """
        node1_name = self.sanitize_name(node1)
        node2_name = self.sanitize_name(node2)
        self.graph.add_edge(node1_name, node2_name)

    # Method to sanitize the name of the resource to be used in the graph by replacing all colons with underscores
    @staticmethod
    def sanitize_name(name):
        """
        Sanitizes the name of a node by replacing all colons with underscores.

        Args:
            name (str): The name to sanitize.

        Returns:
            str: The sanitized name.
        """
        return name.replace(':', '_')

    def filter_nodes_by_connections(self, min_connections=1):
        """
        Filters out nodes in the graph that have fewer than a certain number of connections.

        Args: min_connections (int, optional): The minimum number of connections a node must have to remain in the
        graph. Defaults to 1.
        """
        filtered_nodes = [node for node, degree in self.graph.degree() if degree >= min_connections]
        self.graph = self.graph.subgraph(filtered_nodes)

    def draw(self):
        """
        Draws the graph using matplotlib.
        """
        colors = [data.get('color', 'lightgrey') for node, data in self.graph.nodes(data=True)]
        pos = nx.spring_layout(self.graph)
        nx.draw(self.graph, pos,
                with_labels=True,
                node_color=colors,
                node_size=500,
                edge_color='grey',
                width=0.5,
                font_size=8)
        plt.show()


class AWSDependencies(Dependencies):
    """
    Class for managing AWS dependencies. Inherits from the Dependencies base class.
    """
    def __init__(self):
        """
        Constructor method. Initializes AWS service attributes and a DependencyGraph object.
        """
        self.ec2 = boto3.client('ec2')
        self.stepfunctions = None
        self.security_groups = None
        self.vpcs = None
        self.subnets = None
        self.internet_gateways = None
        self.graph = DependencyGraph()
        super().__init__()

    def get_all_dependencies(self):
        """
        Gets all AWS dependencies by calling the respective methods for each AWS service.
        """
        self.ec2 = self.get_ec2_instances()
        self.security_groups = self.get_security_groups()
        self.vpcs = self.get_vpcs()
        self.subnets = self.get_subnets()
        self.internet_gateways = self.get_internet_gateways()

    def create_graph(self):
        """
        Creates a graph of the AWS dependencies.

        This method iterates over each AWS service (EC2 instances, security groups, VPCs, subnets, and internet
        gateways) and adds them as nodes to the graph. It also adds edges between related nodes. For example,
        an edge is added between an EC2 instance and its associated security groups. Similarly, edges are added
        between a VPC and its tags, a subnet and its tags, and an internet gateway and its tags.

        After all nodes and edges have been added, the method filters out nodes that have fewer than a certain number of
        connections (default is 1). Finally, it draws the graph using matplotlib.
        """

        for instance in self.ec2:
            self.graph.add_node(instance['InstanceId'], color='lightblue', style='filled')
            for security_group in instance['SecurityGroups']:
                self.graph.add_edge(instance['InstanceId'], security_group['GroupName'])

        for security_group in self.security_groups:
            self.graph.add_node(security_group['GroupName'], color='red', style='filled')
            for permission in security_group['IpPermissions']:
                if 'UserIdGroupPairs' in permission and len(permission['UserIdGroupPairs']) > 0:
                    self.graph.add_edge(security_group['GroupName'], permission['UserIdGroupPairs'][0]['GroupId'])

            for permission in security_group['IpPermissionsEgress']:
                if 'UserIdGroupPairs' in permission and len(permission['UserIdGroupPairs']) > 0:
                    self.graph.add_edge(security_group['GroupName'], permission['UserIdGroupPairs'][0]['GroupId'])

        for vpc in self.vpcs:
            self.graph.add_node(vpc['VpcId'], color='yellow', style='filled')
            for tag in vpc['Tags']:
                self.graph.add_edge(vpc['VpcId'], tag['Value'])

        for subnet in self.subnets:
            self.graph.add_node(subnet['SubnetId'], color='lightgreen', style='filled')
            for tag in subnet['Tags']:
                self.graph.add_edge(subnet['SubnetId'], tag['Value'])

        for internet_gateway in self.internet_gateways:
            self.graph.add_node(internet_gateway['InternetGatewayId'], color='lightgrey', style='filled')
            for tag in internet_gateway['Tags']:
                self.graph.add_edge(internet_gateway['InternetGatewayId'], tag['Value'])

        self.graph.filter_nodes_by_connections(1)
        self.graph.draw()
        return


    def get_ec2_instances(self):
        """
        Gets all EC2 instances.

        Returns:
            list: A list of EC2 instances.
        """
        response = self.ec2.describe_instances()

        instances = []
        for reservation in response["Reservations"]:
            for instance in reservation["Instances"]:
                instances.append(instance)
        print("EC2 Instances: ", len(instances))
        print(f"EC2 Instance example: {instances[0]}\n\n")
        return instances

    def get_security_groups(self):
        """
        Gets all security groups.

        Returns:
            list: A list of security groups.
        """
        response = self.ec2.describe_security_groups()
        security_groups = []
        for security_group in response["SecurityGroups"]:
            security_groups.append(security_group)

        print(f"Security Group example: {security_groups[0]}\n\n")
        return security_groups

    def get_vpcs(self):
        """
        Gets all VPCs.

        Returns:
            list: A list of VPCs.
        """
        response = self.ec2.describe_vpcs()
        vpcs = []
        for vpc in response["Vpcs"]:
            vpcs.append(vpc)
        print(f"VPC example: {vpcs[0]}\n\n")
        return vpcs

    def get_subnets(self):
        """
        Gets all subnets.

        Returns:
            list: A list of subnets.
        """
        response = self.ec2.describe_subnets()
        subnets = []
        for subnet in response["Subnets"]:
            subnets.append(subnet)

        print(f"Subnet example: {subnets[0]}\n\n")
        return subnets

    def get_internet_gateways(self):
        """
        Gets all internet gateways.

        Returns:
            list: A list of internet gateways.
        """
        response = self.ec2.describe_internet_gateways()
        internet_gateways = []
        for internet_gateway in response["InternetGateways"]:
            internet_gateways.append(internet_gateway)

        print(f"Internet Gateway example: {internet_gateways[0]}\n\n")
        return internet_gateways


if __name__ == '__main__':
    """
    Main execution. Creates an AWSDependencies object and creates a graph of the dependencies.
    """
    dependencies = AWSDependencies()
    dependencies.create_graph()
