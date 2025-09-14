provider "aws" {
  region = "us-east-2"
}

resource "aws_eks_cluster" "this" {
  name     = "my-pay2-eks-cluster"
  role_arn = "arn:aws:iam::381492217844:role/eks-cluster-role"  # use the role you created

  vpc_config {
    subnet_ids = ["subnet-00ef221606b1cbff7","subnet-0e950cf921ca3dcd5"]  # replace with your private subnet IDs
  }
}

resource "aws_eks_node_group" "this" {
  cluster_name    = aws_eks_cluster.this.name
  node_group_name = "worker-nodes"
  node_role_arn   = "arn:aws:iam::381492217844:role/eks-node-role" # create this role in console if not done
  subnet_ids      = ["subnet-0189d15b98a97b63c", "subnet-0604038a71b8237c1"]

  scaling_config {
    desired_size = 2
    max_size     = 3
    min_size     = 1
  }
}
