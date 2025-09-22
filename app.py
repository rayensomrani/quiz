import streamlit as st
import pandas as pd
import random
import time

# Chargement du fichier Excel
@st.cache_data
def load_questions():
    df = pd.read_excel("NVG_TEST.xlsx")
    df = df.dropna(subset=["Question", "Bonne réponse"])
    return df

df = load_questions()

# Interface principale
st.set_page_config(page_title="Quiz NVG", layout="wide")
st.title("🛩️ Application de Test NVG")

# Sélection du rôle
role = st.sidebar.selectbox("Choisissez votre rôle", ["Pilote", "Admin"])

# Stockage des réponses
if "responses" not in st.session_state:
    st.session_state.responses = {}

if "start_time" not in st.session_state:
    st.session_state.start_time = None

if role == "Pilote":
    st.header("👨‍✈️ Espace Pilote")

    if st.button("🎬 Début du Test"):
        st.session_state.start_time = time.time()
        st.session_state.responses = {}
        st.session_state.quiz = df.sample(n=20).reset_index(drop=True)

    if st.session_state.start_time:
        elapsed = time.time() - st.session_state.start_time
        remaining = max(0, 1800 - int(elapsed))
        minutes, seconds = divmod(remaining, 60)
        st.warning(f"⏳ Temps restant : {minutes:02d}:{seconds:02d}")

        if remaining == 0:
            st.error("⛔ Temps écoulé ! Le test est terminé.")
        else:
            score = 0
            for i, row in st.session_state.quiz.iterrows():
                st.write(f"**Q{i+1}: {row['Question']}**")
                options = [row.get(opt) for opt in ['A', 'B', 'C', 'D'] if pd.notna(row.get(opt))]
                response = st.radio("Votre réponse :", options, key=f"q_{i}")
                st.session_state.responses[i] = response

            if st.button("✅ Soumettre"):
                for i, row in st.session_state.quiz.iterrows():
                    correct = row['Bonne réponse']
                    selected = st.session_state.responses.get(i)
                    if selected and selected.strip().lower() == correct.strip().lower():
                        score += 1
                note = round((score / 20) * 20, 2)
                st.success(f"🎯 Votre note est : {note}/20")
                st.write("📋 Résumé des réponses :")
                for i, row in st.session_state.quiz.iterrows():
                    st.write(f"Q{i+1}: {row['Question']}")
                    st.write(f"Votre réponse : {st.session_state.responses.get(i)}")
                    st.write(f"Bonne réponse : {row['Bonne réponse']}")
                    st.write("---")

elif role == "Admin":
    st.header("🛠️ Espace Admin")

    st.subheader("📌 Ajouter une nouvelle question")
    new_question = st.text_area("Question")
    new_A = st.text_input("Option A")
    new_B = st.text_input("Option B")
    new_C = st.text_input("Option C")
    new_D = st.text_input("Option D")
    new_correct = st.text_input("Bonne réponse")

    if st.button("➕ Ajouter"):
        new_row = {
            "Question": new_question,
            "A": new_A,
            "B": new_B,
            "C": new_C,
            "D": new_D,
            "Bonne réponse": new_correct
        }
        df = df.append(new_row, ignore_index=True)
        df.to_excel("NVG_TEST.xlsx", index=False)
        st.success("✅ Question ajoutée avec succès.")

    st.subheader("📝 Rectifier une question existante")
    question_index = st.number_input("Numéro de la question à modifier", min_value=0, max_value=len(df)-1, step=1)
    st.write(f"Question actuelle : {df.iloc[question_index]['Question']}")
    updated_question = st.text_area("Nouvelle question", value=df.iloc[question_index]['Question'])
    updated_A = st.text_input("Nouvelle option A", value=df.iloc[question_index]['A'])
    updated_B = st.text_input("Nouvelle option B", value=df.iloc[question_index]['B'])
    updated_C = st.text_input("Nouvelle option C", value=df.iloc[question_index]['C'])
    updated_D = st.text_input("Nouvelle option D", value=df.iloc[question_index]['D'])
    updated_correct = st.text_input("Nouvelle bonne réponse", value=df.iloc[question_index]['Bonne réponse'])

    if st.button("✏️ Rectifier"):
        df.at[question_index, "Question"] = updated_question
        df.at[question_index, "A"] = updated_A
        df.at[question_index, "B"] = updated_B
        df.at[question_index, "C"] = updated_C
        df.at[question_index, "D"] = updated_D
        df.at[question_index, "Bonne réponse"] = updated_correct
        df.to_excel("NVG_TEST.xlsx", index=False)
        st.success("✅ Question modifiée avec succès.")
import streamlit_authenticator as stauth

# Configuration des utilisateurs
names = ["Admin", "Pilote"]
usernames = ["admin", "pilote"]
passwords = ["admin123", "pilote123"]  # À sécuriser en production

hashed_passwords = stauth.Hasher(passwords).generate()

authenticator = stauth.Authenticate(names, usernames, hashed_passwords, "quiz_nvgs", "abcdef", cookie_expiry_days=1)

name, authentication_status, username = authenticator.login("🔐 Connexion", "sidebar")

if authentication_status:
    st.sidebar.success(f"Bienvenue {name} 👋")
    role = "Admin" if username == "admin" else "Pilote"
elif authentication_status is False:
    st.sidebar.error("Mot de passe incorrect")
elif authentication_status is None:
    st.stop()

    from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def generate_pdf(name, score, responses, quiz):
    filename = f"Evaluation_{name}.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 50, f"Feuille d'évaluation - {name}")
    c.drawString(50, height - 70, f"Note finale : {score}/20")
    y = height - 100
    for i, row in quiz.iterrows():
        question = row['Question']
        correct = row['Bonne réponse']
        user_answer = responses.get(i, "Non répondu")
        c.drawString(50, y, f"Q{i+1}: {question}")
        y -= 15
        c.drawString(70, y, f"Réponse du pilote : {user_answer}")
        y -= 15
        c.drawString(70, y, f"Bonne réponse : {correct}")
        y -= 30
        if y < 100:
            c.showPage()
            y = height - 50
    c.save()
    return filename
if st.button("✅ Soumettre"):
    for i, row in st.session_state.quiz.iterrows():
        correct = row['Bonne réponse']
        selected = st.session_state.responses.get(i)
        if selected and selected.strip().lower() == correct.strip().lower():
            score += 1
    note = round((score / 20) * 20, 2)
    st.success(f"🎯 Votre note est : {note}/20")

    pdf_file = generate_pdf(name, note, st.session_state.responses, st.session_state.quiz)
    with open(pdf_file, "rb") as f:
        st.download_button("📥 Télécharger la feuille d’évaluation", f, file_name=pdf_file)
