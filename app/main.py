"""
Dhaga & Co. MVP — frontend entrypoint.

Do not build product logic here until docs/discovery_note.md is agreed.
This stub exists so the repo runs and can be deployed early (brief: deploy something trivial in the first two days).
"""

import streamlit as st

st.set_page_config(
    page_title="Dhaga & Co. MVP",
    page_icon="🧵",
    layout="centered",
)

st.title("Dhaga & Co. MVP")
st.caption("FDE Academy · Tech Track · Mini Project 1")

st.info(
    "Discovery first. Fill `docs/discovery_note.md` before wiring workflows. "
    "This screen is a deployable placeholder."
)

st.subheader("Project phases")
st.markdown(
    """
1. **Discover** — decide the problem worth solving and prove why  
2. **Build** — smallest end-to-end MVP with a frontend, deployed to a URL  
3. **Present** — problem, why it matters, live demo (incl. a failure case), what's next  
"""
)

with st.expander("Constraints we will build within"):
    st.markdown(
        """
- Mobile-first, low-end Android, patchy connections  
- Hinglish / vernacular input is normal  
- COD-heavy economics  
- No ML engineer on the client team — must be operable after we leave  
- Fail visibly; never silent wrong answers  
"""
    )

st.divider()
st.caption("Status: scaffold only — discovery not yet locked.")
