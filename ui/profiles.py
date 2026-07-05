import streamlit as st
import json
from database import db

def show():
    st.title("⚡ Spark Execution Profiles")
    st.write("Configure resource allocations, Adaptive Query Execution (AQE), parallelism, and shuffle partitions for your local PySpark executions.")
    
    db.init_db()
    
    profiles = db.get_profiles()
    
    # Render existing profiles in a nice table
    st.subheader("Current Profiles")
    profile_data = []
    for p in profiles:
        profile_data.append({
            "Profile Name": p["name"],
            "Master": p["master"],
            "Driver Memory": p["driver_memory"],
            "Executor Memory": p["executor_memory"],
            "Cores": p["executor_cores"],
            "Shuffle Partitions": p["shuffle_partitions"],
            "AQE Enabled": "Yes" if p["adaptive_query_execution"] == 1 else "No",
            "Broadcast Threshold": f"{p['broadcast_threshold'] / (1024*1024):.1f} MB",
            "Default Parallelism": p["default_parallelism"]
        })
        
    st.dataframe(profile_data, use_container_width=True, hide_index=True)
    
    # Profile Editor form
    st.write("---")
    st.subheader("➕ Create or Edit Profile")
    
    with st.form("profile_form"):
        # Select existing to edit, or Create New
        profile_names = ["-- Create New --"] + [p["name"] for p in profiles]
        selected_to_edit = st.selectbox("Select Profile to Edit/Overwrite (Choose 'Create New' to add a new profile)", profile_names)
        
        # Load values if editing
        edit_profile = None
        if selected_to_edit != "-- Create New --":
            edit_profile = db.get_profile(selected_to_edit)
            
        p_name = st.text_input("Profile Name", edit_profile["name"] if edit_profile else "")
        p_master = st.text_input("Master URL", edit_profile["master"] if edit_profile else "local[*]")
        
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            p_driver_mem = st.text_input("Driver Memory (e.g., 1g, 2g)", edit_profile["driver_memory"] if edit_profile else "1g")
            p_exec_cores = st.number_input("Executor Cores", min_value=1, max_value=32, value=edit_profile["executor_cores"] if edit_profile else 1)
            p_aqe = st.checkbox("Enable Adaptive Query Execution (AQE)", value=True if not edit_profile or edit_profile["adaptive_query_execution"] == 1 else False)
            p_serializer = st.text_input("Serializer Class", edit_profile["serializer"] if edit_profile else "org.apache.spark.serializer.KryoSerializer")
        with col_r2:
            p_exec_mem = st.text_input("Executor Memory (e.g., 1g, 2g)", edit_profile["executor_memory"] if edit_profile else "1g")
            p_shuffle_parts = st.number_input("Shuffle Partitions", min_value=1, max_value=1000, value=edit_profile["shuffle_partitions"] if edit_profile else 2)
            p_broadcast = st.number_input("Broadcast Threshold (bytes)", min_value=-1, value=edit_profile["broadcast_threshold"] if edit_profile else 10485760, help="-1 disables broadcasting")
            p_parallelism = st.number_input("Default Parallelism", min_value=1, max_value=100, value=edit_profile["default_parallelism"] if edit_profile else 2)
            
        p_extra = st.text_area("Extra Configurations (JSON representation)", edit_profile["extra_configs"] if edit_profile else "{}")
        
        submitted = st.form_submit_button("Save Profile")
        if submitted:
            if not p_name.strip():
                st.error("Profile name is required.")
            else:
                try:
                    # Validate JSON
                    extra_json = json.loads(p_extra) if p_extra.strip() else {}
                    db.save_profile(
                        name=p_name.strip(),
                        master=p_master.strip(),
                        driver_memory=p_driver_mem.strip(),
                        executor_memory=p_exec_mem.strip(),
                        executor_cores=p_exec_cores,
                        shuffle_partitions=p_shuffle_parts,
                        aeq=1 if p_aqe else 0,
                        broadcast_threshold=p_broadcast,
                        serializer=p_serializer.strip(),
                        default_parallelism=p_parallelism,
                        extra_configs=extra_json
                    )
                    st.success(f"Profile '{p_name}' saved successfully!")
                    st.rerun()
                except json.JSONDecodeError:
                    st.error("Extra configurations must be valid JSON.")
                except Exception as e:
                    st.error(f"Error saving profile: {str(e)}")
                    
    # Delete Profile
    if len(profiles) > 1:
        st.write("---")
        st.subheader("❌ Delete Profile")
        delete_target = st.selectbox("Select Profile to Delete", [p["name"] for p in profiles if p["name"] not in ["Interview", "Laptop"]])
        if st.button("Delete Selected Profile", type="primary"):
            try:
                db.delete_profile(delete_target)
                st.success(f"Profile '{delete_target}' deleted successfully.")
                st.rerun()
            except Exception as e:
                st.error(f"Error deleting profile: {str(e)}")
