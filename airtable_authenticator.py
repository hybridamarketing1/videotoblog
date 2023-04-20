import streamlit as st
from pyairtable import Table
from typing import Tuple, Optional
import bcrypt
from pyairtable.formulas import match



class AirtableAuthenticator:
    def __init__(self, airtable: Table):
        self.airtable = airtable

    def _get_user(self, username: str):
        user_records = self.airtable.all(formula=match({"Username": username}))
        if user_records:
            return user_records[0]["fields"]
        return None

    def _check_password(self, username: str, password: str) -> Tuple[bool, Optional[str]]:
        user = self._get_user(username)
        if user:
            stored_password = user["Password"].encode('utf-8')
            entered_password = password.encode('utf-8')
            is_password_correct = bcrypt.checkpw(entered_password, stored_password)
            return is_password_correct, user["Name"] if is_password_correct else None
        return False, None

    def _get_name(self, username: str) -> str:
        user = self._get_user(username)
        if user:
            return user["Name"]
        return ""

    def login(self, login_text: str, logout_text: str) -> Tuple[str, bool, str]:
        if "authenticated_username" in st.session_state:
            if st.button(logout_text):
                del st.session_state["authenticated_username"]
                return "", False, ""
            return self._get_name(st.session_state["authenticated_username"]), True, st.session_state["authenticated_username"]

        st.write(login_text)
        self.username = st.text_input("Username:")
        self.password = st.text_input("Password:", type="password")

        if self.username and self.password:
            is_password_correct, name = self._check_password(self.username, self.password)
            if is_password_correct:
                st.session_state["authenticated_username"] = self.username
                return name, True, self.username
            else:
                return "", False, self.username

        return "", None, ""

    def register_user(self, email: str, name: str, username: str, password: str):
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        self.airtable.create({
            "Email": email,
            "Name": name,
            "Username": username,
            "Password": hashed_password,
            "ArticleCount": 0
        })
