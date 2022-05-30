import logging
import os
from typing import List, Optional

import yaml
from pydantic import BaseModel, ValidationError

logger = logging.getLogger("jobs")


class Line(BaseModel):
    size: float
    text: str
    yoffset: Optional[float]


class Lines(BaseModel):
    lines: List[Line]
    quantity: int
    active: Optional[bool]


class Job(BaseModel):
    name: str
    category: str = "Diverse"
    path: str
    labeltype: str
    cutoff: int
    quantity: Optional[int]
    labels: List[Lines]


class Jobs:
    def __init__(self, path):
        logger.info("Process jobs in %s", path)
        self.path = path
        self.joblist = []
        self.load_jobs()
        logger.info("Processed %d jobs", len(self.joblist))

    def load_jobs(self):
        for root, dirs, files in os.walk(self.path):
            for file in files:
                if file.endswith(".yml"):
                    self.process_jobs(os.path.join(root, file))

    def process_jobs(self, path):
        logger.info("Process %s", path)
        with open(path) as yml:
            job = yaml.load(yml, Loader=yaml.FullLoader)
            job["path"] = path
            try:
                self.joblist.append(Job(**job))
            except ValidationError as e:
                logger.error("Error in %s: %s", path, e)


if __name__ == "__main__":
    j = Jobs(os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "jobs"))
