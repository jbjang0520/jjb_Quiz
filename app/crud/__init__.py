from .quiz import CRUDQuiz, quiz_crud
from .user import user
from .question import CRUDQuestion, question_crud

# Quiz 모델을 먼저 임포트해야 합니다.
from app.models.quiz import Quiz

# CRUDQuiz 클래스 정의
quiz_crud = CRUDQuiz(Quiz)

# Question 모델을 먼저 임포트해야 합니다.
from app.models.question import Question

# CRUDQuestion 클래스 정의
question_crud = CRUDQuestion(Question)