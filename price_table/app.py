import numpy_financial as npf
import pandas as pd
import streamlit as st

if __name__ == "__main__":
    col1, col2, col3 = st.columns(3)
    with col1:
        n = st.number_input("Número de parcelas", value=48, min_value=1, key="n")
        pmt = st.number_input("Valor da parcela", value=1566.30, key="pmt", format="%.2f")
    with col2:
        v = st.number_input("Valor do investimento", value=51_621.65, key="v", format="%.2f")
        m = st.date_input("Mês de início", value="2025-09-01", key="m")
    with col3:
        j = npf.rate(nper=n, pmt=-pmt, pv=v, fv=0, when="end")
        st.text_input("Juros mensais (Calculado)", value=f"{j:.2%}")
        t = n * pmt
        st.text_input("Total (Calculado)", value=f"{t:,.2f}")

    df = pd.DataFrame(
        data={
            "# Parcela": range(1, n + 1),
            "Data": pd.date_range(m, periods=n, freq="ME"),
        }
    )

    # Values
    df["Data"] = df["Data"].dt.strftime("%Y-%m")
    df["Parcela"] = pmt

    rolling_v = [v]
    rolling_j = [j * v]
    rolling_a = [pmt - j * v]

    for i in range(1, len(df)):
        prev_v = rolling_v[i - 1]
        prev_j = rolling_j[i - 1]
        prev_a = rolling_a[i - 1]

        cur_v = prev_v - prev_a
        cur_j = cur_v * j
        cur_a = pmt - cur_j

        rolling_v.append(cur_v)
        rolling_j.append(cur_j)
        rolling_a.append(cur_a)

    df["Juros"] = rolling_j
    df["Amortização"] = rolling_a
    df["Saldo Devedor"] = rolling_v

    # Formats
    df["Saldo Devedor"] = df["Saldo Devedor"].apply(lambda x: format(x, ",.2f"))
    df["Juros"] = df["Juros"].apply(lambda x: format(x, ",.2f"))
    df["Amortização"] = df["Amortização"].apply(lambda x: format(x, ",.2f"))
    df["Parcela"] = df["Parcela"].apply(lambda x: format(x, ",.2f"))

    st.dataframe(
        df,
        hide_index=True,
        height="stretch",
    )
