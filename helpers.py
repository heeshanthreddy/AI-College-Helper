import sqlite3
from datetime import datetime, date
import math, re, json
from config import STOP_WORDS
from db import get_connection

def get_cgpa(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    overall_points = 0
    overall_credits = 0
    cursor.execute(
        "SELECT id FROM semesters WHERE user_id=%s",
        (user_id,)
    )
    semesters = cursor.fetchall()
    for semester in semesters:
        semester_id = semester[0]
        cursor.execute(
            """
            SELECT credits, grade
            FROM subjects
            WHERE semester_id=%s
            """,
            (semester_id,)
        )
        subjects = cursor.fetchall()
        for credits, grade in subjects:
            overall_points += credits * grade
            overall_credits += credits
    conn.close()
    if overall_credits == 0:
        return 0
    return round(overall_points / overall_credits, 2)

def get_current_semester(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM semesters WHERE user_id=%s ORDER BY semester_no DESC LIMIT 1", 
        (user_id,)
    )
    existing_semester = cursor.fetchone()
    if existing_semester is None:
        return None
    current_semester = existing_semester[0]
    current_semester_no = existing_semester[1]
    return { "semester_id": current_semester, "semester_no": current_semester_no }

def get_task_stats(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM tasks WHERE user_id=%s",
        (user_id,)
    )
    total_tasks = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM tasks WHERE user_id=%s AND status=0",
        (user_id,)
    )
    pending_tasks = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM tasks WHERE user_id=%s AND status=1",
        (user_id,)
    )
    completed_tasks = cursor.fetchone()[0]
    if total_tasks > 0:
        completion_rate = round((completed_tasks / total_tasks) * 100,2)
    else:
        completion_rate = 0
    if total_tasks == 0:
        task_message = "📝 No tasks created yet."
    elif pending_tasks == 0:
        task_message = "🎉 All tasks completed."
    elif pending_tasks == 1:
        task_message = f"🎉 Only {pending_tasks} task remaining."
    elif  pending_tasks <= 3:
        task_message = f"⚡ Only {pending_tasks} tasks remaining."
    else:
        task_message = f"⚠ You have {pending_tasks} pending tasks."

    if total_tasks > 0:
        task_score = (completed_tasks / total_tasks) * 30
    else:
        task_score = 0
    conn.close()
    return { "total_tasks": total_tasks, "pending_tasks": pending_tasks, "completed_tasks": completed_tasks , "completion_rate": completion_rate,"task_message": task_message,"task_score": task_score, "all_completed": pending_tasks == 0 }

