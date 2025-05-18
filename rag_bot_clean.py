import os
import json
from openai import OpenAI
from datetime import datetime
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.indexes import VectorstoreIndexCreator
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv 
from transformers import AutoTokenizer  # Add this


# Set tokenizer parallelism to false to avoid warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class RAGBot:
    def __init__(self, data_path="raw_model_output.txt"):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.index = None
        self.data_path = data_path

    def build_vectorstore(self):
        try:
            print(f"Building vectorstore from {self.data_path}...")
            if not os.path.exists(self.data_path):
                raise FileNotFoundError(f"Data file not found: {self.data_path}")
                
            loader = TextLoader(self.data_path)
            splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
            self.index = VectorstoreIndexCreator(
                embedding=HuggingFaceEmbeddings(),
                text_splitter=splitter,
                vectorstore_cls=Chroma
            ).from_loaders([loader])
            print("Vectorstore built successfully.")
        except Exception as e:
            print(f"Error building vectorstore: {str(e)}")
            raise

    def generate_qa(self):
        try:
            # Get relevant context
            query = "Generate technical interview questions and answers. The questions should grammatically be asked and extremely similar to an interview question. Answers should be intricate and successful in answering the question. Answer professionally, in complete sentences, and intelligently with ONLY correct responses."
            print("Performing similarity search...")
            results = self.index.vectorstore.similarity_search(query, k=3)
            context = "\n".join([doc.page_content for doc in results])
            print(f"Found {len(results)} relevant documents")

            # Create prompt
            prompt = f"""Based on the following interview experience context, generate 10 technical interview questions and their detailed answers.
            The questions should be based on the actual content of the interview experience.
            Each answer should be detailed and explain the reasoning and importance of the concept.

            Context: {context}

            Return ONLY a Python dictionary where:
            - Keys are specific questions about the interview experience or technical concepts mentioned
            - Values are detailed answers that explain the concepts and their importance
            - Format: {{"Question": "Detailed answer"}}

            Output:"""

            # Generate response using OpenAI
            print("Generating response from OpenAI...")
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a technical interview question generator. Generate questions and answers based on the provided interview experience. Make answers detailed and informative."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            # Extract the response text
            response_text = response.choices[0].message.content
            print("Raw model response received")
            
            # Extract dictionary from response
            try:
                # Find the dictionary in the response
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                if start != -1 and end != 0:
                    dict_str = response_text[start:end]
                    # Clean up any potential formatting issues
                    dict_str = dict_str.replace('\n', ' ').replace('\r', '')
                    qa_dict = eval(dict_str)
                    if isinstance(qa_dict, dict) and len(qa_dict) > 0:
                        print(f"Successfully parsed {len(qa_dict)} Q&A pairs")
                        return qa_dict
                print("No valid dictionary found in response")
                print("Raw response:", response_text)
                return {}
            except Exception as e:
                print(f"Error parsing response: {str(e)}")
                print("Raw response:", response_text)
                return {}
        except Exception as e:
            print(f"Error in generate_qa: {str(e)}")
            return {}

    def evaluate_user_response(self, question, user_answer):
        try:
            # Format prompt as chat messages
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are an expert technical interviewer. Compare the candidate's response "
                        "to the correct answer and provide constructive, concise feedback."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Question: {question}\n\n"
                        f"Correct Answer: {qa_pairs.get(question, 'N/A')}\n\n"
                        f"Candidate Answer: {user_answer}\n\n"
                        "Please give clear, actionable feedback on how well the answer matches the correct answer, "
                        "mentioning what was done well and what could be improved."
                    )
                }
            ]

            # Call OpenAI API to evaluate
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.5,
                max_tokens=300
            )

            feedback = response.choices[0].message.content.strip()
            return feedback

        except Exception as e:
            return f"Error evaluating response: {str(e)}"


# Initialize global objects so they can be imported
bot = RAGBot(data_path="raw_model_output.txt")
bot.build_vectorstore()
qa_pairs = bot.generate_qa()
combined_data = []

if __name__ == "__main__":
    try:
        # Initialize and run RAG bot
        bot = RAGBot(data_path="raw_model_output.txt")
        bot.build_vectorstore()
        
        # Generate Q&A pairs
        qa_pairs = bot.generate_qa()
        
        # Save to JSON
        if qa_pairs:
            output_path = f"interview_qna.json"
            
            with open(output_path, "w") as f:
                json.dump(qa_pairs, f, indent=4)
            print(f"\nQ&A pairs saved to {output_path}")
            
            # Print results
            print("\nGenerated Questions and Answers:")
            for q, a in qa_pairs.items():
                print(f"\nQ: {q}\nA: {a}")
        else:
            print("No Q&A pairs were generated.")
    except Exception as e:
        print(f"Error in main execution: {str(e)}")