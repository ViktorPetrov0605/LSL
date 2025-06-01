"""
Web Admin UI Module

This module implements the web-based admin interface for the LSL server,
providing functionality for managing users, containers, and monitoring
the system status.
"""
import os
import secrets
from datetime import datetime, timedelta
import json
from typing import Dict, Any, Optional, List

import yaml
from fastapi import FastAPI, Request, HTTPException, Depends, status, Form, Cookie
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
import bcrypt

from shared.config import load_yaml_config
from shared.utils.yaml_logger import setup_logger
from shared.utils.uuid_hash import verify_password_hash

# Initialize logger
logger = setup_logger("web_admin", "logs/web_admin.log")

# Path to main config file
CONFIG_PATH = "config/main.yaml"

# Session management
SESSIONS: Dict[str, Dict[str, Any]] = {}
SESSION_COOKIE_NAME = "lsl_admin_session"
SESSION_EXPIRY = 3600  # 1 hour in seconds

class WebAdmin:
    """Web Admin UI implementation"""
    
    def __init__(self, app: FastAPI):
        """
        Initialize the Web Admin UI
        
        Args:
            app: FastAPI application to mount the admin UI to
        """
        self.app = app
        
        # Load templates
        self.templates = Jinja2Templates(directory="site/templates")
        
        # Load static files
        self.app.mount("/static", StaticFiles(directory="site/static"), name="static")
        
        # Setup routes
        self._setup_routes()
        
    def _setup_routes(self):
        """Set up routes for the Web Admin UI"""
        # Login/logout routes
        self.app.add_api_route("/admin/login", self.login_page, methods=["GET"], response_class=HTMLResponse)
        self.app.add_api_route("/admin/login", self.login_submit, methods=["POST"], response_class=RedirectResponse)
        self.app.add_api_route("/admin/logout", self.logout, methods=["GET"], response_class=RedirectResponse)
        
        # Dashboard routes (protected)
        self.app.add_api_route("/admin", self.dashboard, methods=["GET"], response_class=HTMLResponse)
        self.app.add_api_route("/admin/dashboard", self.dashboard, methods=["GET"], response_class=HTMLResponse)
        
        # User management routes (protected)
        self.app.add_api_route("/admin/users", self.user_list, methods=["GET"], response_class=HTMLResponse)
        
        # Container management routes (protected)
        self.app.add_api_route("/admin/containers", self.container_list, methods=["GET"], response_class=HTMLResponse)
        
        # Monitoring routes (protected)
        self.app.add_api_route("/admin/monitor", self.monitor, methods=["GET"], response_class=HTMLResponse)
            
    async def login_page(self, request: Request):
        """
        Login page
        
        Args:
            request: FastAPI request
            
        Returns:
            HTML response with login page
        """
        # Check if already logged in
        session_id = request.cookies.get(SESSION_COOKIE_NAME)
        if session_id and self._validate_session(session_id):
            return RedirectResponse(url="/admin/dashboard", status_code=303)
            
        return self.templates.TemplateResponse(
            "login.html",
            {"request": request, "error": None}
        )
        
    async def login_submit(self, 
                         username: str = Form(...),
                         password: str = Form(...)):
        """
        Process login form submission
        
        Args:
            username: Admin username
            password: Admin password
            
        Returns:
            Redirect to dashboard or back to login page
        """
        # Check credentials against main.yaml
        try:
            config = load_yaml_config(CONFIG_PATH)
            if "admin" not in config:
                logger.error("No admin section in config")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Admin configuration error"
                )
                
            admin_config = config["admin"]
            stored_username = admin_config.get("username")
            stored_password_hash = admin_config.get("password_hash")
            
            if not stored_username or not stored_password_hash:
                logger.error("Missing admin credentials in config")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Admin configuration error"
                )
                
            # Verify credentials
            if username != stored_username:
                logger.warning(f"Failed login attempt: Invalid username '{username}'")
                response = RedirectResponse(url="/admin/login", status_code=303)
                return response
                
            if not verify_password_hash(password, stored_password_hash):
                logger.warning(f"Failed login attempt for user '{username}': Invalid password")
                response = RedirectResponse(url="/admin/login", status_code=303)
                return response
                
            # Create session
            session_id = self._create_session(username)
            logger.info(f"User '{username}' logged in successfully")
            
            response = RedirectResponse(url="/admin/dashboard", status_code=303)
            response.set_cookie(
                key=SESSION_COOKIE_NAME,
                value=session_id,
                httponly=True,
                max_age=SESSION_EXPIRY,
                samesite="lax",
                secure=False  # Set to True in production with HTTPS
            )
            return response
            
        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
            response = RedirectResponse(url="/admin/login", status_code=303)
            return response
            
    async def logout(self, request: Request):
        """
        Log out user
        
        Args:
            request: FastAPI request
            
        Returns:
            Redirect to login page
        """
        session_id = request.cookies.get(SESSION_COOKIE_NAME)
        if session_id and session_id in SESSIONS:
            username = SESSIONS[session_id].get("username", "Unknown")
            del SESSIONS[session_id]
            logger.info(f"User '{username}' logged out")
            
        response = RedirectResponse(url="/admin/login", status_code=303)
        response.delete_cookie(key=SESSION_COOKIE_NAME)
        return response
        
    def _create_session(self, username: str) -> str:
        """
        Create a new session for a user
        
        Args:
            username: Username to create session for
            
        Returns:
            Session ID
        """
        session_id = secrets.token_urlsafe(32)
        expiry = datetime.now() + timedelta(seconds=SESSION_EXPIRY)
        
        SESSIONS[session_id] = {
            "username": username,
            "created_at": datetime.now().isoformat(),
            "expires_at": expiry.isoformat(),
        }
        
        return session_id
        
    def _validate_session(self, session_id: str) -> bool:
        """
        Validate a session
        
        Args:
            session_id: Session ID to validate
            
        Returns:
            True if session is valid, False otherwise
        """
        if session_id not in SESSIONS:
            return False
            
        session = SESSIONS[session_id]
        expiry = datetime.fromisoformat(session["expires_at"])
        
        if datetime.now() > expiry:
            # Session expired, remove it
            del SESSIONS[session_id]
            return False
            
        return True
        
    async def _get_current_user(self, request: Request) -> Optional[str]:
        """
        Get current logged-in user from session
        
        Args:
            request: FastAPI request
            
        Returns:
            Username if session is valid, None otherwise
        """
        session_id = request.cookies.get(SESSION_COOKIE_NAME)
        if not session_id or not self._validate_session(session_id):
            return None
            
        return SESSIONS[session_id]["username"]
        
    async def _auth_required(self, request: Request) -> str:
        """
        Middleware to require authentication
        
        Args:
            request: FastAPI request
            
        Returns:
            Username if authenticated
            
        Raises:
            HTTPException: If not authenticated
        """
        username = await self._get_current_user(request)
        if not username:
            raise HTTPException(
                status_code=status.HTTP_303_SEE_OTHER,
                headers={"Location": "/admin/login"}
            )
            
        return username
        
    async def dashboard(self, request: Request):
        """
        Dashboard page
        
        Args:
            request: FastAPI request
            
        Returns:
            HTML response with dashboard
        """
        # Enforce authentication
        try:
            username = await self._auth_required(request)
        except HTTPException as e:
            return RedirectResponse(url="/admin/login", status_code=303)
        
        # Render dashboard template
        return self.templates.TemplateResponse(
            "dashboard.html",
            {"request": request, "username": username}
        )
        
    async def user_list(self, request: Request):
        """
        User list page
        
        Args:
            request: FastAPI request
            
        Returns:
            HTML response with user list
        """
        # Enforce authentication
        try:
            username = await self._auth_required(request)
        except HTTPException as e:
            return RedirectResponse(url="/admin/login", status_code=303)
        
        # TODO: Load user list from users.yaml
        users = []
        
        return self.templates.TemplateResponse(
            "users.html",
            {"request": request, "username": username, "users": users}
        )
        
    async def container_list(self, request: Request):
        """
        Container list page
        
        Args:
            request: FastAPI request
            
        Returns:
            HTML response with container list
        """
        # Enforce authentication
        try:
            username = await self._auth_required(request)
        except HTTPException as e:
            return RedirectResponse(url="/admin/login", status_code=303)
        
        # TODO: Load container list from containers.yaml
        containers = []
        
        return self.templates.TemplateResponse(
            "containers.html",
            {"request": request, "username": username, "containers": containers}
        )
        
    async def monitor(self, request: Request):
        """
        Monitoring page
        
        Args:
            request: FastAPI request
            
        Returns:
            HTML response with monitoring dashboard
        """
        # Enforce authentication
        try:
            username = await self._auth_required(request)
        except HTTPException as e:
            return RedirectResponse(url="/admin/login", status_code=303)
        
        # TODO: Load monitoring data
        
        return self.templates.TemplateResponse(
            "monitor.html",
            {"request": request, "username": username}
        )
