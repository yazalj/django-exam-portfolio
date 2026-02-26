# --- IMPORTS ---
from django.shortcuts import render # The connecter between HTML files and python data
from django.contrib.auth.decorators import login_required # Forces the user to be logged in before accessing the exam
from django.contrib import messages # Warning messages to the user
from django.http import HttpResponse # Needed for exporting statistics to .txt
from .models import Question, ExamResult, Choice # Importing the database models
import random # The random module to select random questions
import time # Needed for the exam timer
import io # io Activation for data management for Tuna
import base64 # base64 Activation for encoding the chart for HTML for Tuna
import matplotlib.pyplot as plt # Matplotlib Activation for creating stats charts for Tuna
from django.shortcuts import render, redirect  # Redirect activation for the Response Showing from Server
from django.db.models import Avg
import pandas as pd # Pandas Activation for Data Frame Creation for Tuna
import numpy as np # Numpy Activation for Statistics Calculation Tuna
import datetime

EXAM_DURATION = 20 * 60  # 20 minutes (in seconds)


@login_required  # This decorator forces the user to login before seeing this page.
def take_exam(request):
    """
    Displays the exam form and handles the submission. 
    The exam is limited to 20 min and includes analytics for missed questions.
    Input: GET request to show the exam, POST request to submit answers.
    Output: Renders the exam page with questions and timer, or processes the submission and redirects to the statistics page.
    """

    # ---- TIMER ----
    #timer is written in JavaScript code and runs in the browser to update the countdown every second. 
    # Django provides the starting time and exam start time stays the same is session until submission, and JavaScript handles displaying the timer 
    # Try to get the exam start time from the session
    start_time = request.session.get("exam_start_time")
    # If this is the first time the user opens the exam, start the timer
    if start_time is None:
        start_time = time.time()
        request.session["exam_start_time"] = start_time
# for html file in exam.app The time decrease functionality is located on line 48 within the tick() function, where the variable remaining is decremented by one (remaining--;) every second via the recursive setTimeout call on line 49.-->

    elapsed_time = time.time() - start_time  # how much time passed since the exam started
    # Calculate how many seconds are still left; max(0, ...) prevents negative numbers
    remaining_seconds = max(0, EXAM_DURATION - int(elapsed_time))
    
    # --- SCORING LOGIC --- (POST request)
    if request.method == "POST":
        ### Handling user input and calculating score

        # If the user submitted after time expired, show a warning
        if elapsed_time >= EXAM_DURATION:
            messages.warning(request, "Time is up! Exam submitted automatically.")

        score = 0
        # --- Tuna's FEATURE: List to track failed questions ---
        wrong_question_ids = []

        # We loop through every item submitted in the form
        for key, value in request.POST.items():
            if key.startswith('question_'):
                # Extract Question ID to track analytics
                question_id = key.replace('question_', '')
                
                try:
                    # The value is the ID of the chosen answer (Choice ID)
                    choice_id = int(value)
                    ## Check if this choice is correct in the DB
                    ## and ensure the choice actually belongs to the question submitted
                    selected_choice = Choice.objects.get(id=choice_id, question_id=question_id)
                    
                    if selected_choice.is_correct:
                        score += 1
                    else:
                        # --- Tuna's FEATURE: Save the ID of the missed question ---
                        wrong_question_ids.append(str(question_id))
                
                except (ValueError, Choice.DoesNotExist):
                    # If user tampers with the HTML value (e.g., submits "abc" or an invalid ID),
                    # treat it as a wrong answer to prevent a 500 Server Error crash.
                    wrong_question_ids.append(str(question_id))
        
        # Calculate Pass/Fail (Need 16 out of 20)
        passed = score >= 16

        # --- COMBINED SAVE: Including your wrong_questions field ---
        ExamResult.objects.create(
            user=request.user,
            score=score,
            passed=passed,
            wrong_questions=",".join(wrong_question_ids)  # Stores missed IDs as a string
        )

        # Clear session so next exam starts fresh next time
        request.session.pop("exam_start_time", None)
        request.session.pop("exam_question_ids", None)

        # --- Tuna's FEATURE: Automatic redirect to statistics page ---
        return redirect('user_stats')

    # --- DISPLAY LOGIC --- (GET request)
    # Manage random question selection per session
    if "exam_question_ids" not in request.session:
        ## Because of the ForeignKey in the Choice model, we get the choices for each question,
        ## with no need to load the choices again here.
        
        # 1. Get all question IDs
        all_ids = list(Question.objects.values_list("id", flat=True))

        # 2. Pick 20 random IDs
        # (Use min to avoid errors if we have fewer than 20 questions loaded)   
        random_ids = random.sample(all_ids, min(len(all_ids), 20))
        request.session["exam_question_ids"] = random_ids

    else:
        random_ids = request.session["exam_question_ids"]

    # 3. Fetch the actual Question objects
    questions = Question.objects.filter(id__in=random_ids)

    return render(request, "exam_app/exam.html", {
        "questions": questions,
        "remaining_seconds": remaining_seconds
    })

