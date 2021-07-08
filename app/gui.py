from flask import Flask, jsonify, render_template, request

from jobs import Job
from labeltool import LabelTool

labeltool = LabelTool()


class CustomFlask(Flask):
    jinja_options = Flask.jinja_options.copy()
    jinja_options.update(
        dict(
            block_start_string="<%",
            block_end_string="%>",
            variable_start_string="%%",
            variable_end_string="%%",
            comment_start_string="<#",
            comment_end_string="#>",
        )
    )


app = CustomFlask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/reload")
def reload():
    labeltool.load_data()
    return jsonify(True)


@app.route("/labels")
def labels():
    labels = {
        key: labeltool.labels.labels[key].dict() for key in labeltool.labels.labels
    }
    return jsonify(labels=labels)


@app.route("/jobs")
def jobs():
    jobs = [job.dict() for job in labeltool.jobs.joblist]
    return jsonify(jobs=jobs)


@app.route("/print", methods=["POST"])
def printjob():
    job = Job(**request.get_json())
    path = labeltool.generate_print_file(job)
    labeltool.send_printfile(path)
    return jsonify(True)


if __name__ == "__main__":
    app.run("0.0.0.0", 5000, debug=True)