def get_assignment_stats(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT assignment_name, subject, due_date, priority FROM assignments WHERE user_id=%s AND status=0 """,
        (user_id,)
    )
    pending_assignments = cursor.fetchall()
    cursor.execute(
        """SELECT COUNT(*) FROM assignments WHERE user_id=%s AND status=1 """,
        (user_id,)
    )
    completed_assignments = cursor.fetchone()[0]
    cursor.execute(
        """SELECT COUNT(*) FROM assignments WHERE user_id=%s  """,
        (user_id,)
    )
    total_assignments = cursor.fetchone()[0]
    assignment_analytics = []
    today = date.today()
    assignment_penalty = 0
    overdue_count = 0
    for item in pending_assignments:
        assignment_name = item[0]
        subject = item[1]
        due_date = item[2]
        priority = item[3]
        days_left = (due_date - today).days
        if days_left < 0:
            overdue_count += 1
            message = f"❌  Overdue by {abs(days_left)} days"
            assignment_penalty += 5
        elif days_left == 0:
            message = "🚨 Due Today"
        elif days_left == 1:
            message = f"⚠️ Due Tomorrow"
        elif days_left <= 7:
            message = f"✅ Due in {days_left} days"
        else:
            message = f"📅 Due in {days_left} days"
        assignment_analytics.append({ "assignment_name": assignment_name, "subject": subject, "priority": priority, "days_left": days_left, "message": message})
    pending_assignments_count = len(pending_assignments)
        
    if total_assignments > 0:
        assignment_score = (completed_assignments/ total_assignments) * 40
    else:
        assignment_score = 0
    return { "pending_assignments": pending_assignments_count, "completed_assignments": completed_assignments, "total_assignments": total_assignments, "assignment_analytics": assignment_analytics, "assignment_penalty": assignment_penalty, "overdue_count": overdue_count,"assignment_score": assignment_score }

def get_attendance_stats(user_id, semester_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
    """ SELECT timetable.subject_name,
           SUM(CASE WHEN attendance.status = 1 THEN 1 ELSE 0 END) AS present,
           SUM(CASE WHEN attendance.status = 0 THEN 1 ELSE 0 END) AS absent,
           SUM(CASE WHEN attendance.status IN (0,1) THEN 1 ELSE 0 END) AS held
        FROM attendance
        JOIN timetable
        ON attendance.timetable_id = timetable.id
        WHERE attendance.user_id = %s AND timetable.semester_id = %s
        GROUP BY timetable.subject_name """,
        (user_id, semester_id)
    )
    attendance_summary = cursor.fetchall()
    no_of_subjects=len(attendance_summary)
    analytics_data = []
    total_percentage = 0
    attendance_penalty = 0
    low_attendance_subjects = []
    for item in attendance_summary:
        subject_name = item[0]
        present = item[1]
        absent = item[2]
        held = item[3]
        if held > 0:
            percentage = round((present / held) * 100, 2)
            total_percentage += percentage
        else:
            percentage = 0
        if held == 0:
            status = "No classes held yet"
        elif percentage >= 75:
            can_miss = int((present - 0.75 * held) / 0.75)
            status = f"✅ Can miss {can_miss} more classes"
        else:
            need_attend = math.ceil((0.75 * held - present) / 0.25)
            status = f"⚠ Need {need_attend} consecutive classes"
            attendance_penalty += 5
            low_attendance_subjects.append(subject_name)
        analytics_data.append({ "subject": subject_name, "present": present, "absent": absent, "percentage": percentage,"status": status})
    if no_of_subjects > 0:
        average_attendance = total_percentage / no_of_subjects
    else:
        average_attendance = 0
    attendance_score = (average_attendance / 100) * 40
    return { "attendance_summary": analytics_data, "average_attendance": average_attendance, "attendance_score": attendance_score, "attendance_penalty": attendance_penalty, "low_attendance_subjects": low_attendance_subjects,
    "excellent_attendance" : attendance_penalty == 0 }

def get_student_context(user_id):
    
    task_stats = get_task_stats(user_id)
    semester = get_current_semester(user_id)
    assignment_stats = get_assignment_stats(user_id)
    attendance_stats = get_attendance_stats( user_id, semester["semester_id"])
    productivity_score =  task_stats["task_score"] + assignment_stats["assignment_score"] + attendance_stats["attendance_score"]
    penalty = assignment_stats["assignment_penalty"] + attendance_stats["attendance_penalty"]
    productivity_score -=penalty
    productivity_score = round( max(0, min(100, productivity_score)),2 )
    if productivity_score >= 80:
        health = "🟢 Excellent"
    elif productivity_score >= 60:
        health = "🟡 Good"
    elif productivity_score >= 40:
        health = "🟠 Needs Improvement"
    else:
        health = "🔴 Critical"
    return { "semester": semester, "task_stats": task_stats, "assignment_stats": assignment_stats, "attendance_stats": attendance_stats, "productivity_score": productivity_score, "health": health }

def get_productivity_history(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT score, record_date, user_id
        FROM productivity_history
        WHERE user_id=%s
        ORDER BY record_date
        """,
        (user_id,)
    )
    details = cursor.fetchall()
    dates = []
    scores = []
    for detail in details:
        scores.append(detail[0])
        dates.append(detail[1])
    conn.close()
    return { "dates": dates, "scores": scores }

def update_productivity_history(user_id, productivity_score):
    conn = get_connection()
    cursor = conn.cursor()
    today = date.today()
    cursor.execute(
        """
        SELECT id
        FROM productivity_history
        WHERE user_id=%s AND record_date=%s
        """,
        (user_id, today)
    )
    existing_record = cursor.fetchone()
    if existing_record is None:
        cursor.execute(
            """
            INSERT INTO productivity_history
            (user_id, score, record_date)
            VALUES (%s, %s, %s)
            """,
            (user_id, productivity_score, date.today())
        )
    else:
        cursor.execute(
            """
            UPDATE productivity_history
            SET score=%s
            WHERE user_id=%s AND record_date=%s
            """,
            ( productivity_score, user_id, today )
        )
    conn.commit()
    conn.close() 
