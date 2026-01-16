from django.shortcuts import render # The connecter between HTML files and python data
from django.contrib.auth.decorators import login_required # Forces the user to be logged in before accessing the exam
from .models import Question, ExamResult, Choice
import random # The random module to select random questions

"""
The logic for taking the exam.
"""
@login_required # This decorator forces the user to login before seeing this page.
def take_exam(request):
    """
    Displays the exam form and handles the submission.
    """
    if request.method == 'POST':
        ### Nearly all Django developers put POST before GET, because they prioritize handling user input
        # --- SCORING LOGIC --- (POST request)
        score = 0
        # We loop through every item submitted in the form
        for key, value in request.POST.items():
            if key.startswith('question_'):
                # The value is the ID of the chosen answer (Choice ID)
                choice_id = int(value)
                # Check if this choice is correct in the DB
                selected_choice = Choice.objects.get(id=choice_id)
                if selected_choice.is_correct:
                    score += 1
        
        # Calculate Pass/Fail (Need 16 out of 20)
        passed = score >= 16
        
        # Save to Database
        ExamResult.objects.create(user=request.user, score=score, passed=passed)
        
        # Send them to the results page
        return render(request, 'exam_app/result.html', {'score': score, 'passed': passed})

    else:
        # --- DISPLAY LOGIC --- (GET request)
        # Because of the ForeignKey in the Choice model, we get the choices for each question,
        ## with no need to load the choices again here.
        
        # 1. Get all question IDs
        all_ids = list(Question.objects.values_list('id', flat=True))
        
        # 2. Pick 20 random IDs
        # (Use min to avoid errors if we have fewer than 20 questions loaded)
        random_ids = random.sample(all_ids, min(len(all_ids), 20))
        
        # 3. Fetch the actual Question objects
        questions = Question.objects.filter(id__in=random_ids)
        
        return render(request, 'exam_app/exam.html', {'questions': questions})