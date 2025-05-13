import json
from pathlib import Path
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.quiz import Quiz
from app.models.question import Question
from app.models.option import Option

def load_data():
    file_path = Path(__file__).parent / "data.json"
    with open(file_path, encoding="utf-8") as f:
        return json.load(f)

def seed_from_json():
    db: Session = SessionLocal()
    data = load_data()
    owner_id = 1  # 관리자 번호 설정

    for quiz_data in data["quizzes"]:
        quiz = Quiz(
            title=quiz_data["title"],
            description=quiz_data["description"],
            questions_per_quiz=quiz_data["questions_per_quiz"],
            randomize_questions=quiz_data["randomize_questions"],
            randomize_options=quiz_data["randomize_options"],
            created_by=owner_id,
            is_active=True
        )
        db.add(quiz)
        db.flush()

        for i, q_data in enumerate(quiz_data["questions"]):
            question = Question(content=q_data["content"], quiz_id=quiz.id, order_index=i)
            db.add(question)
            db.flush()

            for j, opt in enumerate(q_data["options"]):
                option = Option(
                    content=opt["content"],
                    is_correct=opt["is_correct"],
                    question_id=question.id,
                    order_index=j
                )
                db.add(option)

    db.commit()
    db.close()

if __name__ == "__main__":
    seed_from_json()