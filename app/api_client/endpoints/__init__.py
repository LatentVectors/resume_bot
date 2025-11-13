"""API client endpoints for all API resources."""

from app.api_client.endpoints.certificates import CertificatesAPI
from app.api_client.endpoints.cover_letters import CoverLettersAPI
from app.api_client.endpoints.education import EducationAPI
from app.api_client.endpoints.experiences import ExperiencesAPI
from app.api_client.endpoints.jobs import JobsAPI
from app.api_client.endpoints.messages import MessagesAPI
from app.api_client.endpoints.responses import ResponsesAPI
from app.api_client.endpoints.resumes import ResumesAPI
from app.api_client.endpoints.templates import TemplatesAPI
from app.api_client.endpoints.users import UsersAPI
from app.api_client.endpoints.workflows import WorkflowsAPI

__all__ = [
    "UsersAPI",
    "JobsAPI",
    "ExperiencesAPI",
    "EducationAPI",
    "CertificatesAPI",
    "ResumesAPI",
    "CoverLettersAPI",
    "TemplatesAPI",
    "MessagesAPI",
    "ResponsesAPI",
    "WorkflowsAPI",
]

