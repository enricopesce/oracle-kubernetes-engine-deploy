# WARNING: EXPERIMENTAL CODE!

This IaC template would be the simpler way to deploy a Kubernetes cluster on Oracle Cloud Infrastructure.

Useful to start without big competencies or as a starting working template.

I used Pulumi as an IaC tool, because for different reasons I don't like Terraform, but don't worry, under the hood Pulumi using Terraform anyway.

The main necessities that induce me to develop this template are the following:

- Simplicity: I have customers who need a good blueprint to start without complexity and a deep understanding
- Working: Most of the examples found are complex and not working well
- Security: The template is written to cover the best possible security for example embracing all availability domains, or using the correct optimized OKE images, etc..

I used Pulumi because is very easy to automate and develop some logic automation, the main features are:

- Automatic creation of the VPC with subnetting calculation, you need only to define the supernet CIDR

- Automatic discovery of all availability domains to best configure the OKE pools spreads to all domains.

- Automatic deployment of some stacks on OKE with the Pulumi Kubernetes integration


Any feedback is welcome!