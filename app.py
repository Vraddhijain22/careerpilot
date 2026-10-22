
import streamlit as st

from app.database import (
    init_db,
    get_resume,
    save_resume,
    add_application,
    list_applications,
    get_application,
    update_application,
    save_draft,
    list_drafts,
    save_interview,
    list_interviews,
)
from app.resume import extract_pdf_text, clean_resume
from app.matching import match_resume_to_job, extract_skills
from app.ai import (
    analyze_job,
    create_draft,
    generate_interview_questions,
    evaluate_answer,
)
from app.config import DEFAULT_PROVIDER


# --------------------------------------------------
# App setup
# --------------------------------------------------

st.set_page_config(
    page_title="CareerPilot AI",
    page_icon="🧭",
    layout="wide",
)

init_db()

STATUSES = [
    "Interested",
    "Applied",
    "Recruiter Screen",
    "Interview",
    "Offer",
    "Rejected",
    "Withdrawn",
]

st.title("🧭 CareerPilot AI")
st.caption(
    "Your job-search workspace: evidence-grounded matching, "
    "application tracking, tailored drafts, and interview practice."
)


# --------------------------------------------------
# Sidebar: AI provider settings
# --------------------------------------------------

with st.sidebar:
    st.header("AI settings")

    default_provider = (
        DEFAULT_PROVIDER
        if DEFAULT_PROVIDER in {"gemini", "ollama"}
        else "gemini"
    )

    provider = st.selectbox(
        "Model provider",
        ["gemini", "ollama"],
        index=["gemini", "ollama"].index(default_provider),
        format_func=lambda value: (
            "Gemini API" if value == "gemini" else "Ollama (local)"
        ),
    )

    if provider == "gemini":
        st.info(
            "Gemini sends prompts to Google's hosted API. "
            "Avoid including sensitive information you do not want "
            "to share with the provider."
        )
    else:
        st.info(
            "Ollama runs the selected model locally. "
            "Keep Ollama running while using AI features."
        )

    st.divider()
    st.caption("Local prototype · SQLite storage")


# --------------------------------------------------
# Main navigation
# --------------------------------------------------

resume_tab, jobs_tab, match_tab, drafts_tab, interview_tab = st.tabs(
    [
        "👤 Resume profile",
        "📋 Applications",
        "🎯 Match a job",
        "✍️ Drafts",
        "🎤 Interview lab",
    ]
)


# --------------------------------------------------
# 1. Resume profile
# --------------------------------------------------

with resume_tab:
    st.subheader("Your resume profile")

    st.write(
        "Upload a text-searchable PDF or paste resume text. "
        "The PDF is processed in memory; extracted text is saved "
        "in the local database after you choose to save it."
    )

    uploaded = st.file_uploader(
        "Upload resume PDF",
        type=["pdf"],
        key="resume_pdf",
    )

    if uploaded and st.button("Extract text from PDF"):
        try:
            extracted = extract_pdf_text(uploaded.getvalue())

            if not extracted.strip():
                st.warning(
                    "No text was extracted. This PDF may be scanned "
                    "or image-based."
                )
            else:
                st.session_state["resume_editor"] = extracted
                st.success(
                    f"Extracted {len(extracted)} characters. "
                    "Review the text before saving."
                )

        except Exception as exc:
            st.error(f"Could not extract PDF text: {exc}")

    existing_resume = get_resume()

    if "resume_editor" not in st.session_state:
        st.session_state["resume_editor"] = existing_resume

    resume_text = st.text_area(
        "Resume text (editable)",
        key="resume_editor",
        height=330,
        placeholder="Paste your resume text here, or extract it from a PDF above.",
    )

    col_save, col_info = st.columns([1, 3])

    with col_save:
        if st.button("Save resume", type="primary"):
            cleaned_resume = clean_resume(resume_text)

            if not cleaned_resume:
                st.error("Add resume text before saving.")
            else:
                save_resume(cleaned_resume)
                st.success("Resume saved locally.")

    with col_info:
        st.caption(
            f"Current editor length: {len(resume_text)} characters · "
            "Maximum saved length: 30,000 characters"
        )

    if resume_text.strip():
        st.markdown("**Detected skills (baseline keyword extraction)**")
        st.write(
            ", ".join(extract_skills(resume_text))
            or "No supported skills detected yet."
        )


