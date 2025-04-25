# Oracle kubernetes engine deploy project (OKED)

## Automated Kubernetes Cluster Deployment on Oracle Cloud Infrastructure up and running in minutes

This tool provides a simple way to automate the deployment of an OKE cluster on Oracle Cloud Infrastructure, including all requirements, without stress.

It is useful for starting without extensive expertise or as a foundation code ready to extend.

Demo:

![Demo](demo.gif)

## Why OKED?

The main requirements that motivated me to develop this code are as follows:

- **Simplicity**: Up and running in minutes without any prompt and OCI expertise.
- **Working**: Most online examples available are complex to understand and non-functional.
- **Well-architected**: Best security practices included based on the well written [OCI article](https://docs.oracle.com/en-us/iaas/Content/ContEng/Concepts/contengnetworkconfigexample.htm#example-oci-cni-publick8sapi_privateworkers_publiclb)

The main features that differentiate this tool from the oci web console wizard and other terraform projects are:

- Automatic creation of the VCN with subnetting calculation; you only need to define the supernet CIDR.
- Automatic discovery and configuration of all availability domains to spreaded nodes and obtain the maximum availability.
- Automatic discovery and configuration of the latest, correct and optimized OKE node image to use.
- Kubernetes config file automagically generated, ready to use, for example, with `export KUBECONFIG=$PWD/kubeconfig`.
- Easily extendible script based on well-known open-source Pulumi framework

## Architecture deployed with oracle-kubernetes-engine-deploy

The architecture defined is based on the well written [OCI article](https://docs.oracle.com/en-us/iaas/Content/ContEng/Concepts/contengnetworkconfigexample.htm#example-oci-cni-publick8sapi_privateworkers_publiclb)

![The complete architecture](arch.png)

OKE cluster is depolyed as [BASIC](https://docs.oracle.com/en-us/iaas/Content/ContEng/Tasks/contengcomparingenhancedwithbasicclusters_topic.htm) cluster type with no costs.

Costs depending on shape type and nodes selected, please estimate the correct costs with the [Cost estimator page](https://www.oracle.com/cloud/costestimator.html).

The default settings deploy a simple cluster leveraging the [Oracle Cloud Free Tier](https://www.oracle.com/cloud/free/) with NO COST, leveraging the [Oracle Cloud Free Tier](https://www.oracle.com/cloud/free/) (2 VM ARM Ampere A1 Compute).

## Prerequisites

1. Install Pulumi CLI - https://www.pulumi.com/docs/get-started/install/
2. Install Python - https://www.python.org/downloads/
3. Install OCI CLI - https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm
4. Oracle credentilas for Pulumi - https://www.pulumi.com/registry/packages/oci/installation-configuration/

### Environment set-up

Clone this repository and downloads all Python requirements.

```bash
git clone https://github.com/enricopesce/oracle-kubernetes-engine-deploy.git
cd oracle-kubernetes-engine-deploy
python -m venv .venv
source .venv/bin/activate
pip install poetry
pulumi install
```

## Configuring the stack

Optional: Use local state file (if you don't save your data on pulumi cloud)

```bash
mkdir oci-stack-statefile
pulumi login file://oci-stack-statefile
```

Initialize the pulumi stack

```bash
pulumi stack init testing
```

There are some configurations necessary to personalize the stack configuration.

Required config:

```bash
pulumi config set compartment_ocid "ocid1.compartment.oc1..aaaaaaaaqqu7dsadsadsadsdsdasdsdasdsad" # compartment ocid example
```

Optional configs:

```bash
pulumi config set vcn_cidr_block "10.0.0.0/16" # the supernet
pulumi config set node_shape "VM.Standard.E5.Flex" # the shape type
pulumi config set kubernetes_version "v1.29.1" # the supported OKE kubernetes version
pulumi config set oke_min_nodes "3" # minimal Kubernetes nodes
pulumi config set oke_ocpus "2" # OCPU numbers per node
pulumi config set oke_memory_in_gbs "32" # RAM memory per node
pulumi config set ssh_key "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC7Q8zBoB...." # ssh key content
```

I suggest you to use all options to best fit you requirements, all default settings are saved on Pulumi.yaml file.

you can display all configurations set via the following command

```bash
pulumi config
KEY                 VALUE
compartment_ocid    ocid1.compartment.oc1..aaaaaaaaqqu7dsadsadsadsdsdasdsdasdsad
kubernetes_version  v1.29.1
node_image_id
node_shape          VM.Standard.A1.Flex
oke_memory_in_gbs   32
oke_min_nodes       3
oke_ocpus           2
ssh_key             ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC7...
vcn_cidr_block      10.0.0.0/16
pulumi:tags         {"pulumi:template":"python"}
```

## Deploy the stack

The deployment phase is very easy:

```bash
pulumi up
```

The creation needs 10/15 minutes

## Configure kubectl

When the deployment is done, you can use directly the kubeconfig file created in the same path or copy where you prefer

```bash
chmod 600 kubeconfig
export KUBECONFIG=$PWD/kubeconfig
kubectl get pods -A

NAMESPACE     NAME                                   READY   STATUS    RESTARTS   AGE
kube-system   coredns-6d9c47d4f7-8pm78               1/1     Running   0          2m28s
kube-system   coredns-6d9c47d4f7-f85j5               1/1     Running   0          6m29s
kube-system   coredns-6d9c47d4f7-l8xwm               1/1     Running   0          2m28s
kube-system   csi-oci-node-fvmlj                     1/1     Running   0          4m21s
kube-system   csi-oci-node-gwsjb                     1/1     Running   0          4m42s
kube-system   csi-oci-node-lsztr                     1/1     Running   0          4m17s
kube-system   kube-dns-autoscaler-6c6897cd78-vpvqj   1/1     Running   0          6m28s
kube-system   kube-proxy-45bdm                       1/1     Running   0          4m17s
kube-system   kube-proxy-hkqnl                       1/1     Running   0          4m42s
kube-system   kube-proxy-zmcwn                       1/1     Running   0          4m21s
kube-system   proxymux-client-6z6hk                  1/1     Running   0          4m42s
kube-system   proxymux-client-c6lct                  1/1     Running   0          4m17s
kube-system   proxymux-client-sh2qd                  1/1     Running   0          4m21s
kube-system   vcn-native-ip-cni-bh8jn                1/1     Running   0          4m21s
kube-system   vcn-native-ip-cni-tlnfw                1/1     Running   0          4m42s
kube-system   vcn-native-ip-cni-xl74b                1/1     Running   0          4m17s
```

## Destroy the stack

Before destroying the Pulumi stack, delete the possible resources created by OKE, such as application load balancer (via OCI Console ) or clean the Kubernetes services (Using kubectl)

```bash
pulumi destroy
```

## Feedback and improvements

I'm always looking for feedback and contributions, so feel free to collaborate on the repository or open an issue with any request!
