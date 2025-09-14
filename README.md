Payment App Deployment on AWS EKS

This project demonstrates a full DevOps pipeline for deploying a containerized Payment Application on Amazon EKS using Terraform, GitHub Actions, Docker, and Kubernetes.

🚀 Features

Infrastructure as Code (IaC) with Terraform to provision:

-VPC, Subnets, Security Groups

-Amazon EKS Cluster & Node Groups

-IAM roles and networking resources

CI/CD with GitHub Actions:

-Automated build and push of Docker images to Amazon ECR

-Kubernetes deployment updates applied to EKS

Containerized Application:

-Dockerized Payment App (Node.js / Flask backend)

-Kubernetes manifests (deployment.yaml, service.yaml) for easy scaling

Load Balancer Integration:

-Exposes application via AWS Elastic Load Balancer (publicly accessible DNS)

Monitoring & Scaling:

-Configured auto-scaling for worker nodes

-CloudWatch integration for cluster logs

🛠️ Tech Stack

Cloud: AWS (EKS, ECR, VPC, IAM, EC2, ELB, CloudWatch)

Orchestration: Kubernetes

CI/CD: GitHub Actions

IaC: Terraform

Containers: Docker
