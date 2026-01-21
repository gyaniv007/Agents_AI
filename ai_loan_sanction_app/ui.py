import streamlit as st
import requests
import os

st.title("🏦 AI Bank Loan ")

# 1. User Inputs
name = st.text_input("Applicant Name")
amount = st.number_input("Requested Loan Amount", min_value=1000)
uploaded_file = st.file_uploader("Upload Bank Statement (PDF/CSV)", type=["pdf", "csv"])

if st.button("Submit Application"):
    if uploaded_file and name:
        # 2. Save file locally so the Agent can read the path
        os.makedirs("temp_uploads", exist_ok=True)
        file_path = os.path.join("temp_uploads", uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # 3. Call the FastAPI backend
        payload = {
            "name": name,
            "file_path": file_path,
            "amount": amount
        }
        
        with st.spinner("Agents are analyzing your statement..."):
            response = requests.post("http://127.0.0.1:8000/ai_loan", json=payload)
            
            if response.status_code == 200:
                result = response.json()
                
                # 4. Display Results
                st.success(f"Status: {result.get('final_decision')}")
                st.metric("DTI Ratio", f"{result.get('dti_ratio', 0):.2f}")
                st.write(f"**Risk Category:** {result.get('financial_category')}")
                #st.write(f"Result : ", result)
                
                match result.get('final_decision'):
                    case "Approved":
                        st.balloons()
                        st.info("✅ Congratulations! Loan Sanctioned.")
                       
                    case "Rejected":
                        st.warning("❌ We regret to inform Loan NOT Sanctioned.")

                    case "Conditional":
                        st.warning(f"⚠️ Conditonal Approval. This application has been flagged for Manual Review.")
                    
                    case "Manual Review":
                        st.warning(f"⚠️ Irregularity Found: {result.get('irregularities_found')}. This application has been flagged for Manual Review.")

            else:
                    st.error("Error processing application.")
    else:
        st.error("Please fill in all fields and upload a file.")