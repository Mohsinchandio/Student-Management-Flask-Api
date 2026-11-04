"""Task 1 - Streamlit front-end for the Student API.
Run (with the Flask API already running):  streamlit run streamlit_app.py
"""
import pandas as pd
import requests
import streamlit as st

API_URL = "http://127.0.0.1:5000/students"

st.set_page_config(page_title="Student Management", page_icon="🎓", layout="wide")
st.title("🎓 Student Management System")


# ---------- helpers ----------
def fetch_students():
    try:
        r = requests.get(API_URL, timeout=5)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        st.error(f"Cannot reach the Flask API at {API_URL}. Is it running? ({e})")
        return None


def flash(kind, message):
    """Store a message so it survives st.rerun()."""
    st.session_state["flash"] = (kind, message)


def error_text(resp):
    try:
        return resp.json().get("error", resp.text)
    except ValueError:
        return resp.text


# show message from the previous action
if "flash" in st.session_state:
    kind, msg = st.session_state.pop("flash")
    (st.success if kind == "success" else st.error)(msg)

students = fetch_students()
if students is None:
    st.stop()

# ---------- 1. display all students ----------
st.subheader("📋 All Students")
if students:
    df = pd.DataFrame(students).rename(
        columns={"student_id": "ID", "name": "Name",
                 "department": "Department", "email": "Email"}
    )
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("No students yet. Add one below.")

col_add, col_edit = st.columns(2)

# ---------- 2. add student ----------
with col_add:
    st.subheader("➕ Add Student")
    with st.form("add_form", clear_on_submit=True):
        name = st.text_input("Name")
        dept = st.text_input("Department")
        email = st.text_input("Email")
        if st.form_submit_button("Add Student"):
            if not (name.strip() and dept.strip() and email.strip()):
                st.warning("All fields are required.")
            else:
                r = requests.post(API_URL, json={"name": name, "department": dept, "email": email})
                if r.status_code == 201:
                    flash("success", f"Student '{name}' added successfully.")
                    st.rerun()
                else:
                    st.error(error_text(r))

# ---------- 3. update + 4. delete ----------
with col_edit:
    st.subheader("✏️ Update / Delete Student")
    if not students:
        st.info("Nothing to edit yet.")
    else:
        by_id = {s["student_id"]: s for s in students}
        selected_id = st.selectbox(
            "Select a student",
            options=list(by_id.keys()),
            format_func=lambda i: f"{i} - {by_id[i]['name']}",
        )
        s = by_id[selected_id]

        with st.form("update_form"):
            # keys include the id so fields refresh when selection changes
            new_name = st.text_input("Name", value=s["name"], key=f"n{selected_id}")
            new_dept = st.text_input("Department", value=s["department"], key=f"d{selected_id}")
            new_email = st.text_input("Email", value=s["email"], key=f"e{selected_id}")
            if st.form_submit_button("Update Student"):
                r = requests.put(
                    f"{API_URL}/{selected_id}",
                    json={"name": new_name, "department": new_dept, "email": new_email},
                )
                if r.status_code == 200:
                    flash("success", f"Student {selected_id} updated successfully.")
                    st.rerun()
                else:
                    st.error(error_text(r))

        if st.button("🗑️ Delete Selected Student", type="primary"):
            r = requests.delete(f"{API_URL}/{selected_id}")
            if r.status_code == 200:
                flash("success", f"Student {selected_id} deleted.")
                st.rerun()
            else:
                st.error(error_text(r))
