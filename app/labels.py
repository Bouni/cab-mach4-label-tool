import logging
import os

import yaml
from pydantic import BaseModel, ValidationError

logger = logging.getLogger("labels")


class Label(BaseModel):
    type: str
    description: str
    path: str
    quantity: int
    width: float
    xgap: float
    height: float
    ygap: float
    xoffset: float
    yoffset: float
    printspeed: int
    temperature: int


class Labels:
    def __init__(self, path):
        logger.info("Process labels in %s", path)
        self.path = path
        self.labels = {}
        self.load_labels()
        logger.info("Processed %d labels", len(self.labels))

    def load_labels(self):
        for root, dirs, files in os.walk(self.path):
            for file in files:
                if file.endswith(".yml"):
                    self.process_label(os.path.join(root, file))

    def process_label(self, path):
        logger.info("Process %s", path)
        with open(path) as yml:
            label = yaml.load(yml, Loader=yaml.FullLoader)
            label["path"] = path
            try:
                if label["type"] in self.labels:
                    logger.warning(
                        "Label %s already loaded from %s, skip %s",
                        label["type"],
                        self.labels[label["type"]].path,
                        path,
                    )
                    return
                self.labels[label["type"]] = Label(**label)
            except ValidationError as e:
                logger.error("Error in %s: %s", path, e)


if __name__ == "__main__":
    l = Labels(os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "labels"))
