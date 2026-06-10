from flask import Blueprint, jsonify, request

from ..models import ExamRecord

scores_bp = Blueprint("scores", __name__, url_prefix="/api/scores")


@scores_bp.get("")
def list_scores():
    student_name = request.args.get("studentName")
    id_number = request.args.get("idNumber")
    subject = request.args.get("subject")
    query = ExamRecord.query.order_by(ExamRecord.submitted_at.desc())
    if student_name:
        query = query.filter(ExamRecord.student_name.contains(student_name))
    if id_number:
        query = query.filter(ExamRecord.id_number == id_number)
    if subject:
        query = query.filter_by(subject=subject)
    return jsonify([record.to_dict() for record in query.all()])
