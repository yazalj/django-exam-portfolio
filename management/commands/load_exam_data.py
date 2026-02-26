import pandas as pd
from django.core.management.base import BaseCommand
from exam_app.models import Question, Choice

class Command(BaseCommand):
    """
    Custom Django Management Command to load data from a CSV file to the database.
    Usage: python manage.py load_exam_data
    Input: A CSV file named 'final_exam_data.csv' in the root directory, which contains merged question and answer data.
    Output: Populates the Question and Choice tables in the database with the data from the CSV file.
    """
    help = 'Loads exam data from a single merged CSV file'

    def handle(self, *args, **kwargs):
        # 1. Read the new single CSV file
        file_path = 'final_exam_data.csv'
        self.stdout.write(f"Reading {file_path}...")
        
        try:
            # Read the file (using semicolon delimiter)
            # Note: We use delimiter=';' because our file uses semicolons, not commas.
            df = pd.read_csv(file_path, delimiter=';')
            
            # Validate that the necessary columns actually exist
            required_cols = ['question_text', 'answer_text', 'is_correct']
            if not all(col in df.columns for col in required_cols):
                raise KeyError(f"Missing one or more required columns: {required_cols}")

        except FileNotFoundError as e:
            self.stdout.write(self.style.ERROR(f"Error: Could not find file. {e}"))
            return    
        except pd.errors.EmptyDataError:
            self.stdout.write(self.style.ERROR("Error: The CSV file is empty."))
            return
        except KeyError as e:
            self.stdout.write(self.style.ERROR(f"Data format error: {e}"))
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Unexpected file reading error: {e}"))
            return

        # 2. Clean the database
        # We delete all existing questions to start fresh.
        # This automatically deletes linked Choices (Cascade delete).
        self.stdout.write("Cleaning old data...")
        Question.objects.all().delete()
        
        # 3. Loop through every row in the CSV
        self.stdout.write("Importing new data...")
        
        # iterrows(): Loops through the table one row at a time.
        try:
            for index, row in df.iterrows():
                q_text = row['question_text']
                a_text = row['answer_text']
                # Convert 0/1 to False/True
                is_correct_val = bool(row['is_correct']) 
                # KEY LOGIC: Get the question if it exists, or create it if it's new.
                # We use get_or_create() because the question text appears multiple 
                # times in the file (once for each answer choice).
                # text is the destination column in our Question model.
                # q_text is the source, which is the text from our merged CSV file.
                ## tuple unpacking: get_or_create() returns a tuple (object, created), 
                ## where 'object' is the Question instance 
                ## and 'created' is a boolean indicating if it was newly created or already existed.
                question, created = Question.objects.get_or_create(text=q_text)

                # Create the answer choice linked to this question
                Choice.objects.create(
                    # question is the Foreign Key column in the Choice database (question_id)
                    question=question,
                    text=a_text,
                    is_correct=is_correct_val
                )

            self.stdout.write(self.style.SUCCESS(f'Successfully loaded {len(df)} answer choices!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error while saving to database: {e}"))