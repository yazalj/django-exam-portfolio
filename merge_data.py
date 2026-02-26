import pandas as pd
import sys

def merge_exam_data(questions_file='driving_questions-1.csv', answers_file='driving_answers_improved-1.csv', output_file='final_exam_data.csv'):
    """ 
    Reads two separate CSV files (questions and answers), 
    merges them based on a common 'question_id',
    and saves the result as a new CSV file with only the necessary columns for loading into Django.
    Input: questions_file (CSV with question_id and question_text), answers_file (CSV with question_id, answer_text, is_correct).
    Output: A new CSV file that combines the question text with its corresponding answers and correctness, ready for import into the Django database.
    """
    try:
        # Read the two separate files
        questions = pd.read_csv(questions_file, delimiter=';')
        answers = pd.read_csv(answers_file, delimiter=';')

        # Merge them together using 'question_id'
        merged_df = pd.merge(answers, questions, on='question_id')

        # Select only the needed columns
        final_df = merged_df[['question_text', 'answer_text', 'is_correct']]

        # Save to a new single CSV file
        final_df.to_csv(output_file, sep=';', index=False)

        print(f"Success! Created '{output_file}' with {len(final_df)} rows.")
        return True

    except FileNotFoundError as e:
        print(f"Error: A required file is missing. {e}")
        return False
    except KeyError as e:
        print(f"Error: Missing expected column in the CSV files. {e}")
        return False
    except pd.errors.EmptyDataError:
        print("Error: One of the CSV files is completely empty.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False

if __name__ == "__main__":
    merge_exam_data()