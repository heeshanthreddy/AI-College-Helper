import json, re
from config import client

def parse_json_response(response):
    if not response.text:
        raise ValueError("Empty response received from Gemini.")
    
    text = response.text.strip()
    # Remove markdown code fences if Gemini adds them
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    return json.loads(text)

def generate_ai_report(student_context):
    prompt = f"""
    You are an experienced academic advisor helping a college student.
    Below is the student's current academic information.
    {student_context}
    Analyze the student's academic performance.
    Return ONLY valid JSON.
    {{
        "overall_status":"",
        "summary":"",
        "strengths":[],
        "weaknesses":[],
        "priority_actions":[],
        "recommendations":[],
        "motivation":""
    }}
    Important Rules:

        1. Return ONLY valid JSON.
        2. The JSON must be directly parseable using Python's json.loads().
        3. Do not include markdown.
        4. Do not include ```json.
        5. Do not include explanations before or after JSON.
        6. Be concise.
        7. Summary must be at most 3 sentences.
        8. Maximum 15 words per bullet.
        9. Do not repeat information across sections.
        10. Weaknesses should not contain recommendations.
        11. Recommendations should contain long-term improvements.
        12. Priority Actions should contain immediate actions.
        13. Motivation should reference at least one student strength whenever possible.
        14. Only use the information in student_context.
        15. overall_status must be exactly one of:
            Excellent
            Good
            Needs Improvement
            Critical
    """

    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    report = parse_json_response(response)
    return report

def generate_study_plan(planner_context):
    prompt = f"""
        You are an experienced academic mentor.
        Below is today's complete student information.
        {planner_context}
    Your job is to generate today's personalized study plan.

    Objectives:
        - Help the student improve academics without burnout.
        - Create a realistic plan.
        - Never overload the student.
        - Balance study, rest and meals.
    Use the provided information carefully.

    Planning Rules:
        • Never schedule study during college classes.
        • Respect the provided meal timings.
        • Use ONLY the provided free_slots from planner_context.
        • Never create study sessions outside the provided free_slots.
        • Ignore free slots shorter than 45 minutes.
        • If a free slot is between 45 and 90 minutes, schedule at most one study session.
        • If a free slot is longer than 90 minutes, you may divide it into multiple realistic sessions with short breaks.
        • Schedule study sessions in chronological order from morning to night.

        Planner Modes:
            If recent productivity is low:
                → Recovery Mode
                - Shorter study sessions
                - More breaks
                - Motivation first
            If recent productivity is high:
                → Performance Mode
                - Longer focus sessions
                - Challenging work first

        Daily Missions:
        Generate EXACTLY 3 daily missions.
        Example:
            - Finish TOC Assignment
            - Attend all TOC classes
            - Revise Autoencoders

        Study Schedule:
            Generate at most 6 study sessions.
            Each study session must fit completely inside one of the provided free_slots.
            Never overlap with:
                • Classes
                • Meal timings
            If there is insufficient free time, reduce the number of study sessions instead of forcing additional sessions.

        Tips:
            Give 3-5 concise practical study tips.

        Coach Message:
            Write one encouraging coach message.Maximum 40 words.
            Keep it positive, practical and personalized.
            Do not repeat information already present in the schedule or tips.
            On weekends, encourage both productive study and healthy relaxation.

        Reasoning:
            Briefly explain how today's timetable, assignments, productivity and attendance influenced this plan.

        Weekend Rules:
            If is_weekend is true:
                • Use only the provided available_study_slots.
                • Create a balanced day with study and personal time.
                • Prioritize pending assignments and unfinished tasks.
                • Prefer revision before introducing difficult new topics.
                • Leave enough free time for relaxation or hobbies.

    Return ONLY valid JSON.

    {{
        "planner_mode":"",
        "coach_message":"",
        "daily_missions":[],
        "schedule":[
            {{
                "time":"",
                "activity":"",
                "duration":"",
                "reason":""
            }}
        ],
        "tips":[],
        "reasoning":[]
    }}

    Rules:
        1. Return ONLY JSON.
        2. No Markdown.
        3. No explanations.
        4. No ```json.
        5. Use ONLY provided planner_context.
        6. Do NOT invent subjects.
        7. Do NOT invent assignments.
        8. Do NOT invent attendance.
        9. Maximum 6 study sessions.
        10. Every session must include a reason.
        11. Keep every sentence concise.
        12. Keep every bullet under 15 words.
        13. Make today's plan achievable.
        14. Never modify, extend or invent free time beyond the provided free_slots.
        15. Distribute study sessions naturally across the available free_slots instead of clustering them together.
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    plan = parse_json_response(response)
    return plan

def generate_note_summary(note):
    prompt = f"""
        You are an experienced Engineering Professor and Exam Mentor.
        Below is one student's uploaded engineering note.
        {note}
        Your job is to generate a concise, exam-oriented revision guide.

        IMPORTANT:

            • Keep answers short.
            • Focus on scoring marks in university exams.
            • Do NOT generate unnecessary paragraphs.
            • Use only the uploaded note.
            • If a section is not applicable, return an empty list.
            • Never invent topics not present in the notes.

        For programming notes:
            • Explain important algorithms and code logic simply.
            • Generate coding interview / university style coding questions.
            • Mention time complexity only if present or directly relevant.

        For mathematical notes:
            • Include formulas.
            • Mention important derivations.
            • Mention shortcuts where possible.

        For circuit subjects:
            • Mention important equations.
            • Mention derivations.
            • Mention applications.

        Exam Questions should resemble real university end-semester examination questions.
        Avoid generic textbook questions.

        For derivations:
        • Mention only derivations worth preparing for exams.

        For theoretical subjects:
            • Focus on definitions, comparisons, applications and limitations and Frequently confused concepts.

        Examples:
            • Explain...
            • Derive...
            • Compare...
            • Solve...
            • Write an algorithm...
            • Design...
            • Implement...
            • Draw...
            • Justify...
            • Calculate...

        Return ONLY valid JSON.

        {{
            "summary":"",
            "key_points":[],
            "important_topics":[],
            "definitions":[],
            "formula_sheet":[],
            "derivations":[
                            {{
                                "topic":"",
                                "importance":"",
                                "memory_hint":""
                            }}
                        ],
            "code_explanations":[
                            {{
                                "topic":"",
                                "difficulty":"",
                                "idea":"",
                                "complexity":""
                            }}
                        ],
            "applications":[],
            "limitations":[],
            "common_mistakes":[],
            "memory_tricks":[],
            "prerequisites":[],
            "frequently_confused_with":[],
            "exam_questions":{{
                "theory":[],
                "applications":[],
                "problem_solving":[],
                "coding":[],
                "derivations":[],
                "comparisons":[]
            }},
            "exam_tips":[]
        }}
        Rules:

            1. Return ONLY JSON.
            2. No Markdown.
            3. No explanations.
            4. No ```json.
            5. Maximum 80 words for summary.
            6. Maximum 8 key points.
            7. Maximum 8 important topics.
            8. Maximum 8 definitions.
            9. Maximum 10 formulas.
            10. Maximum 5 derivations.
            11. Maximum 5 code explanations.
            12. Maximum 8 applications.
            13. Maximum 8 limitations.
            14. Maximum 8 common mistakes.
            15. Maximum 8 memory tricks.
            16. Maximum 6 questions in each exam category.
            17. Maximum 6 exam tips.
            18. Keep every bullet under 20 words.
            19. Never repeat the same information.
            20. Empty list if not applicable.
            21.Exam tips should be specific to this note. Avoid generic advice like "Practice regularly."
    """
    response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )
    summary = parse_json_response(response)
    return summary

def generate_weekly_review(student_context):
    prompt = f"""
        You are an experienced Academic Mentor.
        Below is a student's complete academic data.
        {student_context}
        Your job is to generate a Weekly Academic Review.

        IMPORTANT

            • Never write long paragraphs.
            • Prefer bullet points.
            • Keep every point under 20 words.
            • Keep explanations under 2 sentences.
            • Focus on practical improvements.
            • Never invent information.
            • Base every suggestion only on the supplied data.
            • Keep the report easy to scan in under 30 seconds.

        Return ONLY valid JSON.

        {{
            "overall_score": 0,
            "overall_rating": "",
            "overall_verdict": "",

            "biggest_achievement": "",
            "biggest_concern": "",

            "subject_spotlight":
                {{
                    "best_subject":"",
                    "needs_attention":""
            }},

            "weekly_wins": [],
            "next_week_goals": [],
            "study_suggestions": [],
            "weekly_challenge":"",

            "semester_risk":
                {{
                    "level":"",
                    "reason":""
                }},

            "focus_meter":
                {{
                    "assignments":0,
                    "attendance":0,
                    "revision":0
                }},

            "motivation":""
        }}

    Rules

        1. Return ONLY JSON.
        2. No markdown.
        3. No ```json.
        4. Score between 0 and 100.
        5. Maximum 5 Weekly Wins.
        6. Maximum 5 Goals.
        7. Maximum 5 Suggestions.
        8. Motivation under 40 words.
        9. Verdict under 40 words.
        10. Challenge should be achievable within one week.
        11. Never repeat information.
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return parse_json_response(response)

