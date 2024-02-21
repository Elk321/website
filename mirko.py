"""

def current_page_mirko():
    date = st.date_input("Data", format="DD/MM/YYYY", key="date")
    with st.expander("Nuovo nome"):
        st.write("Aggiungere il nome se non è presente nella lista:")
        with st.form(key="add_name", clear_on_submit=True, border=False):
            row1 = st.columns(2)
            with row1[0]:
                tip = Attenzione!!!
                    Aggiungere solo se il soggetto non è
                    presente nella lista.
                    Controlla bene!!! Non aggiungere nomi diversi
                    per un singolo soggetto!
                new_name = st.text_input("Nuovo nome",
                                         help=tip)
            with row1[1]:
                st.subheader("")
                button1 = st.form_submit_button("Aggiungi")
                if button1:
                    add_name(new_name, "tabacchi")
                    st.rerun()

    with (st.form(key="add_debt", clear_on_submit=True, border=False)):
        row2 = st.columns(4)
        with row2[0]:
            name_list = read_file("lista/name_list.csv")
            name_list = name_list.sort_values(by=["nome"])
            name = st.selectbox("Nome",
                                name_list["nome"].apply(lambda x: x.capitalize()),
                                placeholder="Seleziona",
                                index=None)
        with row2[1]:
            debiti = st.number_input("Debiti", value=None)

        with row2[2]:
            st.subheader(" ")
            button2 = st.form_submit_button("Aggiungi")
        if button2:
            if not name or not debiti:
                pass
            else:
                if not check_file_exists(f"date/mirko/{date}.csv"):
                    debt_list = pd.DataFrame(columns=["nome", "debiti", "pagati", "oggetto", "ore"])
                    upload_file(f"date/mirko/{date}.csv", debt_list)

                now = datetime.now()
                current_date = now.strftime("%Y-%m-%d")

                if str(date) == current_date:
                    time = now.strftime("%H:%M")
                    total, lista_tabacchi = update_debt_list(name.lower(), debiti, "mirko", lista_tabacchi)
                    debt_journal(name.lower(), debiti, " ", current_date, time, total)
                else:
                    time = " "

                check_blacklist(name)
                add_debt_current(f"date/mirko/{date}.csv",
                                 name=name,
                                 amount=debiti,
                                 object=" ",
                                 hour=time)
                st.success("Aggiunto!")
                st.rerun()

        show_debt_mirko(f"date/mirko/{date}.csv")
        st.subheader(" ")
        try:
            total_debt, total_payement = total_debt_mirko(f"date/mirko/"
                                                          f"{date}.csv")
            st.write(f"<b>Totale debiti:</b> {total_debt}",
                     unsafe_allow_html=True)
            st.write(f"<b>Totale debiti pagati:</b>"
                     f"{total_payement.strip('-')}",
                     unsafe_allow_html=True)

        except (TypeError, FileNotFoundError):
            pass


def show_page_debt_mirko():
    st.title("Debiti")
    lista = read_file("lista/lista_debiti_mirko.csv")
    lista = lista.drop(lista[lista.totale == 0].index)
    lista = lista.sort_values(by=["nome"], ignore_index=True)
    lista["nome"] = lista["nome"].apply(lambda x: x.capitalize())
    height = (len(lista) + 1) * 35 + 3
    lista = st.data_editor(lista, hide_index=True,
                           width=2000, height=height,
                           column_config={
                               "nome": "Nome",
                               "totale": st.column_config.NumberColumn
                               ("Totale", format="%.2f"),
                               "limite": "Limite"},
                           key="table",
                           disabled=True)


def show_debt_mirko(filename):
    if check_file_exists(filename):
        debt_list = read_file(filename, )
        if not debt_list.empty:
            height = (len(debt_list) + 1) * 35 + 3
            debt_list = debt_list.drop(columns="oggetto", axis=1)
            st.dataframe(debt_list,
                         hide_index=True,
                         column_config={
                             "nome": "Nome",
                             "debiti": "Debiti",
                             "pagati": "Pagati",
                             "ore": "Orario"
                         },
                         width=2000, height=height)
        else:
            st.warning("No data available.")
    else:
        st.warning("No data available.")


def total_debt_mirko(filename):
    debt_list = read_file(filename)
    total_amount = 0
    total_payement = 0
    for index, row in debt_list.iterrows():
        if row['debiti'] != " ":
            total_amount += float(row['debiti'].replace(",", "."))
        if row['pagati'] != " ":
            total_payement += float(row['pagati'].replace(",", "."))

        return float_format(total_amount), float_format(total_payement)
"""
