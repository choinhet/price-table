import numpy_financial as npf
import pandas as pd
import streamlit as st

if __name__ == "__main__":
    st.set_page_config(layout="wide")

    col1, col2, col3 = st.columns(3)
    with col1:
        n = st.number_input("Número de parcelas", value=48, min_value=1, key="n")
        pmt = st.number_input("Valor da parcela", value=1566.30, key="pmt", format="%.2f")
        adp = st.number_input("Adiantamento padrão", value=1, key="adp")
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
    df["Parcelas Adiantadas"] = adp

    # Input col triggering
    st.session_state["edited_cache"] = {
        **st.session_state.get("edited_cache", {}),
        **st.session_state.get("table", {}).get("edited_rows", {})
    }

    edited_cache = st.session_state.get("edited_cache", {})

    # Cache set
    for idx, it in edited_cache.items():
        for _k, _v in it.items():
            df.loc[idx, _k] = _v

    # Calculations
    qp = []
    pa_tot = []
    desc = []
    for i in range(len(df)):
        cur_total_pa = df.loc[0:i - 1, "Parcelas Adiantadas"].sum()
        cur_pa = df.loc[i, "Parcelas Adiantadas"]

        rp = n - cur_total_pa
        cur_qp = list(range(int(rp), int(rp - cur_pa), -1))
        cur_qp = list(filter(lambda x: x > i + 1, cur_qp))

        pa = 0
        for cur_qp_i in cur_qp:
            d = cur_qp_i - i - 1
            cur_pv = pmt / ((1 + j) ** d)
            pa += cur_pv

        cur_desc = (len(cur_qp) * pmt) - pa
        qp.append(cur_qp)
        pa_tot.append(pa)
        desc.append(cur_desc)

    df["Quais Parcelas"] = qp
    df["Preço Adiantamento"] = pa_tot
    df["Total Mês"] = pmt + df["Preço Adiantamento"]
    df["Desconto"] = desc

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

    i_sdv = df.loc[0, "Saldo Devedor"]
    dva = []
    for i in range(len(df)):
        cur_qp = list(map(lambda x: int(x) - 1, df.loc[i, "Quais Parcelas"]))
        cur_qp = list(filter(lambda x: x >= 0, cur_qp))
        amt_qp = df.loc[cur_qp, "Amortização"].sum()
        amt_p = df.loc[i, "Amortização"]
        cur_dva = i_sdv - amt_qp - amt_p
        i_sdv = cur_dva
        dva.append(cur_dva)

    df["Saldo D. Att"] = dva
    df = df[df["Saldo D. Att"] > 0]

    total_pa = df["Preço Adiantamento"].sum()
    total_n_pa = df[df["Quais Parcelas"].apply(len) > 0]["Parcelas Adiantadas"].sum()
    last_p = df["Data"].max()
    avg_ad = df["Preço Adiantamento"].mean()

    # Formats
    df["Saldo Devedor"] = df["Saldo Devedor"].apply(lambda x: format(x, ",.2f"))
    df["Saldo D. Att"] = df["Saldo D. Att"].apply(lambda x: format(x, ",.2f"))
    df["Juros"] = df["Juros"].apply(lambda x: format(x, ",.2f"))
    df["Amortização"] = df["Amortização"].apply(lambda x: format(x, ",.2f"))
    df["Preço Adiantamento"] = df["Preço Adiantamento"].apply(lambda x: format(x, ",.2f"))
    df["Total Mês"] = df["Total Mês"].apply(lambda x: format(x, ",.2f"))
    df["Desconto"] = df["Desconto"].apply(lambda x: format(x, ",.2f"))

    st.data_editor(
        df,
        hide_index=True,
        height="stretch",
        column_config={
            **{
                col: st.column_config.Column(disabled=True)
                for col in df.columns
            },
            **{
                "Parcelas Adiantadas": st.column_config.NumberColumn(min_value=0, step=1, width="small")
            },
        },
        key="table",
    )

    total_nper = df.shape[0]
    total_paid = (pmt * total_nper) + total_pa

    col1, col2, col3 = st.columns(3)
    with col1:
        st.text(f"Total pago: {total_paid:,.2f}")
        st.text(f"Total parcelas: {total_nper:.0f}")
        st.text(f"Última parcela: {last_p}")
    with col2:
        st.text(f"Total de parcelas adiantadas: {total_n_pa:.0f}")
        st.text(f"Preço médio adiantamento: {avg_ad:,.2f}")
        st.text(f"Média mensal: {avg_ad + pmt:,.2f}")
