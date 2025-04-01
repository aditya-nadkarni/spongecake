"""
Request validation schemas for the Spongecake backend API.
"""
from marshmallow import Schema, fields

class RequestSchemas:
    """Request validation schemas for API endpoints."""
    
    class AgentRequestSchema(Schema):
        """Schema for agent action requests."""
        messages = fields.String(required=True)
        auto_mode = fields.Boolean(default=False)
