import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
from sklearn.ensemble import RandomForestClassifier
# Page config
st.set_page_config(page_title="HR Attrition Dashboard", layout="wide")

# Load model
rf_model = joblib.load("C:/Users/ASUS/OneDrive/Desktop/Employee_Attrition_Prediction_HR/rf_pipeline.pkl")

# Title
st.title("📊 Employee Attrition Prediction Dashboard")
st.markdown("Data-driven insights to reduce employee turnover")

@st.cache_data
def load_data():
    df = pd.read_csv("C:/Users/ASUS/OneDrive/Desktop/Employee_Attrition_Prediction_HR/DATA\WA_Fn-UseC_-HR-Employee-Attrition.csv")

    # CLEAN + CONVERT Attrition safely
    df['Attrition'] = (
        df['Attrition']
        .astype(str)
        .str.strip()
        .str.lower()
        .map({'yes': 1, 'no': 0})
    )

    return df
df=load_data()

# -------------------------------------------------
# KPI SECTION
# -------------------------------------------------
st.subheader("📌 Key Metrics")

col1, col2, col3 = st.columns(3)

total_employees = df.shape[0]
attrition_rate = df['Attrition'].mean() * 100
employees_left = df['Attrition'].sum()

col1.metric("Total Employees", total_employees)
col2.metric("Attrition Rate", f"{attrition_rate:.2f}%")
col3.metric("Employees Left", int(employees_left))

# -------------------------------------------------
# EDA VISUALS
# -------------------------------------------------
st.subheader("📈 Attrition Insights")

col1, col2 = st.columns(2)

# Attrition by OverTime
with col1:
    st.markdown("**Attrition by OverTime**")
    fig, ax = plt.subplots()
    sns.barplot(
        x='OverTime',
        y='Attrition',
        data=df,
        estimator=lambda x: sum(x) / len(x),
        ax=ax
    )
    ax.set_ylabel("Attrition Rate")
    st.pyplot(fig)

# Attrition vs Monthly Income
with col2:
    st.markdown("**Attrition vs Monthly Income**")
    fig, ax = plt.subplots()
    sns.boxplot(
        x='Attrition',
        y='MonthlyIncome',
        data=df,
        ax=ax
    )
    ax.set_xticklabels(["Stayed", "Left"])
    st.pyplot(fig)

# -----------------------------
# FEATURE IMPORTANCE
# -----------------------------
st.subheader("🧠 Top Attrition Drivers")

# Step 1: Find RandomForestClassifier in pipeline
rf = None
for step in rf_model.named_steps.values():
    if isinstance(step, RandomForestClassifier):
        rf = step
        break

if rf is None:
    st.error("⚠️ RandomForestClassifier not found in the pipeline!")
else:
    # Step 2: Try to get feature names from pipeline
    try:
        # If pipeline has preprocessing, get transformed feature names
        feature_names = rf_model[:-1].get_feature_names_out()
    except:
        # fallback: just use generic names if we can't get names
        feature_names = [f"Feature {i}" for i in range(len(rf.feature_importances_))]

    # Step 3: Build feature importance DataFrame
    feature_importance = pd.DataFrame({
        "Feature": feature_names,
        "Importance": rf.feature_importances_
    }).sort_values(by="Importance", ascending=False)

    # Step 4: Display
    st.dataframe(feature_importance.head(10))

    fig, ax = plt.subplots(figsize=(8,4))
    sns.barplot(
        data=feature_importance.head(10),
        x="Importance",
        y="Feature"
    )
    st.pyplot(fig)

# -------------------------------------------------
# SIMPLE INSIGHTS TABLE
# -------------------------------------------------
st.subheader("📊 Attrition Summary")

summary = (
    df.groupby('Department')['Attrition']
    .mean()
    .sort_values(ascending=False)
    .reset_index()
)

summary['Attrition Rate (%)'] = summary['Attrition'] * 100
summary.drop(columns='Attrition', inplace=True)

st.dataframe(summary)


# -----------------------------
# PREDICTION INPUT
# -----------------------------
st.subheader("🔮 Predict Employee Attrition Risk")

user_input = {}
for col in df.drop('Attrition', axis=1).columns:
    if df[col].dtype == 'object' or df[col].dtype.name == 'category':
        # For categorical columns, use selectbox
        options = df[col].unique().tolist()
        user_input[col] = st.selectbox(col, options)
    else:
        # For numeric columns, use number_input
        user_input[col] = st.number_input(
            col,
            min_value=float(df[col].min()),
            max_value=float(df[col].max()),
            value=float(df[col].mean())
        )

input_df = pd.DataFrame([user_input])

if st.button("Predict Attrition Risk"):
    prediction = rf_model.predict(input_df)[0]
    probability = rf_model.predict_proba(input_df)[0][1]

    if prediction == 1:
        st.error(f"⚠️ High Risk Employee (Probability: {probability:.2f})")
    else:
        st.success(f"✅ Low Risk Employee (Probability: {probability:.2f})")