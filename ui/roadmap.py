import streamlit as st
import pandas as pd
from database import db

# Define criteria for each level
ROADMAP_DEFINITIONS = {
    "Beginner": {
        "icon": "🌱",
        "description": "Learn the essentials of PySpark including filtering, selecting, and basic string/date operations.",
        "difficulties": ["Easy"],
        "categories": ["Filtering & Sorting", "Date & String"]
    },
    "Intermediate": {
        "icon": "⚡",
        "description": "Master grouping, aggregation, and basic join operations.",
        "difficulties": ["Easy"],
        "categories": ["Aggregations", "Joins"]
    },
    "Advanced": {
        "icon": "🔥",
        "description": "Dive deeper into complex joining, advanced transformations, and handling null values.",
        "difficulties": ["Medium"],
        "categories": ["Filtering & Sorting", "Date & String", "Joins", "Data Cleaning & Null Handling"]
    },
    "Expert": {
        "icon": "🏆",
        "description": "Solve challenging grouping puzzles, advanced window functions, and array/map manipulations.",
        "difficulties": ["Medium"],
        "categories": ["Aggregations", "Window Functions", "Array & Map Operations"]
    },
    "Master": {
        "icon": "👑",
        "description": "Conquer nested data structures, pivoting, optimizations, and custom User Defined Functions (UDFs).",
        "difficulties": ["Medium", "Hard"],
        "categories": ["Advanced Nested & Pivot", "Performance & Optimization", "User Defined Functions (UDFs)"]
    }
}

def get_roadmap_problems(level, all_problems):
    defn = ROADMAP_DEFINITIONS[level]
    probs = []
    for p in all_problems:
        if p["difficulty"] in defn["difficulties"] and p["category"] in defn["categories"]:
            probs.append(p)
    return probs

def show():
    st.title("🗺️ PySpark Learning Roadmaps")
    st.write("Embark on curated paths to level up your PySpark coding. Opt-in to track your progress and solve challenges.")

    db.init_db()
    opted_roadmaps = db.get_opted_roadmaps()
    all_problems = db.get_problems()
    submissions = db.get_submissions()
    
    solved_ids = set(s["problem_id"] for s in submissions if s["status"] == "PASS")
    attempted_ids = set(s["problem_id"] for s in submissions)

    # Let's display the roadmaps in cards
    st.subheader("Explore Roadmap Paths")
    
    cols = st.columns(5)
    selected_level = st.session_state.get("selected_roadmap_level", "Beginner")

    for idx, (level, defn) in enumerate(ROADMAP_DEFINITIONS.items()):
        with cols[idx]:
            is_opted = opted_roadmaps.get(level, 0) == 1
            opted_badge = "🟢 Opted In" if is_opted else "⚪ Not Opted In"
            
            # Filter problems for this level
            level_probs = get_roadmap_problems(level, all_problems)
            total = len(level_probs)
            solved = sum(1 for p in level_probs if p["id"] in solved_ids)
            pct = int((solved / total * 100)) if total > 0 else 0
            
            # Card styling
            active_border = "border: 2px solid #ff4b4b;" if selected_level == level else "border: 1px solid #333;"
            bg_color = "#2b2b2b" if selected_level == level else "#1e1e1e"
            
            st.markdown(
                f"""
                <div style="background-color: {bg_color}; padding: 15px; border-radius: 10px; {active_border} text-align: center; height: 100%;">
                    <h3 style="margin: 0; font-size: 2.2rem;">{defn['icon']}</h3>
                    <h4 style="margin: 5px 0 0 0; color: #fff;">{level}</h4>
                    <p style="font-size: 0.8rem; color: #aaa; margin: 5px 0 10px 0; height: 60px; overflow: hidden;">{defn['description']}</p>
                    <div style="font-weight: bold; margin-bottom: 5px; color: #ffc107;">{pct}% Completed</div>
                    <div style="font-size: 0.85rem; color: #888; margin-bottom: 10px;">{solved} / {total} Solved</div>
                    <div style="font-size: 0.85rem; font-weight: bold; color: {'#107c41' if is_opted else '#888'}; margin-bottom: 10px;">{opted_badge}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Opt-in and select buttons
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if is_opted:
                    if st.button("Opt Out", key=f"opt_out_{level}", use_container_width=True):
                        db.opt_in_roadmap(level, False)
                        st.success(f"Opted out of {level}!")
                        st.rerun()
                else:
                    if st.button("Opt In", key=f"opt_in_{level}", use_container_width=True):
                        db.opt_in_roadmap(level, True)
                        st.success(f"Opted into {level}!")
                        st.rerun()
            with col_b2:
                if st.button("View List", key=f"view_{level}", use_container_width=True):
                    st.session_state["selected_roadmap_level"] = level
                    st.rerun()

    # Detailed view of the selected roadmap
    st.write("---")
    st.subheader(f"📋 {selected_level} Roadmap Details")
    
    defn = ROADMAP_DEFINITIONS[selected_level]
    st.info(f"**Description:** {defn['description']}")
    
    level_probs = get_roadmap_problems(selected_level, all_problems)
    
    if not level_probs:
        st.info("No problems assigned to this roadmap level yet.")
        return

    # Let's show problem list with progress tracking
    display_data = []
    for p in level_probs:
        p_id = p["id"]
        status = "⚪ Unsolved"
        if p_id in solved_ids:
            status = "🟢 Solved"
        elif p_id in attempted_ids:
            status = "🟡 Attempted"
            
        display_data.append({
            "Status": status,
            "ID": p_id,
            "Title": p["title"],
            "Category": p["category"],
            "Difficulty": p["difficulty"]
        })
        
    df = pd.DataFrame(display_data)
    
    # We display a table where the user can choose a problem
    for idx, row in df.iterrows():
        r_col1, r_col2, r_col3, r_col4, r_col5, r_col6 = st.columns([1, 1, 3, 2, 1, 1.5])
        with r_col1:
            st.write(row["Status"])
        with r_col2:
            st.write(row["ID"])
        with r_col3:
            st.write(row["Title"])
        with r_col4:
            st.write(row["Category"])
        with r_col5:
            st.write(row["Difficulty"])
        with r_col6:
            if st.button("💻 Solve", key=f"solve_btn_{row['ID']}", use_container_width=True):
                st.session_state["selected_problem_id"] = row["ID"]
                st.session_state["active_page"] = "💻 Practice Sandbox"
                st.rerun()
