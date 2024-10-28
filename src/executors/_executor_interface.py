from abc import ABC, abstractmethod
from typing import Any, Dict


class ExecutorInterface(ABC):
    """
    Abstract base class for executors that can be executed by GPT commands.
    Each specific executer (e.g., command execution, email sending) should inherit from this class.
    """

    @abstractmethod
    def get_executor_definition(self) -> Dict[str, Any]:
        """
        Returns the executor definition (function) that is passed to the OpenAI API.
        """
        pass

    @abstractmethod
    def exec(self, arguments: Dict[str, Any]) -> str:
        """
        Executes the executer based on the arguments provided by GPT.
        Should return the result or raise an error if necessary.
        """
        pass

    @abstractmethod
    def get_result_interpreter_instructions(self, user_language="en") -> str:
        """
        Returns instructions for GPT on how to interpret and present the result to the user.
        """
        pass
