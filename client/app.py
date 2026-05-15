"""Streamlit form client for ``POST /api/v1/estimate``."""

from __future__ import annotations

import os
from typing import Any

import httpx
import streamlit as st

from models import DetailLevel, EstimationRequest, OutputFormat, ProjectType


def _base_url_error(raw: str) -> str | None:
    u = raw.strip().rstrip("/")
    if not u:
        return (
            "Set **ESTIMATOR_API_BASE_URL** to the engine root, for example "
            "`http://localhost:8000` (no trailing slash)."
        )
    if not u.startswith(("http://", "https://")):
        return "Base URL must start with `http://` or `https://`."
    return None


st.set_page_config(page_title="Estimator", page_icon="📋", layout="centered")

raw_base = os.environ.get("ESTIMATOR_API_BASE_URL", "")
err = _base_url_error(raw_base)
if err:
    st.error(err)
    st.stop()

base = raw_base.strip().rstrip("/")
estimate_url = f"{base}/api/v1/estimate"

st.title("Software estimation")
st.caption(f"POST `{estimate_url}`")

with st.form("estimate_form"):
    description = st.text_area(
        "Project description",
        height=200,
        help="Minimum 20 characters, maximum 2000.",
    )
    project_type = st.selectbox(
        "Project type",
        options=list(ProjectType),
        format_func=lambda x: x.value,
    )
    detail_level = st.selectbox(
        "Detail level",
        options=list(DetailLevel),
        format_func=lambda x: x.value,
    )
    output_format = st.selectbox(
        "Output format",
        options=list(OutputFormat),
        format_func=lambda x: x.value,
    )
    submitted = st.form_submit_button("Get estimate")

if submitted:
    try:
        req = EstimationRequest(
            description=description.strip(),
            project_type=project_type,
            detail_level=detail_level,
            output_format=output_format,
        )
    except Exception as exc:  # noqa: BLE001 — show validation to user
        st.error(f"Invalid form: {exc}")
    else:
        try:
            with httpx.Client(timeout=120.0) as client:
                r = client.post(estimate_url, json=req.model_dump(mode="json"))
        except httpx.RequestError as exc:
            st.error(f"Request failed: {exc}")
        else:
            if r.status_code == 200:
                data: dict[str, Any] = r.json()
                st.success("Done")
                st.write("**prompt_version:**", data.get("prompt_version", ""))
                st.markdown(data.get("text", ""))
            elif r.status_code == 422:
                st.warning("Validation error (engine rejected the payload)")
                st.json(r.json())
            else:
                st.error(f"HTTP {r.status_code}")
                try:
                    st.json(r.json())
                except ValueError:
                    st.code(r.text)
