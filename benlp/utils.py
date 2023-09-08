import warnings
import re

import tiktoken
import random

from langchain.text_splitter import CharacterTextSplitter, RecursiveCharacterTextSplitter, Language


def random_6_digit_id():
    return random.randint(100000, 999999)


def parse_code_blocks(markdown):
    code_blocks = []
    pattern = re.compile(r'```(\w+)?\s(.*?)```', re.DOTALL)
    matches = pattern.findall(markdown)

    for match in matches:
        language, code = match
        code_blocks.append({
            "language": language,
            "code": code.strip()
        })

    return code_blocks


def sanitize_text(text):
    """
    Sanitize the input text by removing unsupported characters, trimming whitespace, and checking for empty strings.

    Args:
        text (str): The input text to be sanitized.

    Returns:
        str: The sanitized text, or None if the text is empty after sanitization.
    """

    # Remove any characters that are not supported by the tokenizer
    # This example assumes the tokenizer supports ASCII characters, digits, and common punctuation
    # You can modify the regular expression to match the specific tokenizer requirements
    sanitized_text = re.sub(r"[^\x00-\x7F]+", "", text)

    # Trim leading and trailing whitespace
    sanitized_text = sanitized_text.strip()

    # Check for empty strings
    if not sanitized_text:
        return None

    return sanitized_text


class TokenUtil:
    """
    A utility class for handling tokens in text using the specified model.
    """

    def __init__(self, model):
        assert model is not None, "Model must be specified. (passed as positional argument)"
        self.model = self.validate_model(model)

    def validate_model(self, model):
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            warnings.warn(
                "Warning: model not found. Using cl100k_base encoding.")
            self.encoding = tiktoken.get_encoding("cl100k_base")
        if model == "gpt-3.5-turbo":
            warnings.warn(
                "Warning: gpt-3.5-turbo may change over time. Returning num tokens assuming gpt-3.5-turbo-0301.")
            model = "gpt-3.5-turbo-0301"
            self.tokens_per_message = 4
            self.tokens_per_name = -1  # if there's a name, the role is omitted
        elif model == "gpt-4":
            warnings.warn(
                "Warning: gpt-4 may change over time. Returning num tokens assuming gpt-4-0314.")
            model = "gpt-4-0314"
            self.tokens_per_message = 3
            self.tokens_per_name = 1
        return model

    def get_tokens(self, text):
        # sanitize text
        text = sanitize_text(text)
        if text is None:
            return 0

        num_tokens = 0
        if isinstance(text, str):
            num_tokens += len(self.encoding.encode(text))
        elif isinstance(text, list):
            for message in text:
                num_tokens += self.tokens_per_message
                for key, value in message.items():
                    num_tokens += len(self.encoding.encode(value))
                    if key == "name":
                        num_tokens += self.tokens_per_name
        else:
            raise TypeError("text must be a string or list of messages.")

        num_tokens += 2  # every reply is primed with <im_start>assistant
        return num_tokens

    def encode(self, text):
        return self.encoding.encode(text)

    def decode(self, tokens):
        return self.encoding.decode(tokens)

    def split_tokens(self, text, max_tokens):
        assert isinstance(
            text, str), f"input text for split_tokens must be a string, not {type(text)}"
        # sanitize text
        text = self.sanitize_text(text)
        if text is None:
            return 0

        tokens = self.encoding.encode(text)
        split_tokens = []
        while len(tokens) > max_tokens:
            split_tokens.append(tokens[:max_tokens])
            tokens = tokens[max_tokens:]
        split_tokens.append(tokens)
        split_text = [self.encoding.decode(tokens) for tokens in split_tokens]
        print(f"Returning {len(split_text)} split messages.")
        return split_text

# ! Text Splitters =============================================================
# all langchain splitters use the .create_documents() method to split text


class DefaultSplitter(RecursiveCharacterTextSplitter):
    def __init__(self, chunk_size=1024, chunk_overlap=0):
        super().__init__(chunk_size=chunk_size, chunk_overlap=chunk_overlap)


class PythonSplitter(RecursiveCharacterTextSplitter):
    def __init__(self, chunk_size=1024, chunk_overlap=0):
        super().__init__(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.language = Language.PYTHON


class TikTokenSplitter(CharacterTextSplitter):
    def __init__(self, chunk_size=1024, chunk_overlap=0):
        super().__init__(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.encoding = tiktoken.get_encoding("cl100k_base")
