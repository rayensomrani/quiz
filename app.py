import streamlit as st
import pandas as pd
import random
import time
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import streamlit_authenticator as stauth
from reportlab.lib.pagesizes import letter
from io import BytesIO
import time
# --- CONFIGURATION UTILISATEURS ---
names = ["Admin", "Pilote"]
usernames = ["admin", "pilote"]
passwords = ["admin123", "pilote123"]
hashed_passwords = stauth.Hasher(passwords).generate()

authenticator = stauth.Authenticate(names, usernames, hashed_passwords,
                                     "quiz_nvgs", "abcdef", cookie_expiry_days=1)

name, auth_status, username = authenticator.login("🔐 Connexion", "sidebar")

if auth_status is False:
    st.error("Mot de passe incorrect")
    st.stop()
elif auth_status is None:
    st.warning("Veuillez entrer vos identifiants")
    st.stop()

# --- CHARGEMENT DES QUESTIONS ---
@st.cache_data
def load_questions():
    df = pd.read_excel("NVG_TEST.xlsx")
    df = df.dropna(subset=["Question", "Bonne réponse"])
    return df

df = load_questions()

# --- INITIALISATION SESSION ---
if "responses" not in st.session_state:
    st.session_state.responses = {}
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "quiz" not in st.session_state:
    st.session_state.quiz = None

# --- FONCTION PDF ---
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

# --- INTERFACE ---
st.set_page_config(page_title="Quiz NVG", layout="wide")
st.markdown("<h2 style='color:#007ACC;'>🛫 Application de Test NVG</h2>", unsafe_allow_html=True)
st.sidebar.success(f"Bienvenue {name} 👋")

role = "Admin" if username == "admin" else "Pilote"

if role == "Pilote":
    st.header("👨‍✈️ Espace Pilote")

    if st.button("🎬 Début du Test"):
        st.session_state.start_time = time.time()
        st.session_state.responses = {}
        st.session_state.quiz = df.sample(n=20).reset_index(drop=True)

    if st.session_state.start_time and st.session_state.quiz is not None:
        elapsed = time.time() - st.session_state.start_time
        remaining = max(0, 1800 - int(elapsed))
        minutes, seconds = divmod(remaining, 60)
        st.warning(f"⏳ Temps restant : {minutes:02d}:{seconds:02d}")

        if remaining == 0:
            st.error("⛔ Temps écoulé ! Le test est terminé.")
        else:
            for i, row in st.session_state.quiz.iterrows():
                st.write(f"**Q{i+1}: {row['Question']}**")
                options = [row.get(opt) for opt in ['A', 'B', 'C', 'D'] if pd.notna(row.get(opt))]
                response = st.radio("Votre réponse :", options, key=f"q_{i}")
                st.session_state.responses[i] = response

            if st.button("✅ Soumettre"):
                score = 0
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

    st.subheader("✏️ Rectifier une question existante")
    question_index = st.number_input("Numéro de la question à modifier", min_value=0, max_value=len(df)-1, step=1)
    st.write(f"Question actuelle : {df.iloc[question_index]['Question']}")
    updated_question = st.text_area("Nouvelle question", value=df.iloc[question_index]['Question'])
    updated_A = st.text_input("Nouvelle option A", value=df.iloc[question_index]['A'])
    updated_B = st.text_input("Nouvelle option B", value=df.iloc[question_index]['B'])
    updated_C = st.text_input("Nouvelle option C", value=df.iloc[question_index]['C'])
    updated_D = st.text_input("Nouvelle option D", value=df.iloc[question_index]['D'])
    updated_correct = st.text_input("Nouvelle bonne réponse", value=df.iloc[question_index]['Bonne réponse'])

    if st.button("💾 Rectifier"):
        df.at[question_index, "Question"] = updated_question
        df.at[question_index, "A"] = updated_A
        df.at[question_index, "B"] = updated_B
        df.at[question_index, "C"] = updated_C
        df.at[question_index, "D"] = updated_D
        df.at[question_index, "Bonne réponse"] = updated_correct
        df.to_excel("NVG_TEST.xlsx", index=False)
        st.success("✅ Question modifiée avec succès.")
def generate_pdf(score, total):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.drawString(100, 750, f"Quiz Results: {score}/{total}")
    p.save()
    buffer.seek(0)
    return buffer

# Dans la section résultats, ajoutez :
pdf_file = generate_pdf(st.session_state.score, len(QUESTIONS))
st.download_button("📄 Télécharger PDF", data=pdf_file, file_name="results.pdf")