def get_today_timetable(user_id, semester_id):
    today_day = datetime.now().weekday() + 1
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
    """SELECT subject_name, start_time, end_time
        FROM timetable
        WHERE user_id=%s AND semester_id=%s AND day=%s
        ORDER BY start_time """,
        (user_id, semester_id, today_day)
    )
    classes = cursor.fetchall()
    today_classes = []
    for item in classes:
        today_classes.append( { "subject": item[0], "start": item[1], "end": item[2] } )
    conn.close()
    return today_classes

def get_today_tasks(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT task
        FROM tasks
        WHERE user_id=%s AND status=0
        LIMIT 5
    """,
    (user_id,))
    rows = cursor.fetchall()
    today_tasks = []
    for row in rows:
        today_tasks.append({ "task": row[0] })
    conn.close()
    return today_tasks

def get_notes_context(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT subject, extracted_text
            FROM notes
            WHERE user_id=%s
        """,
        (user_id,)
    )
    notes = cursor.fetchall()
    notes_summary = []
    for note in notes:
        subject = note[0]
        text = note[1] if note[1] else ""
        notes_summary.append({
            "subject": subject,
            "coverage": len(text.split()),
            "text": text[:1000]
        })
    conn.close()
    return { "notes": notes_summary, "total_notes": len(notes_summary) }

def get_today_assignments(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """ SELECT assignment_name, subject, due_date, priority
        FROM assignments
        WHERE user_id=%s
        AND status=0
        ORDER BY due_date ASC, priority DESC
        LIMIT 5""", 
        (user_id,)
    )
    rows = cursor.fetchall()
    today = date.today()
    assignments = []
    for row in rows:
        due_date = row[2]
        days_left = (due_date - today).days
        assignments.append({
            "assignment": row[0],
            "subject": row[1],
            "due_date": row[2],
            "days_left": days_left,
            "priority": row[3]
        })
    conn.close()
    return assignments

def get_today_information(user_id,semester_id):
    today = date.today()
    day = today.strftime("%A")
    is_weekend = day in ["Saturday", "Sunday"]
    recommended_sleep = "11:00 PM"
    recommended_wakeup = "6:30 AM"
    today_classes = get_today_timetable(user_id, semester_id)
    college_hours = 0
    recommended_sessions=0
    for item in today_classes:
        start = datetime.strptime(item["start"], "%H:%M")
        end = datetime.strptime(item["end"], "%H:%M")
        duration = (end - start).seconds / 3600
        college_hours += duration
    awake_hours = 16
    meal_break_hours = 4
    available_study_hours = awake_hours - college_hours - meal_break_hours
    available_study_hours = max(2, min(6, round(available_study_hours)))  # Cap study hours between 2 and 6 so the planner remains realistic. Even on holidays we avoid overwhelming schedules, and on busy days we still encourage at least 2 productive hours.
    if available_study_hours <= 3:
        recommended_sessions = 2
    elif available_study_hours <= 5:
        recommended_sessions = 3
    else:
        recommended_sessions = 4
    free_time_slots = [
        { "start":"06:30", "end":"07:30", "energy":"High", "recommended_focus":"Learning difficult concepts" },
        { "start":"09:15", "end":"11:30", "energy":"High", "recommended_focus":"Assignments and difficult practice"},
        { "start":"14:15", "end":"16:30", "energy":"Medium", "recommended_focus":"Coding practice and revision" },
        { "start":"17:00", "end":"19:15", "energy":"Medium", "recommended_focus":"Pending tasks" },
        { "start":"21:00", "end":"22:30", "energy":"Low", "recommended_focus":"Revision and note reading" }
    ]

    meal_timings = { "breakfast":"07:30-09:00", "lunch":"12:00-14:00", "dinner":"19:30-21:00" }
    return { "day": day, "date": str(today), "is_weekend": is_weekend, "college_hours": college_hours, "available_study_hours": available_study_hours, "free_time_slots": free_time_slots, "recommended_sleep": recommended_sleep, "recommended_wakeup": recommended_wakeup, "meal_timings": meal_timings, "recommended_sessions": recommended_sessions }