# --------------------------------------------------
# 2. Application tracker
# --------------------------------------------------

with jobs_tab:
    st.subheader("Application tracker")

    with st.form("add_application_form", clear_on_submit=True):
        col_company, col_role = st.columns(2)

        company = col_company.text_input("Company *")
        role = col_role.text_input("Role title *")

        job_url = st.text_input("Job URL (optional)")
        status = st.selectbox("Status", STATUSES)

        job_description = st.text_area(
            "Job description (recommended)",
            height=180,
        )

        follow_up = st.text_input(
            "Follow-up date (YYYY-MM-DD, optional)"
        )
        notes = st.text_area("Notes (optional)", height=70)

        submitted = st.form_submit_button(
            "Save application",
            type="primary",
        )

        if submitted:
            if not company.strip() or not role.strip():
                st.error("Company and role are required.")
            else:
                try:
                    application_id = add_application(
                        company.strip(),
                        role.strip(),
                        job_url.strip(),
                        job_description.strip(),
                        status,
                        notes.strip(),
                        follow_up.strip(),
                    )

                    st.success(
                        f"Saved application #{application_id}."
                    )

                except Exception as exc:
                    st.error(f"Could not save application: {exc}")

    st.divider()

    applications = list_applications()

    if applications:
        st.dataframe(
            [
                {
                    "ID": app["id"],
                    "Company": app["company"],
                    "Role": app["role"],
                    "Status": app["status"],
                    "Match": (
                        f'{app["match_score"]}%'
                        if app["match_score"] is not None
                        else "Not scored"
                    ),
                    "Follow-up": app["follow_up_date"],
                }
                for app in applications
            ],
            use_container_width=True,
            hide_index=True,
        )

        selected_id = st.selectbox(
            "Update an application",
            [app["id"] for app in applications],
            format_func=lambda app_id: next(
                (
                    f'#{app["id"]} — {app["company"]} / {app["role"]}'
                    for app in applications
                    if app["id"] == app_id
                ),
                f"Application #{app_id}",
            ),
        )

        selected_app = get_application(selected_id)

        if selected_app:
            with st.form("update_application_form"):
                current_status = selected_app["status"]

                new_status = st.selectbox(
                    "New status",
                    STATUSES,
                    index=(
                        STATUSES.index(current_status)
                        if current_status in STATUSES
                        else 0
                    ),
                )

                new_follow_up = st.text_input(
                    "Follow-up date",
                    value=selected_app["follow_up_date"] or "",
                )

                new_notes = st.text_area(
                    "Notes",
                    value=selected_app["notes"] or "",
                )

                update_submitted = st.form_submit_button(
                    "Update application"
                )

                if update_submitted:
                    try:
                        update_application(
                            selected_id,
                            status=new_status,
                            follow_up_date=new_follow_up.strip(),
                            notes=new_notes.strip(),
                        )
                        st.success("Application updated.")
                        st.rerun()

                    except Exception as exc:
                        st.error(f"Could not update application: {exc}")

    else:
        st.info("No applications yet. Add your first role above.")


# --------------------------------------------------
# 3. Resume-to-job matching
# --------------------------------------------------