########################################################################################################################
############################################ TUNA YILMAZ ###############################################################
########################################################################################################################
@login_required
def user_statistics_view(request):
    """
        This function processes user exam history to build a performance dashboard. It
        cleans raw data (takes up quantitative and categorical data), calculates metrics
        (such as mean standard deviation etc.), takes precautions against possible errors
        (such as data type and absent data), and generates dynamic charts, line graph, pie
        chart and histograms for the user performance evaluation.

        LOGIC FLOW:
        - DATA (1.A-C): Grabs ExamResult records. Uses Pandas 'errors=coerce' to turn
          corrupted scores into NaNs, then NumPy to calculate Average, Std Dev (Consistency),
          and Max Score safely.
        - DOWNLOAD (2): If 'download' is in GET, it generates a structured .txt report
          on the fly and returns it as an attachment.
        - MISTAKES (3): Extracts wrong question IDs from strings. Uses a set() to avoid
          duplicates and returns an empty list [] if no errors exist to prevent HTML crashes.
        - VISUALS (4-6): Uses Matplotlib (Agg backend) to draw Pie, Line, or Histograms.
          Encodes the result into a Base64 string for direct HTML rendering without disk I/O.
        - OUTPUT (7): Renders 'user_stats.html' with all calculated metrics and the
          encoded chart.
    """

    # --- 1. DATA PROCESSING ---
    # 1.A Data Importation from the ExamResult class in exam_app/models.py filtered by the user and ordered by the date
    user_data = ExamResult.objects.filter(user=request.user).order_by('date_taken')

    # 1... A Small Error Handling Against Absent User Data
    if not user_data.exists():
        return render(request, "exam_app/user_stats.html", {
            "no_data": True,
            "message": "You haven't taken any exams yet. Finish an exam to see your statistics!"
        }) # If no data exists for user_data give the output as above for teh whole page of statistics

    # 1.B Creation of Data from the Imported Data through Pandas according to the # of passes, scores and dates
    df = pd.DataFrame(list(user_data.values('score', 'passed', 'date_taken')))

    # 1.C NumPy for the calculation of Descriptive Statistics
    df['score'] = pd.to_numeric(df['score'], errors='coerce') # creation of a series - array in Pd - object for Numpy via Pandas
    # if non-numeric values encountered converted into NaN
    scores_array = df['score'].dropna().to_numpy() # Creation of a fully numeric array with dropped NaN values
    # Advanced Metrics for the Continuous Data
    total_exams = len(df) # Object for # of data points in data
    avg_score = np.mean(scores_array) if len(scores_array) > 0 else 0 # Average calculation
    std_dev = np.std(scores_array) if len(scores_array) > 0 else 0 # Consistency metric (Standard Deviation) calculation
    max_score = np.max(scores_array) if len(scores_array) > 0 else 0 # Personal best score finding in data

    # Consistency Level based on Standard Deviation
    consistency_score = "High" if std_dev < 2 else "Medium" if std_dev < 4 else "Low"
    # Determination of the constituency score according to the state of the standard deviation

    # Categorical Data: Pass vs Fail Percentages
    passed_count = df['passed'].sum()
    success_rate = (passed_count / total_exams) * 100 if total_exams > 0 else 0
    # Determination of the success_rate according to the percentage of the passed_counts

    # --- 2. DOWNLOAD REPORT ---
    if 'download' in request.GET: # if user requests "download" through GET download the report file as a .txt
        # Step 2.A: Create the header and basic stats list
        # First part of the report with the # of exams taken, average, standard deviation, succes rate, consistency
        report_lines = [
            f"EXAM PERFORMANCE REPORT - {request.user.username.upper()}",
            "=" * 45, # separators
            f"Total Exams Taken: {total_exams}",
            f"Average Score:     {avg_score:.2f} / 20", # .2f => float with 2 decimal points
            f"Standard Deviation: {std_dev:.2f}", # .2f => float with 2 decimal points
            f"Success Rate:      %{success_rate:.1f}", # .1f => float with 1 decimal point
            f"Consistency Level: {consistency_score}", # consistency_score => a qualitative data calculated from std_dev
            "-" * 45, # separators
            "\nDETAILED EXAM HISTORY:" # Title of the second part of the exam
        ]

        # Step 2.B: Add detailed logs using List Comprehension (Your logic!)
        # List of strings for the user for each of the taken exam records in the database
        log_entries = [
            f"- Date: {res.date_taken.strftime('%Y-%m-%d')} | Score: {res.score}/20 | Status: {'Passed' if res.passed else 'Failed'}"
            # All data presented with their corresponding metrics | strftime to convert into %Y-%m-%d format
            for res in user_data]

        # Step 2.C: Combine all lines into the main list
        report_lines.extend(log_entries) # append the log_entries list to the end of report_lines
        report_lines.append("\n" + "=" * 45) # seperator
        report_lines.append("END OF REPORT") # terminal of the report

        # Step 2.D: Join all lines with a newline character to create one large string
        final_report_text = "\n".join(report_lines)
        # log_entries appended report_lines list is separated line by line through "\n".join method

        # Step 2.E: Create the HTTP Response for file download
        # 'text/plain' informs the browser about the content of file as a text file but not an HTML file
        response = HttpResponse(final_report_text, content_type='text/plain') # a text - not an HTML - is response for HTML

        # 'attachment' downloads to PC instead of displaying on HTML
        filename = f"Performance_Report_{request.user.username}.txt" # setting up the filename for the download file
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        # attachment is the response type that activates saves as rather than display the object = filename here

        return response

    # --- 3. IDENTIFY MISTAKES: Analyze wrong question IDs from previous exams ---
    all_wrong_ids = [] # creation of a list for all the wrong answers of a user so far

    for res in user_data:
        # check if there are any recorded wrong questions for this exam
        if res.wrong_questions:
            # IDs are stored as a string, split them by comma and add to list.
            all_wrong_ids.extend(res.wrong_questions.split(','))

    # set() function to remove duplicate IDs from the list  from all_wrong_ids and give a pure list = all_wrong_ids
    unique_wrong_ids = set(all_wrong_ids)
    if unique_wrong_ids:
    # fetch question objects from the database according to the unique IDs and give them as list failed_questions
        failed_questions = Question.objects.filter(id__in=unique_wrong_ids)
    else: failed_questions = []

    # --- 4. PREPARE CHART: Determine the visualization type from the URL query parameters. ---
    chart_type = request.GET.get('chart_type', 'pie')
    # If no type is specified it defaults to 'pie'.
    failed_count = total_exams - passed_count # calculation of failed_count from passed_count and tota_exams
    # passed_count was already calculated at 1.C as a metric
    scores = df['score'].tolist() # listing of pandas data frame for matplotlib

    # --- 5. DATA VISUALIZATION: Generate charts using Matplotlib ---
    # Usage of 'Agg' backend to run in a non-GUI environment (ideal for web servers)
    plt.switch_backend('Agg') # Anti-Grain Geometry => Creation of an image without window
    plt.clf()  # Clear the current figure to prevent overlapping plots
    plt.figure(figsize=(8, 5))  # For the figure size adjustment

    if chart_type == 'histogram': # If histogram is chosen on the HTML file
        # Create a histogram to visualize the distribution of exam scores from scores object
        # 'bins' define the intervals, 'alpha' adds slight transparency
        plt.hist(scores, bins=5, color='skyblue', edgecolor='black', alpha=0.8)
        # Bins = number of intervals on a histogram | alpha = colour intensity
        plt.title("Score Distribution Across Exams", fontsize=14)
        plt.xlabel("Score (Out of 20)")
        plt.ylabel("Number of Exams")

    elif chart_type == 'line':
        # Create a line graph for the changes of success rates of the user over the tests taken
        trial_numbers = list(range(1, len(df) + 1)) # Assignment of trial numbers through the length +1 of df
        plt.plot(trial_numbers, df['score'], marker='o', color='purple', linewidth=2)
        # Takes the trial_numbers as x-axis data | takes the score data array as the y-axis data
        # marker for the adjustment of the data point shape
        plt.title("Your Progress Over Time", fontsize=14)
        plt.xlabel("Number of Exams")
        plt.ylabel("Score")
        plt.grid(True, linestyle='--', alpha=0.6)

    else:
        # Create a pie chart for the comparison of Passing vs. Failing counts
        plt.pie([passed_count, failed_count], labels=['Pass', 'Fail'],
                autopct='%1.1f%%', colors=['green', 'red'], startangle=140)
        # 'autopct' formats the percentage labels
        # - '1.1f': Display as a float (f) with 1 digit after the decimal.
        # - '%%': Appends percentage sign to the value.
        plt.title("Overall Pass/Fail Ratio", fontsize=14)

    # Adjust layout to make sure titles and labels don't get cut off
    plt.tight_layout()

    # 6. --- IMAGE ENCODING: Convert the plot into a Base64 string for HTML rendering ---
    buffer = io.BytesIO()
    # Initialization of an in-memory byte stream to capture the image data without disk I/O
    plt.savefig(buffer, format='png')
    # Rendering and exporting the Matplotlib plot into the buffer in PNG format
    buffer.seek(0)  # Reset buffer pointer to the beginning
    # Rewinding the buffer pointer to the start to ensure the full data stream is read

    chart_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    # Encode the raw binary data to a Base64 string for direct embedding in an HTML <img> tag
    # This converts the binary image into a UTF-8 compatible ASCII string
    buffer.close()
    # Shut the buffer off

    # 7. --- SHOW ON SCREEN: Send everything to the 'user_stats.html' page. ---
    return render(request, "exam_app/user_stats.html", {
        "chart": chart_base64, # # Base64 encoded string representing the generated plot image for inline HTML rendering.
        "chart_type": chart_type, # the chosen chart_type from pie - line - hist | assigned in part 4 and 5
        "failed_questions": failed_questions,  # List of Wrong Answered Questions. | assigned in part 3
        "avg_score": avg_score,  # Mean for the Specific User | assigned in part 1
        "std_dev": std_dev,  # Standard Deviation | assigned in part 1
        "max_score": max_score,  # Maximum Score | assigned in part 1
        "consistency": consistency_score,  # Consistency Score | assigned in part 1
        "total_exams": total_exams, # number of total exams | assigned in part 1
        "success_rate": success_rate,  # Success Rate | assigned in part 1
    })