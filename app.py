import streamlit as st
from src.pipeline import SupportAgent


st.set_page_config(
    page_title="AmazonHelp AI Support Agent",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 AmazonHelp AI Support Agent")
st.write(
    "AI-powered customer support demo using historical AmazonHelp conversations."
)

st.divider()

customer_message = st.text_area(
    "Customer Message",
    placeholder="Example: My package has not arrived yet.",
    height=120
)

if st.button("Analyze Customer Message", type="primary"):

    if not customer_message.strip():
        st.warning("Please enter a customer message.")
    else:
        with st.spinner("Analyzing customer message..."):

            try:
                agent = SupportAgent()
                result = agent.handle(customer_message)

                st.divider()

                st.subheader("1️⃣ Intent Classification")
                st.success(result["intent"])

                st.subheader("2️⃣ Historical Evidence")

                evidence = result.get("evidence", [])

                if evidence:
                    for i, item in enumerate(evidence, 1):
                        st.markdown(f"**Example {i}**")

                        customer_text = item.get("customer_text", "")
                        response_text = item.get("response_text", "")

                        st.write("Customer:")
                        st.info(customer_text)

                        st.write("Historical AmazonHelp Response:")
                        st.success(response_text)

                        st.divider()
                else:
                    st.write("No historical evidence found.")

                st.subheader("3️⃣ Draft Reply")
                st.write(result["reply"])

                st.subheader("4️⃣ Automation Decision")

                decision = result["decision"]

                if decision == "AUTO_HANDLE":
                    st.success("✅ AUTO-HANDLE")
                else:
                    st.warning("⚠️ ESCALATE")

                st.write("**Reason:**")
                st.write(result["reason"])

            except Exception as e:
                st.error(f"Error while running the agent: {e}")