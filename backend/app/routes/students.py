from flask import Blueprint, jsonify, request

from ..models import Appointment, ExamRecord, Makeup

students_bp = Blueprint("students", __name__, url_prefix="/api/students")


def _merge_unique(list_a, list_b):
    seen = set()
    merged = []
    for item in list_a + list_b:
        if item.id not in seen:
            seen.add(item.id)
            merged.append(item)
    return merged


@students_bp.get("/trajectory")
def get_student_trajectory():
    id_number = request.args.get("idNumber", "").strip()
    student_name = request.args.get("studentName", "").strip()

    if not id_number and not student_name:
        return jsonify({"message": "请提供证件号或学员姓名"}), 400

    appointments = []
    exam_records = []
    makeups = []

    idn_appointments, idn_exams, idn_makeups = [], [], []
    name_appointments, name_exams, name_makeups = [], [], []

    if id_number:
        idn_appointments = Appointment.query.filter_by(id_number=id_number).all()
        idn_exams = ExamRecord.query.filter_by(id_number=id_number).all()
        idn_makeups = Makeup.query.filter_by(id_number=id_number).all()

    if student_name:
        name_appointments = Appointment.query.filter(
            Appointment.student_name == student_name
        ).all()
        name_exams = ExamRecord.query.filter(
            ExamRecord.student_name == student_name
        ).all()
        name_makeups = Makeup.query.filter(
            Makeup.student_name == student_name
        ).all()

    appointments = _merge_unique(idn_appointments, name_appointments)
    exam_records = _merge_unique(idn_exams, name_exams)
    makeups = _merge_unique(idn_makeups, name_makeups)

    exam_id_to_index = {}

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

    for idx, rec in enumerate(exam_records):
        item = {
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
        timeline.append(item)
        exam_id_to_index[rec.id] = len(timeline) - 1

    for mk in makeups:
        item = {
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
            "sourceExamId": mk.source_exam_id,
            "raw": mk.to_dict(),
        }
        if mk.source_exam_id and mk.source_exam_id in exam_id_to_index:
            exam_idx = exam_id_to_index[mk.source_exam_id]
            exam_item = timeline[exam_idx]
            group_key = f"group-exam-{mk.source_exam_id}"
            exam_item["groupId"] = group_key
            exam_item["groupRole"] = "head"
            item["groupId"] = group_key
            item["groupRole"] = "tail"
            item["sourceExamIndex"] = exam_idx
        timeline.append(item)

    timeline.sort(key=lambda item: (item["datetime"], 0 if item["type"] == "exam" else 1))

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
        if not final_id_number and exam_records[0].id_number:
            final_id_number = exam_records[0].id_number
    if makeups and not final_student_name:
        final_student_name = makeups[0].student_name
        if not final_id_number and makeups[0].id_number:
            final_id_number = makeups[0].id_number

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
