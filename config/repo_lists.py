"""Predefined repository lists for different AI/ML domains."""

# Popular LLM repositories
LLM_REPOS = [
    "huggingface/transformers",
    "openai/openai-python",
    "microsoft/DeepSpeed",
    "THUDM/ChatGLM-6B",
    "facebookresearch/llama",
    "google-research/bert",
    "microsoft/DialoGPT",
    "EleutherAI/gpt-neox",
    "bigscience-workshop/Megatron-DeepSpeed",
    "huggingface/tokenizers",
]

# Generative AI and tools
GENAI_REPOS = [
    "langchain-ai/langchain",
    "run-llama/llama_index",
    "openai/gym",
    "Stability-AI/stablediffusion",
    "CompVis/stable-diffusion",
    "microsoft/semantic-kernel",
    "hwchase17/langchain",
    "jerryjliu/llama_index",
    "guidance-ai/guidance",
    "microsoft/autogen",
]

# LLMOps and deployment
LLMOPS_REPOS = [
    "bentoml/BentoML",
    "ray-project/ray",
    "mlflow/mlflow",
    "wandb/wandb",
    "optuna/optuna",
    "determined-ai/determined",
    "feast-dev/feast",
    "kubeflow/kubeflow",
    "seldon-io/seldon-core",
    "onnx/onnx",
]

# Machine Learning frameworks
ML_REPOS = [
    "pytorch/pytorch",
    "tensorflow/tensorflow",
    "scikit-learn/scikit-learn",
    "keras-team/keras",
    "Lightning-AI/lightning",
    "jax-ml/jax",
    "dmlc/xgboost",
    "catboost/catboost",
    "microsoft/LightGBM",
    "apache/spark",
]

# Natural Language Processing
NLP_REPOS = [
    "explosion/spaCy",
    "nltk/nltk",
    "RaRe-Technologies/gensim",
    "flairNLP/flair",
    "stanfordnlp/stanza",
    "allenai/allennlp",
    "pytorch/fairseq",
    "google-research/language",
    "UKPLab/sentence-transformers",
    "deepset-ai/haystack",
]

# All predefined lists
REPO_LISTS = {
    "llm": LLM_REPOS,
    "genai": GENAI_REPOS,
    "llmops": LLMOPS_REPOS,
    "ml": ML_REPOS,
    "nlp": NLP_REPOS,
}


def get_repo_list(name: str) -> list[str]:
    """Get a predefined repository list by name."""
    return REPO_LISTS.get(name.lower(), [])


def list_available_repo_lists() -> list[str]:
    """Get names of all available predefined repository lists."""
    return list(REPO_LISTS.keys())
