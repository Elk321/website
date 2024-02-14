import streamlit as st
from st_files_connection import FilesConnection

conn = st.connection("gcs", type=FilesConnection)
def change_limit(changed_limit_name, changed_limit_value):
    lista_tabacchi = conn.read("bartabacchi_website/lista/lista_debiti_tabacchi.csv",
                               input_format="csv", ttl=300)
    lista_mirko = conn.read("bartabacchi_website/lista/lista_debiti_mirko.csv",
                               input_format="csv", ttl=300)
    row_number = lista_tabacchi.index.get_loc(lista_tabacchi[lista_tabacchi["nome"] == changed_limit_name].index[0])
    lista_tabacchi.at[row_number, "limite"] = changed_limit_value
    lista_tabacchi.to_csv("lista/lista_debiti_tabacchi.csv", index=False)
    if changed_limit_name in lista_mirko["nome"].unique():
        row_number = lista_mirko.index.get_loc(lista_mirko[lista_mirko["nome"] == changed_limit_name].index[0])
        lista_mirko.at[row_number, "limite"] = changed_limit_value
        lista_mirko.to_csv("lista/lista_debiti_mirko.csv", index=False)
def show_page_debt_tabacchi():
    st.title("Debiti")
    lista = conn.read("bartabacchi_website/lista/lista_debiti_tabacchi.csv",
                               input_format="csv", ttl=300)
    lista = lista.sort_values(by=["nome"], ignore_index=True)
    lista["nome"] = lista["nome"].apply(lambda x: x.capitalize())
    lista = lista.drop(lista[lista.totale == 0].index)
    height = (len(lista) + 1) * 35 + 3
    lista_show = st.data_editor(lista, hide_index=True,
                           width=2000, height=height,
                           column_config={
                               "nome": "Nome",
                               "totale": st.column_config.NumberColumn
                               ("Totale", format="%.2f"),
                               "limite": "Limite"},
                           key="table",
                           disabled=("nome", "totale"))


    if st.session_state["table"]["edited_rows"]:
        edited_row_name = list(st.session_state["table"]["edited_rows"].keys())
        edited_row_name = edited_row_name[0]
        edited_row_limit = (st.session_state["table"]["edited_rows"]
        [edited_row_name]["limite"])
        changed_limit_name = lista.at[edited_row_name, "nome"].lower()
        change_limit(changed_limit_name, edited_row_limit)
        del st.session_state["table"]["edited_rows"]
        st.rerun()


st.session_state