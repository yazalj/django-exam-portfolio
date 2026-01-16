import pandas as pd
from django.core.management.base import BaseCommand
from exam_app.models import Question, Choice

class Command(BaseCommand):
    """
    Custom Django Management Command to load data from TWO CSV files.
    Usage: python manage.py load_exam_data
    """
    help = 'Loads questions and choices from two separate CSV files'

    def handle(self, *args, **kwargs):
        # Files to read
        questions_file = 'driving_questions-1.csv'
        answers_file = 'driving_answers_improved-1.csv'

        self.stdout.write("Reading CSV files...")

        # 1. Read the CSVs using Pandas
        # Note: We use delimiter=';' because our file uses semicolons, not commas.
        try:
            df_questions = pd.read_csv(questions_file, delimiter=';')
            df_answers = pd.read_csv(answers_file, delimiter=';')
        except FileNotFoundError as e:
            self.stdout.write(self.style.ERROR(f"Error: Could not find file. {e}"))
            return

        self.stdout.write("Cleaning old database data...")

        # Delete old questions (this automatically deletes choices too because of on_delete=CASCADE in models.py)
        ## so if we run this script twice we would not get duplicate questions
        # 1. Question.objects: Access the tool that manages Question data.
        # 2. .all(): Select EVERY question in the database.
        # 3. .delete(): Delete them all.
        Question.objects.all().delete()

        self.stdout.write(f"Processing {len(df_questions)} questions and {len(df_answers)} answers...")

        # --- THE MAPPING LOGIC ---
        # We need to link the answers to the questions.
        # We will create a dictionary to store the "Real Database Object" for each "CSV ID".
        # Format: { csv_id : Question_Database_Object }
        question_dictionary = {}

        # 2. Load Questions Firstly
        # df_questions has columns named 'question_id' and 'question_text'
        # iterrows(): Loops through the table one row at a time.
        for index, row in df_questions.iterrows():
            csv_id = row['question_id']
            csv_content = row['question_text']
            
            # Create the question in the database
            # This let SQLite3 assigns it a brand new, Real Database ID.
            # text is the destination column in our Question model.
            # csv_content is the source, which is the text from our CSV file.
            q_object = Question.objects.create(text=csv_content)
            
            # Store it in the dictionary so we can find it later when loading answers
            # for example the output will be: question_dictionary[1] = <Question Object (Database ID: 55)>
            question_dictionary[csv_id] = q_object

        # 3. Load Answers Secondly
        for index, row in df_answers.iterrows():
            # Get the ID of the question this answer belongs to
            target_question_id = row['question_id']
            
            # Find the real database object using our dictionary
            # Check if the target_question_id exists in our dictionary to prevent errors
            if target_question_id in question_dictionary:
                # [] Match target_question_id inside the list of keys and then assign the Value to parent_question_object.
                parent_question_object = question_dictionary[target_question_id]
        
                # Then It creates the choice in the database and links it to such question Real Database ID set by SQLite3.
                Choice.objects.create(
                    # question is the Foreign Key column in the Choice database (question_id)
                    question=parent_question_object,
                    text=row['answer_text'],
                    is_correct=bool(row['is_correct'])
                )

        self.stdout.write(self.style.SUCCESS(f"Success! Loaded {Question.objects.count()} questions and {Choice.objects.count()} choices."))