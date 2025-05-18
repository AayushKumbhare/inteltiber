import os
import json
from datetime import datetime
from transformers import AutoTokenizer, AutoModelForCausalLM
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.indexes import VectorstoreIndexCreator
from langchain_huggingface import HuggingFaceEmbeddings

class RAGBot:
    def __init__(self, data_path="my_data.txt"):
        self.model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        self.llm = None
        self.tokenizer = None
        self.index = None
        self.data_path = data_path

    def load_model(self):
        print("Loading model...")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.llm = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype="auto",
            device_map="auto"
        )
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.llm.config.pad_token_id = self.llm.config.eos_token_id
        print("Model loaded.")

    def build_vectorstore(self):
        print(f"Building vectorstore from {self.data_path}...")
        loader = TextLoader(self.data_path)
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        self.index = VectorstoreIndexCreator(
            embedding=HuggingFaceEmbeddings(),
            text_splitter=splitter
        ).from_loaders([loader])
        print("Vectorstore built.")

    def generate_qa(self):
        # Get relevant context
        query = "Generate technical interview questions and answers"
        results = self.index.vectorstore.similarity_search(query, k=3)
        context = "\n".join([doc.page_content for doc in results])

        # Create prompt
        prompt = f"""Based on this context, generate 5 technical interview questions and answers.
        Format as a Python dictionary where questions are keys and answers are values.
        Keep answers concise and informative.

        Context: {context}

        Output:"""

        # Generate response
        messages = [
            {"role": "system", "content": "You are a technical interview question generator."},
            {"role": "user", "content": prompt}
        ]
        
        text = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.tokenizer([text], return_tensors="pt").to(self.llm.device)
        
        output_ids = self.llm.generate(
            **inputs,
            max_new_tokens=512,
            temperature=0.7,
            top_p=0.95,
            do_sample=True
        )

        # Decode and parse response
        response = self.tokenizer.batch_decode(output_ids, skip_special_tokens=True)[0]
        
        # Extract dictionary from response
        try:
            # Find the dictionary in the response
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end != 0:
                qa_dict = eval(response[start:end])
                return qa_dict
            return {}
        except:
            return {}
    def evaluate_user_response(self, question, user_answer):
        prompt = f"""
            You are an expert technical interviewer.

            Question: {question}

            User Answer: {user_answer}

            Evaluate the user's answer and provide feedback. Highlight what they got right or wrong and suggest improvements. Be concise. Be positive
            and encouraging to the user, making the feel like it is feedback more than criticism.
        """
        messages = [
            {"role": "system", "content": "You are a technical interview evaluator."},
            {"role": "user", "content": prompt}
        ]

        text = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.tokenizer([text], return_tensors="pt").to(self.llm.device)

        output_ids = self.llm.generate(
            **inputs,
            max_new_tokens=256,
            temperature=0.7,
            top_p=0.95,
            do_sample=True
        )

        feedback = self.tokenizer.batch_decode(output_ids, skip_special_tokens=True)[0]
        return feedback

def main():
    # Initialize and run RAG bot
    bot = RAGBot(data_path="my_data.txt")
    bot.load_model()
    bot.build_vectorstore()
    
    # Generate Q&A pairs
    qa_pairs = bot.generate_qa()
    
    # Save to JSON
    if qa_pairs:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"interview_qa_{timestamp}.json"
        
        with open(output_path, "w") as f:
            json.dump(qa_pairs, f, indent=4)
        print(f"\nQ&A pairs saved to {output_path}")
        
        # Print results
        print("\nGenerated Questions and Answers:")
        for q, a in qa_pairs.items():
            print(f"\nQ: {q}\nA: {a}")
    else:
        print("No Q&A pairs were generated.")
    
    feedback = []

    for question in qa_pairs:
        print(f"------------------------------------------------------------------------------------------------")
        print(f"\nQuestion: {question}")
        user_answer = input("Your answer: ")
        feedback.append(bot.evaluate_user_response(question, user_answer))
        print(f"\nFeedback: {feedback}")

if __name__ == "__main__":
    main()
