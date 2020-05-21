---
title: Pythonic infrastructure diagrams
date: 2020-05-21T22:00:43+00:00
author: paolo
layout: post
permalink: /2020/05/21/pythonic-infrastructure-diagrams/
categories:
  - en-US
tags:
  - infrastructure
  - python
---

# Pythonic infrastructure diagram

I've been designing and analyzing a lot of architectures lately and I felt the need for a tool to export images quick, so that I could add them to the documentations, or just to show a concept to someone else, but I am far from at least a decent graphic designer. So I decided to search google for "diagram as code" and, well, I found many crazy options, but one of them caught my attention, as it was a python library: [**Diagrams**](https://diagrams.mingrammer.com)!

It's great that I don't even need to leave the python interpreter to draw things and it's very simples to use it. As an example, I'll design the architecture of my [**ASI**](https://github.com/paoloo/asi) project:

```python
from diagrams import Cluster, Diagram, Edge
from diagrams.aws.network import ELB
from diagrams.aws.devtools import Codebuild, Codedeploy
from diagrams.aws.compute import Fargate, ECR, ECS
from diagrams.onprem.vcs import Github
from diagrams.aws.storage import S3
from diagrams.aws.management import Cloudwatch
from diagrams.aws.database import RDS
with Diagram(name="ASI", show=False):
    with Cluster("Continuous Delivery"):
        with Cluster("webhook"):
            gh = Github("PUSH")
        with Cluster(""):
            ecr = ECR("ECR")
            fargate = Fargate("Fargate")
            s3 = S3("artifacts")
            delivery = [ecr, fargate, s3]
        with Cluster("CodePipeline"):
            gh >> Codebuild("CodeBuild") >> Codedeploy("CodeDeploy") >> delivery
    lb = ELB("load balancer")
    with Cluster("VPC"):
        app = ECS("ECS")
        db = RDS("database")
        app - Edge(color="brown", style="dotted") - db
    lb >> app << fargate
    app >> Cloudwatch("CloudWatch")
```

Just that, and the result is:

[<img src="{{ site.baseurl }}/uploads/2020/05/diagram.jpg" alt="" width="300" />]({{ site.baseurl }}/uploads/2020/05/diagram.jpg)

I'll try to create a library later to integrate and self generate terraform templates from the design script. Thay may be very handy in the future.

