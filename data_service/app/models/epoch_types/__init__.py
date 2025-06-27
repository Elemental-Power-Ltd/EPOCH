"""Pydantic Type definitions that are closely tied to EPOCH's internal types."""

from .report_data_type import ReportData as ReportData
from .task_data_type import TaskData as TaskDataPydantic

__all__ = ["ReportData", "TaskDataPydantic"]
