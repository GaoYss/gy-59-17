from flask import Blueprint, jsonify, request

from ..models import Appointment, ExamRecord, Makeup

students_bp = Blueprint("students", __name__, url_prefix="/api/students")


@students_bp.get("/trajectory")
def get_student_trajectory():
    id_number = request.args.get("idNumber", "").strip()
    student_name = request.args.get("studentName", "").strip()

    if not id_number and not student_name:
        return jsonify({"message": "请提供证件号或学员姓名"}), 400

    appointments = []
    exam_records = []
    makeups = []

    if id_number:
        appointments = Appointment.query.filter_by(id_number=id_number).all()
        exam_records = ExamRecord.query.filter_by(id_number=id_number).all()
        makeups = Makeup.query.filter_by(id_number=id_number).all()

    if student_name:
        if not appointments:
            appointments = Appointment.query.filter(
                Appointment.student_name == student_name
            ).all()
        if not exam_records:
            exam_records = ExamRecord.query.filter(
                ExamRecord.student_name == student_name
            ).all()
        if not makeups:
            makeups = Makeup.query.filter(
                Makeup.student_name == student_name
            ).all()

    timeline = []

    for apt in appointments:
        timeline.append(
            {
                "type": "appointment",
                "id": apt.id,
                "date": apt.exam_date.isoformat(),
                "datetime": apt.created_at.isoformat(timespec="seconds"),
                "subject": apt.subject,
                "title": f"{apt.subject} - 考试预约",
                "description": f"预约时段：{apt.exam_date.isoformat()} {apt.timeslot}",
                "status": apt.status,
                "timeslot": apt.timeslot,
                "raw": apt.to_dict(),
            }
        )

    for rec in exam_records:
        timeline.append(
            {
                "type": "exam",
                "id": rec.id,
                "date": rec.submitted_at.date().isoformat(),
                "datetime": rec.submitted_at.isoformat(timespec="seconds"),
                "subject": rec.subject,
                "title": f"{rec.subject} - 模拟考试",
                "description": f"得分：{rec.score}分（答对 {rec.correct_count}/{rec.total_questions} 题）",
                "status": "合格" if rec.passed else "不合格",
                "score": rec.score,
                "passed": rec.passed,
                "raw": rec.to_dict(),
            }
        )

    for mk in makeups:
        timeline.append(
            {
                "type": "makeup",
                "id": mk.id,
                "date": (mk.scheduled_date.isoformat() if mk.scheduled_date else mk.created_at.date().isoformat()),
                "datetime": mk.created_at.isoformat(timespec="seconds"),
                "subject": mk.original_subject,
                "title": f"{mk.original_subject} - 补考",
                "description": (
                    f"不及格分数：{mk.failed_score}分"
                    + (f" | 安排日期：{mk.scheduled_date.isoformat()}" if mk.scheduled_date else "")
                    + (f" | 备注：{mk.notes}" if mk.notes else "")
                ),
                "status": mk.status,
                "failedScore": mk.failed_score,
                "scheduledDate": mk.scheduled_date.isoformat() if mk.scheduled_date else None,
                "raw": mk.to_dict(),
            }
        )

    timeline.sort(key=lambda item: item["datetime"])

    result_appointments = sorted([a.to_dict() for a in appointments], key=lambda x: x["createdAt"])
    result_exams = sorted([e.to_dict() for e in exam_records], key=lambda x: x["submittedAt"])
    result_makeups = sorted([m.to_dict() for m in makeups], key=lambda x: x["createdAt"])

    summary = {
        "totalAppointments": len(result_appointments),
        "totalExams": len(result_exams),
        "passedExams": sum(1 for e in result_exams if e["passed"]),
        "failedExams": sum(1 for e in result_exams if not e["passed"]),
        "totalMakeups": len(result_makeups),
        "pendingMakeups": sum(1 for m in result_makeups if m["status"] in ["待安排", "已安排"]),
    }

    final_student_name = ""
    final_id_number = id_number or ""
    if appointments:
        final_student_name = appointments[0].student_name
        if not final_id_number:
            final_id_number = appointments[0].id_number
    if exam_records and not final_student_name:
        final_student_name = exam_records[0].student_name
    if makeups and not final_student_name:
        final_student_name = makeups[0].student_name

    return jsonify(
        {
            "student": {
                "studentName": final_student_name,
                "idNumber": final_id_number,
            },
            "summary": summary,
            "timeline": timeline,
            "appointments": result_appointments,
            "exams": result_exams,
            "makeups": result_makeups,
        }
    )
