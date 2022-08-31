from abc import abstractmethod, ABC


class IssueProvider(ABC):

    @abstractmethod
    def get_issues(self) -> list:
        pass


class ProxyIssueProvider(IssueProvider):

    def __init__(self, issues: list) -> None:
        self.issues = issues

    def get_issues(self) -> list:
        return self.issues
