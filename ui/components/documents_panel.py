"""
Document requirements panel component
"""
import streamlit as st

def render_documents_panel(documents):
    """
    Render document checklist
    
    Args:
        documents: List of document strings
    """
    st.markdown("### 📄 Required Documents")
    
    if not documents:
        st.success("No additional verification documents required.")
        return
        
    st.markdown("Collect these documents to verify information and mitigate risks.")
    
    # In a real app we might map documents to priorities
    # For now, let's just categorize them simply
    
    for i, doc in enumerate(documents):
        # Determine priority style (simulate logic)
        priority_class = "document-priority-medium"
        if "proof" in doc.lower() or "statement" in doc.lower():
            priority_class = "document-priority-high"
        elif "letter" in doc.lower():
            priority_class = "document-priority-low"
            
        st.markdown(f"""
        <div class="document-item {priority_class}">
            <div style="margin-right: 1rem; color: #3B82F6;">{i+1}.</div>
            <div style="flex-grow: 1;">{doc}</div>
            <input type="checkbox" style="transform: scale(1.5);">
        </div>
        """, unsafe_allow_html=True)
        
    st.info("Check boxes as documents are received and verified.")
