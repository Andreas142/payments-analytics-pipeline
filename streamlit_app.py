"""Payments reconciliation dashboard — presents the gold reconciliation mart."""
from pathlib import Path

import altair as alt
import duckdb
import pandas as pd
import streamlit as st

DB_PATH = Path(__file__).parent / "dbt_payments" / "dev.duckdb"
st.set_page_config(page_title="Payments Reconciliation", layout="wide")


@st.cache_data
def load_recon() -> pd.DataFrame:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    df = con.sql("select * from main.fct_order_reconciliation").df()
    con.close()
    return df


df = load_recon()

# ---- Sidebar filters --------------------------------------------------------
st.sidebar.header("Filters")
statuses = sorted(df["order_status"].dropna().unique())
recon_opts = sorted(df["recon_status"].dropna().unique())
methods = sorted(df["dominant_payment_type"].dropna().unique())

sel_status = st.sidebar.multiselect("Order status", statuses, default=statuses)
sel_recon = st.sidebar.multiselect("Reconciliation status", recon_opts, default=recon_opts)
sel_method = st.sidebar.multiselect("Payment method", methods, default=methods)

mask = (
    df["order_status"].isin(sel_status)
    & df["recon_status"].isin(sel_recon)
    & df["dominant_payment_type"].isin(sel_method)
)
fdf = df[mask]

# ---- Header + metrics -------------------------------------------------------
st.title("Payments Reconciliation")
st.caption(
    "Reconciling what customers paid against what their orders were worth, across "
    "~99k real Olist orders. Every order is classified so breaks are explained, not just flagged. "
    "Use the sidebar to filter."
)

total = len(fdf)
reconciled = (fdf["recon_status"] == "reconciled").sum()
suspicious = (fdf["recon_status"] == "underpaid").sum()
flagged_value = fdf.loc[fdf["recon_status"] != "reconciled", "paid_minus_value"].abs().sum()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Orders (filtered)", f"{total:,}")
c2.metric("Reconciled", f"{reconciled / total:.1%}" if total else "-")
c3.metric("Suspicious (underpaid)", f"{suspicious:,}")
c4.metric("Total flagged gap", f"R$ {flagged_value:,.0f}")

st.divider()

# ---- Row 1: status breakdown + payment methods ------------------------------
left, right = st.columns(2)

with left:
    st.subheader("Orders by reconciliation status")
    counts = fdf["recon_status"].value_counts().rename_axis("status").reset_index(name="orders")
    bars = alt.Chart(counts).mark_bar().encode(
        x=alt.X("orders:Q", title="orders"),
        y=alt.Y("status:N", sort="-x", title=None),
        tooltip=["status", "orders"],
    )
    labels = bars.mark_text(align="left", dx=3).encode(text="orders:Q")
    st.altair_chart((bars + labels).properties(height=280), use_container_width=True)

with right:
    st.subheader("Orders by dominant payment method")
    pm = fdf["dominant_payment_type"].value_counts().rename_axis("method").reset_index(name="orders")
    pm_bars = alt.Chart(pm).mark_bar().encode(
        x=alt.X("orders:Q", title="orders"),
        y=alt.Y("method:N", sort="-x", title=None),
        tooltip=["method", "orders"],
    )
    pm_labels = pm_bars.mark_text(align="left", dx=3).encode(text="orders:Q")
    st.altair_chart((pm_bars + pm_labels).properties(height=280), use_container_width=True)

st.divider()

# ---- Row 2: flagged gap over time -------------------------------------------
st.subheader("Reconciliation gap over time")
st.caption("Total absolute gap (R$) from non-reconciled orders, by order month.")
gap = (
    fdf[fdf["recon_status"] != "reconciled"]
    .assign(abs_gap=lambda d: d["paid_minus_value"].abs())
    .groupby("order_month", as_index=False)["abs_gap"].sum()
    .sort_values("order_month")
)
line = alt.Chart(gap).mark_line(point=True).encode(
    x=alt.X("order_month:N", title="order month"),
    y=alt.Y("abs_gap:Q", title="flagged gap (R$)"),
    tooltip=["order_month", alt.Tooltip("abs_gap:Q", format=",.0f")],
).properties(height=280)
st.altair_chart(line, use_container_width=True)

st.divider()

# ---- Row 3: investigation queue --------------------------------------------
st.subheader("Underpaid orders — the investigation queue")
st.caption("Payment below order value with no voucher to explain it — surfaced for review.")
underpaid = (
    fdf[fdf["recon_status"] == "underpaid"]
    [["order_id", "order_status", "dominant_payment_type", "order_value", "total_paid", "paid_minus_value"]]
    .sort_values("paid_minus_value")
)
st.dataframe(underpaid, use_container_width=True, hide_index=True)
