"""Generates SYNTHETIC demo data (template-assembled, not real students). The 'label' column is the intended sentiment of each template,
so it is only a smoke-test of the evaluation page, not evidence of real-world accuracy."""
import random, csv, json
random.seed(7)
P = ["The faculty explains concepts clearly and with good examples.", "Labs and practical sessions were very useful.", "Notes and recordings were easy to access.", "The instructor is approachable and answers my doubts patiently.",
     "The course is well organized and the schedule was followed.", "Lectures were engaging and interesting.", "The syllabus is relevant and up to date.", "Exams were fair and the grading was transparent."]
N = ["The teaching pace is too fast to follow.", "Assignments are excessive and deadlines are too tight.", "Learning resources are insufficient and notes are outdated.", "Doubts are rarely addressed in class.",
     "The classes were boring and the content felt outdated.", "Exams were unfair and the grading is not transparent.", "The course is disorganized and classes are often cancelled.", "Not enough practical sessions or labs."]
U = ["The class meets on Mondays and Wednesdays.", "The course has four units.", "Attendance was taken every day."]
rows = []
for sem in ("2025-Fall", "2026-Spring"):
    for course, fac in (("Data Structures", "Faculty A"), ("Machine Learning", "Faculty B"), ("Databases", "Faculty C")):
        for i in range(14):
            k = random.random()
            if k < .45: t, l = random.choice(P), "Positive"
            elif k < .8: t, l = random.choice(N), "Negative"
            elif k < .9: t, l = random.choice(U), "Neutral"
            else: t, l = random.choice(P) + " But " + random.choice(N)[0].lower() + random.choice(N)[1:], "Negative"
            if course == "Machine Learning" and sem == "2025-Fall" and random.random() < .5: t, l = N[0], "Negative"
            rows.append({"feedback": t, "course": course, "faculty": fac, "semester": sem, "date": f"{2025 if 'Fall' in sem else 2026}-{random.randint(8,11) if 'Fall' in sem else random.randint(2,5):02d}-{random.randint(1,28):02d}", "rating": random.randint(1,5), "label": l})
with open("sample_data/sample_feedback.csv", "w", newline="") as f:
    w = csv.DictWriter(f, rows[0].keys()); w.writeheader(); w.writerows(rows)
import pandas as pd
pd.DataFrame([{"student_comment": r["feedback"], "subject_name": r["course"], "instructor_name": r["faculty"]} for r in rows[:30]]).to_excel("sample_data/sample_feedback_alt_columns.xlsx", index=False)
open("sample_data/sample_feedback.txt", "w").write("\n".join(r["feedback"] for r in rows[:20]) + "\nContact me at student@uni.edu or 9876543210 about this.\n")
json.dump([{k: v for k, v in r.items() if k != "label"} for r in rows[:25]], open("sample_data/sample_feedback.json", "w"), indent=1)
print(len(rows), "rows")
