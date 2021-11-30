from flask import Blueprint
from flask import jsonify, request, render_template
import os
import json

from src.base import RequirementsGenerator, generate_tree

bp = Blueprint("foutes", __name__, url_prefix="/")


# generate requirements.txt(main)
@bp.route("/generate", methods=["POST"])
def generate():
    language = request.form["language"]
    selected_dirs = request.form["dir_list"]
    dirs = list(set(selected_dirs.split(",")))

    for dir in dirs:
        RequirementsGenerator(dir, language)

    return jsonify()

# update directory information
@bp.route("/update", methods=["POST"])
def update():
    generate_tree()
    return jsonify()

# get selected directory detail
@bp.route("/detail", methods=["POST"])
def detail():
    selected_dirs = request.form["dir_list"]
    dirs = list(set(selected_dirs.split(",")))
    detail_data = {"detail_data": ""}
    return jsonify(values=json.dumps(detail_data))

# base
@bp.route("/")
def base():
    if not os.path.exists(f"{os.getcwd()}\\static\\tree.json"):
        generate_tree()

    lang_data = {lang.capitalize(): lang for lang in settings["languages"]}
    return render_template("main.html", data=lang_data)


# Global variables are currently more efficient. maybe...
data = open(f"{os.getcwd()}\\src\\settings.json", "r")
settings = json.load(data)