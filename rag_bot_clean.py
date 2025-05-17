import os
from transformers import AutoTokenizer, AutoModelForCausalLM
from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.indexes import VectorstoreIndexCreator
from langchain.embeddings import HuggingFaceEmbeddings

class RAGBot:
    def __init__(self, data_path="my_data.txt"):
        self.model_name = "tiiuae/Falcon3-1B-Instruct"
        self.llm = None
        self.tokenizer = None
        self.index = None
        self.full_prompt = ""
        self.max_tokens = 512  # increased to support longer output
        self.top_k = 3
        self.data_path = data_path

    def load_model(self):
        print("🚀 Loading model...")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.llm = AutoModelForCausalLM.from_pretrained(
            self.model_name, torch_dtype="auto", device_map="auto"
        )
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.llm.config.pad_token_id = self.llm.config.eos_token_id
        print("✅ Model loaded.")

    def build_vectorstore(self, chunk_size=500, overlap=50):
        print(f"📚 Building vectorstore from {self.data_path}...")
        if not os.path.isfile(self.data_path):
            raise FileNotFoundError(f"Missing file: {self.data_path}")
        loader = TextLoader(self.data_path)
        splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=overlap)
        self.index = VectorstoreIndexCreator(
            embedding=HuggingFaceEmbeddings(), text_splitter=splitter
        ).from_loaders([loader])
        print("✅ Vectorstore built.")

    def create_prompt(self, rag_enabled=True):
        task = (
            "Generate 5 behavioral interview questions based on this material. "
            "For each question, also provide a detailed sample answer."
        )
        results = self.index.vectorstore.similarity_search(task, k=self.top_k)
        context = "\n".join([doc.page_content for doc in results])
        if rag_enabled:
            self.full_prompt = f"Context: {context}\n\nTask: {task}\nOutput:"
        else:
            self.full_prompt = f"Task: {task}\nOutput:"

    def inference(self):
        messages = [
            {"role": "system", "content": "You are an AI that creates behavioral interview Q&A pairs based on context of the database."},
            {"role": "user", "content": self.full_prompt}
        ]
        text = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.tokenizer([text], return_tensors="pt").to(self.llm.device)
        output_ids = self.llm.generate(**inputs, max_new_tokens=self.max_tokens, top_k=self.top_k)
        trimmed = [ids[len(inp):] for inp, ids in zip(inputs.input_ids, output_ids)]
        return self.tokenizer.batch_decode(trimmed, skip_special_tokens=True)[0]

if __name__ == "__main__":
    bot = RAGBot(data_path="my_data.txt")
    bot.load_model()
    bot.build_vectorstore()
    bot.create_prompt()
    result = bot.inference()

    print("\n🧠 Interview Questions + Sample Answers:\n")
    print(result)