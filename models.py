from django.db import models
from django.contrib.auth.models import User


class Question(models.Model): 
    """
    Represents a single driving test question.
    This is the 'Parent' table in our database.
    """
    # TextField datatype allows for long questions.
    text = models.TextField()

    # The __str__ method controls how this object looks in the Admin panel.
    # Instead of "Question object (1)", it will show the actual text.
    def __str__(self):
        return self.text

class Choice(models.Model):
    """
    Represents one of the multiple-choice options for a Question.
    This is the 'Child' table. Each choice belongs to one Question.
    """
    # question --> will be converted into a question_id column in the database, which is done automatically by Django.
    ## which links each choice to its parent question.
    # ForeignKey links this Choice to a specific Question.
    # related_name='choices' lets us grab all choices for a question easily later.
    # on_delete=models.CASCADE is a safety rule, which means: "If the Question is deleted, delete these choices too."
    question = models.ForeignKey(Question, related_name='choices', on_delete=models.CASCADE)
    
    # CharField datatype is used for shorter texts, and it require a max_length.
    text = models.CharField(max_length=300)
    
    # BooleanField is True (1) if this is the right answer, False (0) otherwise.
    is_correct = models.BooleanField(default=False)

    # Instead of "Choice object (1)", it will show the actual text.
    def __str__(self):
        return f"{self.text} (Correct: {self.is_correct})"

class ExamResult(models.Model):
    """
    Stores the history of a user's attempt at the exam.
    """
    # Links the result to a specific User (the person who logged in).
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # The number of correct answers.
    score = models.IntegerField()
    
    # Did they meet the 80% threshold?
    passed = models.BooleanField()
    
    # Automatically saves the exact time the test finished (auto_now_add sets this automatically)
    date_taken = models.DateTimeField(auto_now_add=True)