import logging
import os
from datetime import datetime as dt
from ftplib import FTP
from pathlib import Path

from jobs import Jobs
from labels import Labels

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("main")

BASEPATH = Path(os.path.join(os.path.abspath(os.path.dirname(__file__)))).parent


class LabelTool:
    def __init__(self):
        self.setup()
        self.labels = Labels(os.path.join(BASEPATH, "labels"))
        self.jobs = Jobs(os.path.join(BASEPATH, "jobs"))

    @staticmethod
    def setup():
        """Create folders if they do not yet exist."""
        Path(os.path.join(BASEPATH, "labels")).mkdir(parents=True, exist_ok=True)
        Path(os.path.join(BASEPATH, "jobs")).mkdir(parents=True, exist_ok=True)
        Path(os.path.join(BASEPATH, "output")).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def calculate_label_settings(label):
        """Generate label settings like dimensions, offsets etc."""
        ptype = "l1"  # Durchlichtabtastung
        xo = label.xoffset
        yo = label.yoffset
        ho = label.height
        dy = label.height + label.xgap
        wd = (label.width * label.quantity) + (label.xgap * (label.quantity - 1))
        name = label.type
        return f"S {ptype};{xo},{yo},{ho},{dy},{wd};{name}\n"

    @staticmethod
    def print_speed_temperature(label):
        """Generate print speed and print temperature settings."""
        h = label.printspeed
        t = label.temperature
        return f"H {h},{t}\n"

    @staticmethod
    def options():
        """Static: Option Printmode backfeed optimized."""
        return f"O P\n"

    @staticmethod
    def cutter():
        """Static. Cut at the end of the job."""
        return f"C e\n"

    @staticmethod
    def labelcount():
        """Static. Always 1 as we calculate labelpositions our selves and don't use CAB label counters."""
        return f"A 1\n\n"

    @staticmethod
    def comment(job):
        """Generate comment."""
        return f";{'='*30}\n;{'Job path:':<12} {job.path}\n;{'Job name:':<12} {job.name}\n;{'Labeltype:':<12} {job.labeltype}\n;{'='*30}\n\n"

    @staticmethod
    def jobname(job):
        """Generate job name."""
        return f"J {job.name}\n"

    @staticmethod
    def calculate_label_position(labeltype, label, counter):
        """Calculates the position of the textboxes for all lines of a label."""
        lines = []
        x = (labeltype.width * counter) + (labeltype.xgap * counter)
        r = "0"
        font = "3"  # Swiss 721TM
        width = labeltype.width
        y = 0
        for line in label.lines:
            y += line.size
            if line.yoffset:
                y += line.yoffset
            fontsize = line.size
            text = line.text
            lines.append(f"T {x},{y},{r},{font},{fontsize};{text}[J:c{width}]\n")
        return lines

    def calculate_labels(self, job, labeltype):
        """Calculate textboxes for all labels"""
        labelcounter = 0
        labels = []
        for label in job.labels:
            for l in range(0, label.quantity):
                labels.append(
                    self.calculate_label_position(labeltype, label, labelcounter)
                )
                if labelcounter < labeltype.quantity - 1:
                    labelcounter += 1
                else:
                    labelcounter = 0
        return labels

    @staticmethod
    def filename(job):
        """Generate file name for print file."""
        return f"{dt.now().strftime('%Y-%m-%d-%H-%M-%S')}-{job.name}.txt"

    def generate_print_file(self, job_id):
        """Generate the printfile that is sent to the printer."""
        # Exit if no valid job id is passed in
        if len(self.jobs.joblist) < job_id:
            logger.error("Invalid job ID %s", job_id)
            return
        job = self.jobs.joblist[job_id]
        # Exit if labeltype defined in job is not in loaded labeltypes
        if not job.labeltype in self.labels.labels:
            logger.error("Invalid label type %s for job ID %s", job.labeltype, job_id)
            return
        labeltype = self.labels.labels[job.labeltype]

        xcounter = 0
        ycounter = 0
        label_end = False
        printfile = os.path.join(BASEPATH, "output", self.filename(job))
        with open(printfile, "w") as f:
            f.write(self.comment(job))
            for label in self.calculate_labels(job, labeltype):
                label_end = False
                if xcounter == 0:
                    f.write(self.jobname(job))
                    f.write(self.print_speed_temperature(labeltype))
                    f.write(self.calculate_label_settings(labeltype))
                    f.write(self.options())
                for line in label:
                    f.write(line)
                xcounter += 1
                if xcounter == labeltype.quantity:
                    ycounter += 1
                    if ycounter == job.cutoff:
                        f.write(self.cutter())
                    f.write(self.labelcount())
                    xcounter = 0
                    label_end = True
            if not label_end:
                f.write(self.cutter())
                f.write(self.labelcount())
        return printfile

    @staticmethod
    def send_printfile(path, ip="192.168.3.53", user="root", pin="0000"):
        ftp = FTP(ip)
        ftp.login(user, pin, "")
        ftp.cwd("execute")
        with open(path, "rb") as f:
            ftp.storbinary("STOR job.txt", f)


if __name__ == "__main__":
    lt = LabelTool()
    f = lt.generate_print_file(1)
    lt.send_printfile(f)