def remove_meal_times(free_slots):
    meal_times = [
        ("07:30", "09:00"),   # Breakfast
        ("12:00", "14:00"),   # Lunch
        ("17:00", "18:00"),   # Snacks
        ("19:30", "21:00")    # Dinner
    ]
    updated_slots = []
    for slot in free_slots:
        slot_start, slot_end = slot.split(" - ")
        slot_start = datetime.strptime(slot_start, "%H:%M")
        slot_end = datetime.strptime(slot_end, "%H:%M")
        current_slots = [(slot_start, slot_end)]
        for meal_start, meal_end in meal_times:
            meal_start = datetime.strptime(meal_start, "%H:%M")
            meal_end = datetime.strptime(meal_end, "%H:%M")
            new_slots = []
            for start, end in current_slots:
                if meal_end <= start or meal_start >= end:     # we are ensuring there is no overlap
                    new_slots.append((start, end))
                else:
                    
                    if start < meal_start:                      # Slot before meal
                        new_slots.append((start, meal_start))
                    
                    if meal_end < end:                          # Slot after meal
                        new_slots.append((meal_end, end))
            current_slots = new_slots

        for start, end in current_slots:
            duration = (end - start).total_seconds() / 60
            if duration >= 60:
                updated_slots.append( f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')}" )
    return updated_slots

def get_planner_context(user_id):
    semester = get_current_semester(user_id)
    if semester is None:
        return None
    today = datetime.now().strftime("%A")
    today_day = datetime.now().weekday() + 1
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
            SELECT subject_name, start_time, end_time
            FROM timetable
            WHERE user_id=%s AND semester_id=%s AND day=%s
            ORDER BY start_time
        """,
        ( user_id, semester["semester_id"], today_day)
    )

    classes = cursor.fetchall()
    free_slots = calculate_free_slots(classes)
    if today in ["Saturday", "Sunday"]:
        free_slots = [ "09:00 - 11:00", "14:00 - 16:00", "19:00 - 20:00" ]
    planner_context = {
        "student_context": get_student_context(user_id),
        "today_information": get_today_information( user_id, semester["semester_id"] ),
        "today_timetable": get_today_timetable( user_id, semester["semester_id"] ),
        "today_tasks": get_today_tasks(user_id),
        "today_assignments": get_today_assignments(user_id),
        "notes_context": get_notes_context(user_id),
        "productivity_history": get_productivity_history(user_id),
        "available_study_slots": free_slots,
        "is_weekend": today in ["Saturday", "Sunday"]
    }
    conn.close()
    return planner_context

def calculate_free_slots(classes):
    free_slots = []
    day_start = datetime.strptime("08:00", "%H:%M")
    day_end = datetime.strptime("22:00", "%H:%M")
    current = day_start

    for subject, start, end in classes:
        class_start = datetime.strptime(start, "%H:%M")
        class_end = datetime.strptime(end, "%H:%M")
        if current < class_start:
            free_slots.append(
                f"{current.strftime('%H:%M')} - {class_start.strftime('%H:%M')}"
            )
        current = max(current, class_end)

    if current < day_end:
        free_slots.append(
            f"{current.strftime('%H:%M')} - {day_end.strftime('%H:%M')}"
        )
    free_slots = remove_meal_times(free_slots)
    return free_slots

def get_note_text(note_id,user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, subject, file_name, extracted_text FROM notes WHERE id=%s AND user_id=%s ",
        (note_id,user_id)
        )
    details = cursor.fetchone()
    conn.close()
    if details is None:
        return None
    return { "id": details[0], "subject": details[1], "file_name": details[2], "text": details[3] }

def get_summary(note_id, user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT summary_json FROM notes WHERE id=%s AND user_id=%s",
        (note_id, user_id)
    )
    row = cursor.fetchone()
    conn.close()
    if row is None:
        return None
    return row[0]

def save_summary(note_id, user_id, summary):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE notes SET summary_json=%s WHERE id=%s AND user_id=%s", 
        (json.dumps(summary),note_id,user_id)
    )
    conn.commit()
    conn.close()

def get_ai_report(user_id, report_type):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT report_json FROM ai_reports WHERE user_id=%s AND report_type=%s ",
        (user_id,report_type)
    )
    row = cursor.fetchone()
    conn.close()
    if row is None:
        return None
    return row[0]

def save_ai_report(user_id, report_type, report):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM ai_reports WHERE user_id=%s AND report_type=%s",
        (user_id,report_type)
    )
    exists = cursor.fetchone()
    if exists:
        cursor.execute(
            "UPDATE ai_reports SET report_json=%s, generated_at=CURRENT_TIMESTAMP WHERE user_id=%s AND report_type=%s",
            (json.dumps(report),user_id,report_type)
        )
    else:
        cursor.execute(
            "INSERT INTO ai_reports(user_id,report_type,report_json) VALUES(%s, %s, %s)",
            (user_id,report_type,json.dumps(report))
        )
    conn.commit()
    conn.close()

def get_study_plan(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT plan_json FROM study_plans WHERE user_id=%s",
        (user_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if row is None:
        return None
    return row[0]

def save_study_plan(user_id, plan):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM study_plans WHERE user_id=%s",
        (user_id,)
    )
    exists = cursor.fetchone()
    if exists:
        cursor.execute(
            "UPDATE study_plans SET plan_json=%s, generated_at=CURRENT_TIMESTAMP WHERE user_id=%s",
            (json.dumps(plan), user_id)
        )
    else:
        cursor.execute(
            " INSERT INTO study_plans(user_id, plan_json) VALUES(%s, %s)",
            (user_id, json.dumps(plan))
        )
    conn.commit()
    conn.close()

def extract_keywords(question):
    question = question.lower()   # Convert to lowercase
    question = re.sub(r"[^a-z0-9\s]", " ", question)   # Remove punctuation
    words = question.split()     # Split into words
    words = [
        word for word in words
        if word not in STOP_WORDS and len(word) > 1     # Remove stop words and one-letter words
    ]                               
    keywords = []
    keywords.extend(words)   # Single words
    for i in range(len(words) - 1):      # Two-word phrases
        keywords.append(f"{words[i]} {words[i + 1]}")

    for i in range(len(words) - 2):       # Three-word phrases
        keywords.append(f"{words[i]} {words[i + 1]} {words[i + 2]}")

    keywords.sort(key=len, reverse=True)    # Search longer phrases first
    seen = set()          # Remove duplicates while preserving order
    final_keywords = []

    for keyword in keywords:
        if keyword not in seen:
            seen.add(keyword)
            final_keywords.append(keyword)

    return final_keywords

def extract_chunk(text, keywords):
    text_lower = text.lower()
    for keyword in keywords:
        position = text_lower.find(keyword)     # finsing the postion of the keyword
        if position != -1:                    # this is to check thaat the word is present   
            start = max(0, position - 3000)
            end = min(len(text), position + 3000)  # we are considering 3000 characters before and after the word
            return text[start:end]
    return text[:6000]  # if no keyword is  found we will return beginning instead of crashing

def retrieve_relevant_notes(user_id, question):
    keywords = extract_keywords(question)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT file_name, extracted_text FROM notes WHERE user_id=%s ",
        (user_id,)
    )
    notes = cursor.fetchall()
    conn.close()
    ranked_notes = []
    for file_name, text in notes:
        if not text:
            continue
        text_lower = text.lower()
        score = 0
        for keyword in keywords:
            occurrences = text_lower.count(keyword)
            if " " in keyword:
                score += occurrences * 3
            else:
                score += occurrences
        if score > 0:
            chunk = extract_chunk(text, keywords)
            ranked_notes.append({ "file_name": file_name, "text": chunk, "score": score })
    ranked_notes.sort( key=lambda note: note["score"], reverse=True )  # we are sorting in decreasing order
    return ranked_notes[:3]    # we are retreiving only the top 3 filenames and texts