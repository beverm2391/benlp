from operator import itemgetter
import os
import pickle
from .utils import random_6_digit_id
from .llms import Completion, Chat, embed_ada
from .document import Document
from .prompts.react import REACT_EXAMPLES
from typing import Dict, List, Tuple
import numpy as np
import random


class BaseAgent:
    def __init__(self, objective, config=None, index_path=None):
        # config
        self.config = config
        self.objective = objective

        # llm stuff
        self.tools = []
        self.chat_history = []
        self.task_list = []
        self.code_executions = []
        self.token_counter = 0

        # DB stuff
        self.index = self.init_index(index_path)
        self.index_id = None
        self.index_path = self.get_index_path(self.index_id)
        self.working_memory = []

    # ! CONFIG methods ==========================================================

    def set_objective(self, objective):
        self.objective = objective
        print(f"Objective set to: {objective}")

    def add_tool(self, tool):
        self.tools.append(tool)
        print(f"Tool added: {tool}")

    def remove_tool(self, tool):
        self.tools.remove(tool)
        print(f"Tool removed: {tool}")

    def get_tools(self):
        tools_prompt = "Tools Availible:" + \
            "\n".join(
                [f"{tool['name']}: {tool['instruction']}" for tool in self.tools])
        return tools_prompt

    def save_config(self, path):
        pass

    def load_config(self, path):
        pass

    # ! Models =============================================================

    def generate_tasks(self):
        tools_prompt = self.get_tools()
        base_prompt = f"""
            You are a task generator. You are given a list of tools and an objective, {self.objective}. Generate a list of tasks that will help you achieve your objective as efficiently as possible using only the tools provided.
            Tools Availible: {tools_prompt}""" + """

            Output only your task list in an array of dictionaries with keys:
            "name": str, the name of the task
            "instruction": str, the instruction for the task
            "tools_needed": str, the name of the tools needed for the task, if any. You can only use tools included in the list above. separate multiple tools with commas. ex: "tool1, tool2, tool3"
            
            Example Output:

            [
                {
                    "name": "task1",
                    "instruction": "do this",
                    "tools_needed": "tool1, tool2"
                },
                {
                    "name": "task2",
                    "instruction": "do that",
                    "tools_needed": "tool3"
                }, ...
            ]

            Output only a valid python list with valid python dictionaries."""

        chat = Chat()
        res = chat(base_prompt)['response'].strip()
        print(f"Task List:\n\n{res}")
        self.task_list = eval(res)

    def evaluate_objective(self):
        memory_string = "\n\n".join(self.working_memory)
        evaluation_prompt = f"""
            You are tasked with evaluating if an objective, {self.objective}, has been sufficiently completed. You are given a history of tasks completed as follows: {memory_string}. Evaluate if the objective has been completed. If it has, output only "True", if it has not, output only "False".
        """
        chat = Chat()
        res = chat(evaluation_prompt)['response'].strip()
        print(f"Objective Evaluation:\n\n{res}")
        _bool = eval(res)
        return _bool


    # ! DB methods ==============================================================

    def get_index_path(self, index_id):
        return os.path.join(os.path.dirname(os.getcwd()), "data", "indexes", f"{str(index_id)}.pkl")

    def init_index(self, index_path):
        fpath = index_path

        # create data folder if it doesn't exist
        if not os.path.exists(os.path.join(os.path.dirname(os.getcwd()), "data")):
            os.mkdir(os.path.join(os.path.dirname(os.getcwd()), "data"))
        # create indexes folder if it doesn't exist
        if not os.path.exists(os.path.join(os.path.dirname(os.getcwd()), "data", "indexes")):
            os.mkdir(os.path.join(os.path.dirname(
                os.getcwd()), "data", "indexes"))

        # load index if it exists
        if fpath is not None:
            if os.path.exists(fpath):
                with open(fpath, "rb") as f:
                    index = pickle.load(f)
                print("Index loaded from file.")
                index_id = os.path.basename(fpath).split(".")[0]
                self.index_id = index_id
                self.index_path = fpath
                return index
            else:
                print(f"Index at {fpath} does not exist.")
                print("Initializing empty index.")
        self.index_id = random_6_digit_id()
        self.index_path = self.get_index_path(self.index_id)
        index = []
        # save empty index
        with open(self.index_path, "wb") as f:
            pickle.dump(index, f)
        print("Empty Index initialized.")
        return self

    def sync_index(self):
        with open(self.index_path, "wb") as f:
            pickle.dump(self.index, f)
        print("Index synced locally.")
        return self

    def load_index(self):
        with open(self.index_path, "rb") as f:
            index = pickle.load(f)
        self.index = index
        self.index_id = os.path.basename(self.index_path).split(".")[0]
        self.index_path = self.get_index_path(self.index_id)
        print("Index loaded from file.")
        return self

    def add_document_to_index(self, fpath: str):
        data = Document(fpath).process().to_dict()
        self.index.append(data)
        self.sync_index()
        print(f"Document added to index: {fpath}")
        return self

    # ! Semantic Search =========================================================

    def get_top_k(self, text, top_k=5):
        embedding = embed_ada(text)
        results = []
        for doc_dict in self.index:
            for chunk_dict in doc_dict["data"]:
                similarity = np.dot(embedding, chunk_dict["embedding"])
                chunk_dict["similarity"] = similarity
                results.append({
                    "id": chunk_dict["id"],
                    "text": chunk_dict["text"],
                    "similarity": similarity
                })
        results = sorted(results, key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]

    # ! RUN =====================================================================

    def run(self):
        print("Running...")
        print("Generating Tasks...")
        self.generate_tasks()

        # While objective is not completed
        for task in self.task_list:
            # eval - are we done?
            if self.evaluate_objective():
                print("Objective Completed!")
                break

            # debug so we can see what's going on
            print(f"Task: {task['name']}")
            print(f"Description: {task['description']}")

            # create prompt
            prompt = f"""
            OBJECTIVE: {self.objective}
            TASK: {task['name']}
            TASK DESCRIPTION: {task['description']}
            TOOLS NEEDED: {task['tools_needed']}

            CONTEXT: {self.working_memory}

            EXAMPLE OUTPUT: 
            {random.sample(REACT_EXAMPLES, 3)}

            YOUR OUTPUT:
            """
            chat = Chat(model='gpt-3.5-turbo', max_tokens=1000)
            res = chat(prompt)['response'].strip()

            # TODO parser goes here 
            # tools: search, code_execute
            # TODO update REACT_EXAMPLES to use my syntax

            # take any action needed
            # add all results to working memory
            # TODO create working memory with recursive summarization once we exceed a token limit
            # potentially embed working memory into a separate index?? using the exact same methods as the main index? or store working memory and data in the same index as separate data structures?