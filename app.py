import pandas as pd
import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Robô Auditor Moto X", page_icon="🏍️", layout="wide"
)

# Estilização visual com CSS customizado
st.markdown(
    """
    <style>
    .main { background-color: #0f172a; color: #f8fafc; }
    .stMetric { background-color: #1e293b; padding: 15px; border-radius: 10px; border: 1px solid #334155; }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("🏍️ Robô de Auditoria | Moto X - Rio Grande do Sul")
st.markdown(
    "Faça o upload das planilhas abaixo para cruzar os dados, auditar valores e verificar duplicados automaticamente."
)

# Layout de colunas para os uploads
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Gestão Moto X (Comissões)")
    file_moto = st.file_uploader(
        "Envie a planilha da Moto X",
        type=["xlsx", "xls", "csv"],
        key="moto",
    )

with col2:
    st.subheader("2. Motoristas Auxiliares")
    file_aux = st.file_uploader(
        "Envie a planilha de Auxiliares",
        type=["xlsx", "xls", "csv"],
        key="aux",
    )

if file_moto and file_aux:
    try:
        # Leitura da planilha Moto X
        df_moto_raw = pd.read_excel(file_moto, skiprows=1)
        col_nome_moto = [
            c
            for c in df_moto_raw.columns
            if "nome" in str(c).lower() and "completo" in str(c).lower()
        ]
        col_comissao = [
            c
            for c in df_moto_raw.columns
            if "comissões" in str(c).lower() or "comissao" in str(c).lower()
        ]

        if not col_nome_moto or not col_comissao:
            df_moto_raw = pd.read_excel(file_moto)
            col_nome_moto = [
                c
                for c in df_moto_raw.columns
                if "nome" in str(c).lower() and "completo" in str(c).lower()
            ]
            col_comissao = [
                c for c in df_moto_raw.columns if "comissão" in str(c).lower()
            ]

        # Leitura da planilha Auxiliares
        df_aux_raw = pd.read_excel(file_aux, skiprows=1)
        col_nome_aux = [
            c for c in df_aux_raw.columns if "auxiliar" in str(c).lower()
        ]
        col_valor = [
            c for c in df_aux_raw.columns if "valor" in str(c).lower()
        ]
        col_empresa = [
            c for c in df_aux_raw.columns if "empresa" in str(c).lower()
        ]

        if not col_nome_aux or not col_valor:
            df_aux_raw = pd.read_excel(file_aux)
            col_nome_aux = [
                c for c in df_aux_raw.columns if "auxiliar" in str(c).lower()
            ]
            col_valor = [
                c for c in df_aux_raw.columns if "valor" in str(c).lower()
            ]
            col_empresa = [
                c for c in df_aux_raw.columns if "empresa" in str(c).lower()
            ]

        # Processamento Moto X
        nome_m_col = col_nome_moto[0] if col_nome_moto else df_moto_raw.columns[0]
        com_col = col_comissao[0] if col_comissao else df_moto_raw.columns[8]

        df_moto = pd.DataFrame()
        df_moto["clean_name"] = (
            df_moto_raw[nome_m_col].astype(str).str.strip().str.upper()
        )
        df_moto["comissao"] = pd.to_numeric(
            df_moto_raw[com_col], errors="coerce"
        ).fillna(0)
        moto_map = dict(zip(df_moto["clean_name"], df_moto["comissao"]))

        # Processamento Auxiliares
        nome_a_col = col_nome_aux[0] if col_nome_aux else df_aux_raw.columns[7]
        val_col = col_valor[0] if col_valor else df_aux_raw.columns[13]
        emp_col = (
            col_empresa[0] if col_empresa else df_aux_raw.columns[4]
        )

        df_aux = pd.DataFrame()
        df_aux["original_name"] = df_aux_raw[nome_a_col].astype(str).str.strip()
        df_aux["clean_name"] = df_aux["original_name"].str.upper()
        df_aux["empresa"] = (
            df_aux_raw[emp_col].astype(str) if emp_col else "-"
        )

        # Converter valores para float
        def parse_valor(val):
            if pd.isna(val):
                return 0.0
            if isinstance(val, (int, float)):
                return float(val)
            val_str = (
                str(val)
                .replace("R$", "")
                .replace(".", "")
                .replace(",", ".")
                .strip()
            )
            try:
                return float(val_str)
            except:
                return 0.0

        df_aux["valor"] = df_aux_raw[val_col].apply(parse_valor)

        # Verificação de Duplicados
        duplicados = (
            df_aux[df_aux["clean_name"].duplicated(keep=False)][
                "original_name"
            ]
            .unique()
            .tolist()
        )

        if duplicados:
            st.warning(
                f"⚠️ **Atenção:** Foram encontrados nomes duplicados na planilha de auxiliares: {', '.join(duplicados)}"
            )

        # Cruzamento e Auditoria
        resultados = []
        divergencias_count = 0
        total_geral = df_aux["valor"].sum()

        for _, row in df_aux.iterrows():
            c_name = row["clean_name"]
            val = row["valor"]
            emp = row["empresa"]
            orig = row["original_name"]

            comissao_moto = moto_map.get(c_name, None)

            if comissao_moto is None:
                status = "Não Encontrado"
                divergencias_count += 1
            elif abs(val - comissao_moto) > 0.01:
                status = "Divergente"
                divergencias_count += 1
            else:
                status = "OK (Batido)"

            resultados.append(
                {
                    "Motorista Auxiliar": orig,
                    "Empresa": emp,
                    "Valor Auxiliar": val,
                    "Comissão Moto X": (
                        comissao_moto if comissao_moto is not None else 0.0
                    ),
                    "Status": status,
                }
            )

        df_res = pd.DataFrame(resultados)

        # Exibição de KPIs
        st.markdown("---")
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        with kpi1:
            st.metric("Total Auxiliares", len(df_res))
        with kpi2:
            st.metric("Divergências / Erros", divergencias_count)
        with kpi3:
            st.metric("Nomes Duplicados", len(duplicados))
        with kpi4:
            st.metric(
                "Valor Total a Pagar",
                f"R$ {total_geral:,.2f}".replace(",", "X")
                .replace(".", ",")
                .replace("X", "."),
            )

        # Filtros na tabela
        st.markdown("### 📋 Tabela de Auditoria")
        filtro_status = st.selectbox(
            "Filtrar por Status:",
            ["Todos", "OK (Batido)", "Divergente", "Não Encontrado"],
        )

        df_filtered = df_res.copy()
        if filtro_status != "Todos":
            df_filtered = df_res[df_res["Status"] == filtro_status]

        st.dataframe(df_filtered, use_container_width=True)


        @st.cache_data
        def convert_df_to_excel(df):
            from io import BytesIO

            output = BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df.to_excel(output, index=False, sheet_name="Auditoria")
            return output.getvalue()


        excel_data = convert_df_to_excel(df_res)
        st.download_button(
            label="📥 Baixar Relatório de Auditoria em Excel",
            data=excel_data,
            file_name="Relatorio_Auditoria_MotoX.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    except Exception as e:
        st.error(
            f"Erro ao processar as planilhas. Verifique se os arquivos correspondem aos modelos esperados. Detalhe: {e}"
        )
else:
    st.info(
        "👈 Por favor, faça o upload de **ambas as planilhas** nas caixas acima para iniciar a auditoria."
    )