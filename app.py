"""Hindsight Workout Tracker — a mobile-friendly Streamlit app."""

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from lib.memory import init_bank, log_workout, recall_context, generate_plan, ask_insight, save_completed_plan
from lib.coach import get_response
from lib.models import ActivePlan

# ── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(page_title="Workout Tracker", page_icon="🏋️", layout="centered")

# Larger touch targets for mobile
st.markdown(
    """<style>
    .stCheckbox label { font-size: 1.1rem; padding: 0.3rem 0; }
    .stTextInput input { font-size: 1rem; }
    </style>""",
    unsafe_allow_html=True,
)

# ── Session state defaults ───────────────────────────────────────────────────

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "active_plan" not in st.session_state:
    st.session_state.active_plan = None
if "bank_ready" not in st.session_state:
    with st.spinner("Connecting to Hindsight..."):
        try:
            init_bank()
            st.session_state.bank_ready = True
        except Exception as e:
            st.error(f"Could not connect to Hindsight API: {e}")
            st.stop()

# ── Tabs ─────────────────────────────────────────────────────────────────────

tab_log, tab_plan, tab_insights = st.tabs(["Log", "Plan", "Insights"])

# ── Log tab ──────────────────────────────────────────────────────────────────

with tab_log:
    st.caption("Chat with your coach — log workouts and ask questions.")

    # Render chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("e.g. Squatted 315x5 today"):
        # Show user message immediately
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Recall relevant context, get coach response, and log the workout
                context = recall_context(prompt)
                # Build history for OpenAI (last 10 messages to keep context window small)
                history_for_llm = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.chat_history[-10:]
                ]
                reply = get_response(prompt, context, history_for_llm)
                log_workout(prompt)

            st.markdown(reply)
            st.session_state.chat_history.append({"role": "assistant", "content": reply})

# ── Plan tab ─────────────────────────────────────────────────────────────────

with tab_plan:
    if st.session_state.active_plan is None:
        st.caption("Generate a personalized workout based on your history.")

        col1, col2 = st.columns([3, 1])
        with col1:
            plan_query = st.text_input(
                "What kind of workout?",
                placeholder="Push day, leg day, full body...",
                label_visibility="collapsed",
            )
        with col2:
            generate_btn = st.button("Generate", use_container_width=True)

        if generate_btn and plan_query:
            with st.status("Generating plan...", expanded=True) as status:
                st.write("Recalling your workout history...")
                plan = generate_plan(
                    f"Generate a {plan_query} workout based on my history and strength levels."
                )
                status.update(label="Plan ready!", state="complete")

            st.session_state.active_plan = ActivePlan(plan=plan)
            st.rerun()

    else:
        # ── Active plan follow-along ─────────────────────────────────────
        active: ActivePlan = st.session_state.active_plan
        plan = active.plan

        st.subheader(plan.title)
        if plan.notes:
            st.caption(plan.notes)

        with st.form("plan_form"):
            for i, ex in enumerate(plan.exercises):
                col_check, col_weight = st.columns([3, 1])
                with col_check:
                    done = st.checkbox(
                        f"{ex.name} — {ex.sets}x{ex.reps}",
                        value=active.completed.get(i, False),
                        key=f"ex_{i}",
                    )
                with col_weight:
                    weight = st.text_input(
                        "Weight",
                        value=active.actual_weights.get(i, ex.weight),
                        key=f"wt_{i}",
                        label_visibility="collapsed",
                    )
                active.completed[i] = done
                active.actual_weights[i] = weight

            col_complete, col_discard = st.columns(2)
            with col_complete:
                submitted = st.form_submit_button("Complete Workout", use_container_width=True)
            with col_discard:
                discarded = st.form_submit_button("Discard", use_container_width=True)

        if submitted:
            n_done = sum(1 for v in active.completed.values() if v)
            if n_done == 0:
                st.warning("Check off at least one exercise first.")
            else:
                with st.spinner("Saving workout..."):
                    save_completed_plan(plan, active.completed, active.actual_weights)
                st.session_state.active_plan = None
                st.success(f"Logged {n_done}/{len(plan.exercises)} exercises!")
                st.rerun()

        if discarded:
            st.session_state.active_plan = None
            st.rerun()

# ── Insights tab ─────────────────────────────────────────────────────────────

with tab_insights:
    st.caption("Ask about your progress, PRs, or recovery.")

    # Quick-access buttons
    cols = st.columns(3)
    quick_queries = ["Squat progress", "Weekly volume", "Recovery status"]
    selected_quick = None
    for col, q in zip(cols, quick_queries):
        if col.button(q, use_container_width=True):
            selected_quick = q

    insight_query = st.text_input(
        "Or ask anything:",
        value=selected_quick or "",
        placeholder="How is my bench press trending?",
        label_visibility="collapsed",
    )

    if st.button("Ask", use_container_width=True) and insight_query:
        with st.spinner("Analyzing your history..."):
            answer = ask_insight(insight_query)
        st.markdown(answer)
