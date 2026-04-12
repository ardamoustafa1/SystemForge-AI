"""Shared export query enums for OpenAPI/codegen clarity."""

from enum import Enum


class ExportFormatQuery(str, Enum):
    """`format` query parameter for design export endpoints."""

    markdown = "markdown"
    pdf = "pdf"