with match_tab:
    st.subheader("Analyze a job")

    resume = get_resume()
    applications = list_applications()

    choices = ["Paste a new job description"] + [
        f'#{app["id"]} — {app["company"]} / {app["role"]}'
        for app in applications
    ]

    choice = st.selectbox(
        "Choose a saved application or enter a new job",
        choices,
        key="match_application_choice",
    )

    if choice == choices[0]:
        new_company = st.text_input(
            "Company",
            key="match_company",
        )
        new_role = st.text_input(
            "Role title",
            key="match_role",
        )
        new_url = st.text_input(
            "Job URL",
            key="match_url",
        )
        jd = st.text_area(
            "Paste job description",
            height=220,
            key="match_jd",
        )
        save_new = st.checkbox(
            "Save this job to the application tracker",
            key="match_save_new",
        )
        app_id = None

    else:
        app_id = int(choice.split(" — ")[0][1:])
        current_app = get_application(app_id)

        if current_app:
            new_company = current_app["company"]
            new_role = current_app["role"]
            new_url = current_app["job_url"]
            jd = current_app["job_description"] or ""

            st.text_area(
                "Saved job description",
                value=jd,
                height=180,
                disabled=True,
                key=f"saved_jd_{app_id}",
            )
        else:
            new_company = ""
            new_role = ""
            new_url = ""
            jd = ""

        save_new = False

    if st.button("Analyze match", type="primary"):
        if not resume.strip():
            st.error("Save your resume first in the Resume profile tab.")

        elif not jd.strip():
            st.error(
                "Paste or save a job description first. "
                "URL fetching is not automatic in this MVP."
            )

        else:
            try:
                match = match_resume_to_job(resume, jd)

                matched_application_id = app_id

                if choice == choices[0] and save_new:
                    if not new_company.strip() or not new_role.strip():
                        st.error(
                            "Enter the company and role before saving this job."
                        )
                        st.stop()

                    matched_application_id = add_application(
                        new_company.strip(),
                        new_role.strip(),
                        new_url.strip(),
                        jd.strip(),
                        "Interested",
                        "",
                        "",
                    )

                elif app_id is not None:
                    update_application(
                        app_id,
                        match_score=match["score"],
                    )

                st.session_state["last_match"] = {
                    "match": match,
                    "jd": jd,
                    "company": new_company,
                    "role": new_role,
                    "url": new_url,
                    "application_id": matched_application_id,
                }

                st.session_state.pop("last_analysis", None)
                st.success("Job match calculated.")

            except Exception as exc:
                st.error(f"Could not analyze this job: {exc}")

    last_match = st.session_state.get("last_match")

    if last_match:
        match = last_match["match"]

        st.metric(
            "Skill overlap indicator",
            f'{match["score"]}%',
        )
        st.caption(match["score_note"])

        col_matched, col_missing = st.columns(2)

        with col_matched:
            st.markdown("**Matched skills**")
            st.write(
                ", ".join(match["matched_skills"])
                or "No overlap detected by the baseline vocabulary."
            )

        with col_missing:
            st.markdown("**Job skills not found in resume**")
            st.write(
                ", ".join(match["missing_skills"])
                or "No missing terms detected by the baseline vocabulary."
            )

        with st.expander("Show all detected skills"):
            st.write(
                "Resume:",
                ", ".join(match["resume_skills"]),
            )
            st.write(
                "Job:",
                ", ".join(match["job_skills"]),
            )

        if st.button("Generate AI fit analysis"):
            try:
                with st.spinner("Analyzing resume evidence..."):
                    analysis = analyze_job(
                        resume,
                        last_match["jd"],
                        match,
                        provider,
                    )

                st.session_state["last_analysis"] = analysis

            except Exception as exc:
                st.error(f"Analysis failed: {exc}")

        if st.session_state.get("last_analysis"):
            st.markdown("### AI fit analysis")
            st.markdown(st.session_state["last_analysis"])


# --------------------------------------------------
# 4. Application drafts
# --------------------------------------------------

with drafts_tab:
    st.subheader("Evidence-grounded application drafts")

    resume = get_resume()
    applications = list_applications()

    if not applications:
        st.info("Add an application with a job description first.")

    else:
        app_labels = {
            f'#{app["id"]} — {app["company"]} / {app["role"]}': app
            for app in applications
        }

        draft_choice = st.selectbox(
            "Application",
            list(app_labels.keys()),
            key="draft_app",
        )

        target = app_labels[draft_choice]

        draft_type = st.selectbox(
            "Draft type",
            [
                "Cover letter",
                "Recruiter message",
                "Application answer",
                "Follow-up email",
            ],
            key="draft_type",
        )

        if st.button("Generate draft", type="primary"):
            if not resume.strip():
                st.error("Save your resume first.")

            elif not (target["job_description"] or "").strip():
                st.error(
                    "This application has no job description. "
                    "Add one in the Applications tab first."
                )

            else:
                try:
                    with st.spinner("Drafting from resume evidence..."):
                        content = create_draft(
                            resume,
                            target["job_description"],
                            draft_type,
                            provider,
                        )

                    save_draft(
                        target["id"],
                        draft_type,
                        content,
                    )

                    st.session_state["current_draft"] = content
                    st.session_state["current_draft_app_id"] = target["id"]

                except Exception as exc:
                    st.error(f"Draft generation failed: {exc}")

        current_draft = st.session_state.get("current_draft")

        if current_draft:
            st.markdown("### Formatted preview")
            st.markdown(current_draft)

            with st.expander("Edit or copy the raw draft"):
                st.text_area(
                    "Generated draft",
                    value=current_draft,
                    height=360,
                    key="draft_raw_view",
                )

            st.warning(
                "Review all details and remove placeholders before sending. "
                "AI-generated drafts are not sent automatically."
            )

    with st.expander("Saved draft history"):
        try:
            saved_drafts = list_drafts()

            if not saved_drafts:
                st.info("No saved drafts yet.")

            else:
                for draft in saved_drafts[:20]:
                    st.markdown(
                        f'**#{draft["id"]} · {draft["draft_type"]} '
                        f'· {draft["created_at"]}**'
                    )
                    st.markdown(draft["content"][:2500])
                    st.divider()

        except Exception as exc:
            st.error(f"Could not load draft history: {exc}")


