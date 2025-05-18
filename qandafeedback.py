from rag_bot_clean import qa_pairs, bot, combined_data
import json
from datetime import datetime

class feedback:
    user_answers = {}
    for question in qa_pairs:
        print(f"\n{question}")
        user_input = input("Your answer: ")  # Placeholder for user's input
        user_answers[question] = user_input

    for question, ai_answer in qa_pairs.items():
        user_answer = user_answers.get(question, "")
        feedback = bot.evaluate_user_response(question, user_answer)

        combined_data.append({
            "question": question,
            "ai_answer": ai_answer,
            "feedback": feedback
        })

    combined_path = f"interview_combined_.json"
    with open(combined_path, "w") as f:
        json.dump(combined_data, f, indent=4)

    print(f"\nCombined data saved to {combined_path}")