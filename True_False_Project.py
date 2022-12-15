#####The True/False Project#####

#########################################################################
#parts:
#1. Creating the question class
#2. Creating the list of Questions objects from the data
#3. The QuizBrain and the next_question method
#4. How to continue showing new questions
#5. Checking answers and keeping score
#########################################################################
question_data = [
    {"text": "A slug's blood is green.", "answer": "True"},
    {"text": "The loudest animal is the African Elephant.", "answer": "False"},
    {"text": "Approximately one quarter of human bones are in the feet.", "answer": "True"},
    {"text": "The total surface area of a human lungs is the size of a football pitch.", "answer": "True"},
    {"text": "In West Virginia, USA, if you accidentally hit an animal with your car, you are free to take it home to eat.", "answer": "True"},
    {"text": "In London, UK, if you happen to die in the House of Parliament, you are entitled to a state funeral.", "answer": "False"},
    {"text": "It is illegal to pee in the Ocean in Portugal.", "answer": "True"},
    {"text": "You can lead a cow down stairs but not up stairs.", "answer": "False"},
    {"text": "Google was originally called 'Backrub'.", "answer": "True"},
    {"text": "Buzz Aldrin's mother's maiden name was 'Moon'.", "answer": "True"},
    {"text": "No piece of square dry paper can be folded in half more than 7 times.", "answer": "False"},
    {"text": "A few ounces of chocolate can to kill a small dog.", "answer": "True"}
    ]





####################
# from data import question_data
# from quiz_brain import QuizBrain
# from question_model import Question
# from quiz_brain import *
# from data import *
# from question_model import *


######################
#########################################################################
#1. Creating the question class
class Question:
    def __init__(self, q_text, q_answer):
#setting the values:
        self.text = q_text
        self.answer = q_answer
#testing code
# new_q =  Question("jhndsfkjhkjsdhfg", "hckjxhask")
#print(new_q.text)
#########################################################################

#########################################################################
#2. Creating the list of Questions objects from the data
question_bank = []

for question in question_data:
    question_text = question["text"]
    question_answer = question["answer"]
    new_question = Question(question_text, question_answer)
    question_bank.append(new_question)

# print(question_bank)
quiz = QuizBrain(question_bank)

while quiz.still_has_questions():
    quiz.next_question()

print("You've completed the quiz.")
print(f"Your final score was: {len(question_bank)}")
print(f"Your final score was: {quiz.score} / {quiz.question_number}")

#########################################################################
#3. The QuizBrain and the next_question method
class QuizBrain:
    def __init__(self, q_list):
        self.question_number = 0
        self.score = 0
        self.question_list = q_list
#4. How to continue showing new questions
    def still_has_questions(self):
        return self.question_number < len(self.question_list)
        #     return True
        # else:
        #     False
    
    def next_question(self):
        current_question = self.question_list[self.question_number]
        self.question_number += 1
        user_answer = input(f"Q. {self.question_number}: {current_question.text} (True/False): ")
        self.check_answer(user_answer, current_question.answer)
#5. Checking answers and keeping score
    def check_answer(self, user_answer, correct_answer):
        if user_answer.lower() == correct_answer.lower():
            self.score += 1
            print("You got it right!")
        else:
            print("Sorry, that's incorrect.")
        print(f"the correct answer was: {correct_answer}")
        print(f"Your current score is: {self.score}/{self.question_number}")
        #gives the end user a little bit more space when running the game
        print("\n")
#########################################################################