# --------------------------------------------------
# 5. Interview practice lab
# --------------------------------------------------

with interview_tab:
    st.subheader("Interview practice lab")

    resume = get_resume()
    applications = list_applications()

    if not applications:
        st.info("Add an application with a job description first.")

    else:
        labels = {
            f'#{app["id"]} — {app["company"]} / {app["role"]}': app
            for app in applications
        }

        interview_choice = st.selectbox(
            "Target role",
            list(labels.keys()),
            key="interview_app",
        )

        target = labels[interview_choice]

        mode = st.selectbox(
            "Practice focus",
            [
                "Balanced",
                "Technical",
                "Behavioral",
                "Project deep dive",
            ],
            key="interview_mode",
        )

        if st.button(
            "Generate interview questions",
            type="primary",
        ):
            if not resume.strip():
                st.error("Save your resume first.")

            elif not (target["job_description"] or "").strip():
                st.error(
                    "Add a job description to this application first."
                )

            else:
                try:
                    with st.spinner("Preparing role-specific questions..."):
                        questions = generate_interview_questions(
                            resume,
                            target["job_description"],
                            mode,
                            provider,
                        )

                    st.session_state["interview_questions"] = questions
                    st.session_state["interview_questions_app_id"] = target["id"]

                except Exception as exc:
                    st.error(f"Question generation failed: {exc}")

        current_questions = st.session_state.get("interview_questions")

        if current_questions:
            st.markdown("### Interview questions and answer guidance")
            st.markdown(current_questions)

            with st.expander("View or copy raw text"):
                st.text_area(
                    "Raw interview questions",
                    value=current_questions,
                    height=300,
                    key="interview_questions_raw",
                )

        st.divider()
        st.markdown("### Practice one answer")

        question = st.text_input(
            "Interview question",
            key="practice_question",
        )

        answer = st.text_area(
            "Your answer",
            height=180,
            key="practice_answer",
        )

        if st.button("Evaluate my answer"):
            if not resume.strip():
                st.error("Save your resume first.")

            elif not (target["job_description"] or "").strip():
                st.error(
                    "Add a job description to this application first."
                )

            elif not question.strip() or not answer.strip():
                st.error("Enter both a question and your answer.")

            else:
                try:
                    with st.spinner("Evaluating your answer..."):
                        feedback = evaluate_answer(
                            question,
                            answer,
                            resume,
                            target["job_description"],
                            provider,
                        )

                    save_interview(
                        target["id"],
                        question,
                        answer,
                        feedback,
                    )

                    st.session_state["last_feedback"] = feedback
                    st.session_state["last_feedback_app_id"] = target["id"]

                except Exception as exc:
                    st.error(f"Evaluation failed: {exc}")

        if st.session_state.get("last_feedback"):
            st.markdown("### Answer feedback")
            st.markdown(st.session_state["last_feedback"])

        with st.expander("Practice history"):
            try:
                history = list_interviews()

                if not history:
                    st.info("No practice sessions yet.")

                else:
                    for session in history[:20]:
                        st.markdown(
                            f'**{session["created_at"]} · '
                            f'{session["question"]}**'
                        )

                        st.write("Your answer:", session["answer"])
                        st.markdown("**Feedback**")
                        st.markdown(session["feedback"])
                        st.divider()

            except Exception as exc:
                st.error(f"Could not load practice history: {exc}")
