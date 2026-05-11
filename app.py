import streamlit as st
import pandas as pd
import sqlite3
import time

# -------------------------
# Page Config
# -------------------------

st.set_page_config(layout="wide")

# -------------------------
# Connect to SQLite Database
# -------------------------

conn = sqlite3.connect("sales.db")

# -------------------------
# Session State
# -------------------------

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "user_question" not in st.session_state:
    st.session_state.user_question = ""

# -------------------------
# Sidebar
# -------------------------

st.sidebar.header("💡 Suggested Questions")

suggestions = [
    "Total Sales",
    "Total Orders",
    "Average Sales",
    "Top Product",
    "Sales by Month",
    "Promo Impact"
]

for s in suggestions:
    if st.sidebar.button(s):
        st.session_state.user_question = s.lower()

# -------------------------
# Product Dashboard
# -------------------------

st.sidebar.header("📊 Product Dashboard")

if st.sidebar.button("Show Top 10 Products"):

    query = """
    SELECT product_name, SUM(sales_amount) as revenue
    FROM sales
    GROUP BY product_name
    ORDER BY revenue DESC
    LIMIT 10
    """

    df = pd.read_sql_query(query, conn)

    st.subheader("🏆 Top 10 Products by Revenue")

    st.dataframe(df)

    st.bar_chart(df.set_index("product_name"))

# -------------------------
# Layout Columns
# -------------------------

col_main, col_chat = st.columns([3,1])

# =========================
# MAIN AREA
# =========================

with col_main:

    st.title("🤖 SalesBuddy AI — Retail Sales Analytics Assistant")

    st.write(
        "Analyze sales trends, product performance, and promotional impact using natural language queries."
    )

    # -------------------------
    # KPI Dashboard
    # -------------------------

    kpi_query = """
    SELECT 
    SUM(sales_amount) as total_sales,
    COUNT(DISTINCT transaction_id) as total_orders,
    AVG(sales_amount) as avg_sales
    FROM sales
    """

    kpi_df = pd.read_sql_query(kpi_query, conn)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Total Sales",
            f"₹{kpi_df['total_sales'][0]:,.0f}"
        )

    with col2:
        st.metric(
            "Total Orders",
            f"{kpi_df['total_orders'][0]:,}"
        )

    with col3:
        st.metric(
            "Average Sales",
            f"₹{kpi_df['avg_sales'][0]:,.2f}"
        )

    st.divider()

    user_question = st.text_input(
        "Ask questions about your sales data and get instant insights",
        value=st.session_state.user_question,
        placeholder="Example: Show top products by sales"
    )

# -------------------------
# Question → SQL Mapping
# -------------------------

def generate_sql(question):

    q = question.lower()

    if "total sales" in q:
        return "SELECT SUM(sales_amount) AS total_sales FROM sales"

    elif "total orders" in q:
        return "SELECT COUNT(DISTINCT transaction_id) AS total_orders FROM sales"

    elif "average sales" in q:
        return "SELECT AVG(sales_amount) AS average_sales FROM sales"

    elif "top product" in q:
        return """
        SELECT product_name, SUM(volume_units) as total_units
        FROM sales
        GROUP BY product_name
        ORDER BY total_units DESC
        LIMIT 5
        """

    elif "sales by month" in q:
        return """
        SELECT transaction_month, SUM(sales_amount) as monthly_sales
        FROM sales
        GROUP BY transaction_month
        """

    elif "promo impact" in q:
        return """
        SELECT promo_offer, SUM(sales_amount) as total_sales
        FROM sales
        GROUP BY promo_offer
        """

    else:
        return None


# -------------------------
# Process Question
# -------------------------

if user_question:

    start = time.time()

    sql_query = generate_sql(user_question)

    if sql_query:

        with st.spinner("SalesBuddy is analyzing your data..."):

            result = pd.read_sql_query(sql_query, conn)

            time.sleep(0.5)

        end = time.time()
        response_time = round(end - start, 3)

        # Save chat history
        st.session_state.chat_history.append(("User", user_question))
        st.session_state.chat_history.append(("SalesBuddy", f"Returned {len(result)} records"))

        # keep last 10 messages
        st.session_state.chat_history = st.session_state.chat_history[-10:]

        with col_main:

            # -------------------------
            # Display Result
            # -------------------------

            st.subheader("Result")

            st.dataframe(result)

            st.write(f"⏱ Response time: {response_time} seconds")

            # -------------------------
            # Charts
            # -------------------------

            if "monthly_sales" in result.columns:

                st.subheader("📈 Monthly Sales Trend")

                st.line_chart(result.set_index("transaction_month"))

            if "total_units" in result.columns:

                st.subheader("🏆 Top Products")

                st.bar_chart(result.set_index("product_name"))

            if "promo_offer" in result.columns:

                st.subheader("🎯 Promotion Impact")

                st.bar_chart(result.set_index("promo_offer"))

            # -------------------------
            # Business Insights
            # -------------------------

            st.subheader("📊 Business Insights")

            if "total_sales" in result.columns:

                value = float(result["total_sales"].iloc[0])

                st.info(f"Total revenue generated is **₹{value:,.2f}**.")

            if "total_units" in result.columns:

                top_product = result.iloc[0]["product_name"]

                st.info(
                    f"Top performing product is **{top_product}** based on units sold."
                )

            if "promo_offer" in result.columns and "total_sales" in result.columns:

                best = result.loc[result["total_sales"].astype(float).idxmax()]

                promo_type = best["promo_offer"]

                promo_sales = float(best["total_sales"])

                if promo_type == "Yes":
                    text = "when promotions are applied"
                else:
                    text = "without promotions"

                st.info(
                    f"Sales are highest **{text}**, generating revenue of **₹{promo_sales:,.2f}**."
                )

            # -------------------------
            # AI Insight
            # -------------------------

            st.subheader("🧠 SalesBuddy Insight")

            if "monthly_sales" in result.columns:

                best_month = result.loc[result["monthly_sales"].idxmax()]

                st.success(
                    f"Highest sales occurred in **Month {best_month['transaction_month']}**."
                )


# =========================
# CHAT HISTORY (RIGHT SIDE)
# =========================

with col_chat:

    st.subheader("💬 Chat History")

    if st.session_state.chat_history:

        chat_df = pd.DataFrame(
            st.session_state.chat_history,
            columns=["Role", "Message"]
        )

        st.dataframe(chat_df, use_container_width=True)

    else:
        st.info("No conversation yet.")

    # -------------------------
    # Download Chat Report
    # -------------------------

    if st.session_state.chat_history:

        report_data = []

        for role, msg in st.session_state.chat_history:

            report_data.append({
                "role": role,
                "content": msg
            })

        report_df = pd.DataFrame(report_data)

        st.download_button(
            label="📥 Download Chat Report",
            data=report_df.to_csv(index=False),
            file_name="chat_report.csv",
            mime="text/csv"
        )

# -------------------------
# Footer
# -------------------------

st.markdown("---")
st.caption("SalesBuddy AI | Retail Analytics Dashboard | Built with Streamlit, SQL, and Python")