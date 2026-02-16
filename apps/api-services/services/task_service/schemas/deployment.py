from typing import List
from pydantic import BaseModel, Field


class DeploymentConfigSchema(BaseModel):
    """Schema for deployment configuration"""

    name: str = Field(..., description="Unique deployment name")
    flow_name: str = Field(..., description="Prefect flow name")
    docker_image: str = Field(..., description="Docker image with tag")
    work_pool_name: str = Field(..., description="Prefect work pool name")
    tags: List[str] = Field(default_factory=list, description="Deployment tags")
    concurrency: int = Field(default=10, description="Max concurrent runs")
    active: bool = Field(default=True, description="Deployment is active")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Execute Run",
                "flow_name": "process-run-flow",
                "docker_image": "bom.ocir.io/bmttln9csnzu/call-task:3.4.21.v2",
                "work_pool_name": "call-work-pool",
                "tags": ["call", "production"],
                "concurrency": 10,
            }
        }