def generate_doubt_solver(question, context):
    prompt = f"""
        You are an academic assistant.
        Your job is to answer the student's question ONLY using the retrieved study notes.
        Question:
            {question}

        Retrieved Notes:
            {context}

        Return ONLY valid JSON.
            {{
                "answer_found": true,
                "answer": "",
                "confidence": "",
                "summary": ""
            }}

        Instructions:

                1. Return ONLY valid JSON.
                2. Keep the answer concise but complete.
                3. Do NOT return ```json.
                4. Answer ONLY using the retrieved notes.
                5. Never use outside knowledge.
                6. Never guess or assume missing information.
                7. If the answer is not present in the notes:
                    - answer_found = false
                    - answer = "I couldn't find the answer in your uploaded notes."
                    - confidence = "None"
                8. If the answer is present:
                    - answer_found = true
                9. Start the answer with one direct sentence answering the question.
                10. Then explain the concept clearly and keep answer student friendly.
                10. Use short paragraphs.
                11. Leave only ONE blank line between paragraphs.
                12. Do NOT insert multiple consecutive blank lines.
                13. Use bullet points wherever appropriate.
                14. Do NOT add unnecessary whitespace.
                15. Use valid Markdown formatting.
                16. For every bullet list, leave one blank line before the first bullet.
                    Correct formatting:

                        Architecture consists of:

                        - Encoder
                        - Decoder
                        - Bottleneck

                        Applications include:

                        - Compression
                        - Denoising
                        - Feature Learning

                        Do NOT write

                        Architecture consists of:
                        - Encoder
                        - Decoder
                17. Do not place bullet points immediately after a sentence without a blank line.
                18. Include examples ONLY if they are present in the retrieved notes.
                19. Do NOT mention source files anywhere in the answer.
                20. Do NOT mention that you used notes or retrieved context.
                22. confidence must be exactly one of:
                    - High
                    - Medium
                    - Low
                    - None
            """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return parse_json_response(response)