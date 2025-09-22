import streamlit as st
import pandas as pd
import time
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
import streamlit_authenticator as stauth
from datetime import datetime
import base64

# --- CONFIGURATION DES UTILISATEURS ---
credentials = {
    "usernames": {
        "admin": {
            "name": "Admin",
            "password": stauth.Hasher(["admin123"]).generate()[0]
        },
        "pilote": {
            "name": "Pilote",
            "password": stauth.Hasher(["pilote123"]).generate()[0]
        }
    }
}

authenticator = stauth.Authenticate(
    credentials,
    "quiz_nvgs",
    "abcdef",
    cookie_expiry_days=1
)

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
    try:
        df = pd.read_excel("NVG_TEST.xlsx")
        df = df.dropna(subset=["Question", "Bonne réponse"])
        
        # Debug: Afficher les noms de colonnes pour vérification
        st.sidebar.write("🔍 Colonnes détectées dans le fichier Excel:")
        st.sidebar.write(list(df.columns))
        
        return df
    except Exception as e:
        st.error(f"Erreur lors du chargement du fichier Excel: {e}")
        return pd.DataFrame()

df = load_questions()

# --- INITIALISATION SESSION ---
if "responses" not in st.session_state:
    st.session_state.responses = {}
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "quiz" not in st.session_state:
    st.session_state.quiz = None
if "score" not in st.session_state:
    st.session_state.score = None
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False
if "last_update" not in st.session_state:
    st.session_state.last_update = time.time()

# --- FONCTION POUR CHRONOMÈTRE DYNAMIQUE ---
def update_timer():
    if st.session_state.start_time and not st.session_state.quiz_submitted:
        current_time = time.time()
        # Mettre à jour seulement si 1 seconde s'est écoulée
        if current_time - st.session_state.last_update >= 1:
            st.session_state.last_update = current_time
            return True
    return False

# --- FONCTION PDF ---
def generate_pdf(name, score, responses, quiz):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, f"FEUILLE D'ÉVALUATION - QUIZ UAGN")
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 70, f"Nom du pilote: {name}")
    c.drawString(50, height - 85, f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    c.drawString(50, height - 100, f"Note finale: {score}/20")
    
    y = height - 130
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "DÉTAIL DES RÉPONSES:")
    y -= 20
    
    c.setFont("Helvetica", 10)
    for i, row in quiz.iterrows():
        question = row['Question']
        correct = str(row['Bonne réponse']).strip()
        user_answer = responses.get(i, "Non répondu")
        
        # Question
        c.drawString(50, y, f"Q{i+1}: {question}")
        y -= 15
        
        # Réponse utilisateur
        c.drawString(60, y, f"✓ Réponse du pilote: {user_answer}")
        y -= 15
        
        # Bonne réponse
        c.drawString(60, y, f"✓ Bonne réponse: {correct}")
        y -= 20
        
        # Vérification
        if str(user_answer).strip().lower() == correct.lower():
            c.setFillColorRGB(0, 0.5, 0)  # Vert
            c.drawString(60, y + 5, "✓ CORRECT")
        else:
            c.setFillColorRGB(0.8, 0, 0)  # Rouge
            c.drawString(60, y + 5, "✗ INCORRECT")
        
        c.setFillColorRGB(0, 0, 0)  # Retour au noir
        y -= 25
        
        if y < 100:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 10)
    
    c.save()
    buffer.seek(0)
    return buffer

# --- FONCTION POUR OBTENIR LES OPTIONS ---
def get_options(row):
    """Récupère les options disponibles d'une question"""
    options = []
    
    # Essayer différents formats de noms de colonnes
    possible_columns = ['A', 'B', 'C', 'D', 'Option A', 'Option B', 'Option C', 'Option D', 
                       'Réponse A', 'Réponse B', 'Réponse C', 'Réponse D']
    
    for col in possible_columns:
        if col in row and pd.notna(row[col]) and str(row[col]).strip() != "":
            options.append(str(row[col]).strip())
    
    # Si aucune option n'est trouvée avec les noms standards, essayer toutes les colonnes
    if not options:
        for col in row.index:
            if col not in ['Question', 'Bonne réponse', 'Bonne_reponse'] and pd.notna(row[col]) and str(row[col]).strip() != "":
                options.append(str(row[col]).strip())
    
    return options

# --- FONCTION POUR AFFICHER LE LOGO ---
def display_logo(image_path, width=100):
    try:
        # Encoder l'image en base64 pour l'affichage
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        st.markdown(
            f'<img src="data:image/png;base64,{encoded_string}" width="{width}">',
            unsafe_allow_html=True
        )
    except:
        st.write("📸 Logo")

# --- INTERFACE AVEC EN-TÊTE PERSONNALISÉE ---
st.set_page_config(page_title="Quiz NVG UAGN", layout="wide")

# En-tête personnalisé avec logos et titre
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
    display_logo("left_logo.png", 80)  # Remplacez par le chemin de votre logo gauche
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("""
        <div style='text-align: center;'>
            <h1 style='color: #007ACC; font-size: 2.5em; margin: 0;'>QUIZ UAGN</h1>
            <h3 style='color: #555; margin: 0;'>Test de Connaissances NVG</h3>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
    display_logo("right_logo.png", 80)  # Remplacez par le chemin de votre logo droit
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")

st.sidebar.success(f"Bienvenue {name} 👋")

role = "Admin" if username == "admin" else "Pilote"

if role == "Pilote":
    st.header("👨‍✈️ Espace Pilote")

    # Réinitialiser le quiz si nécessaire
    if st.button("🎬 Début du Test", key="start_quiz"):
        st.session_state.start_time = time.time()
        st.session_state.responses = {}
        st.session_state.quiz = df.sample(n=min(20, len(df))).reset_index(drop=True)
        st.session_state.score = None
        st.session_state.quiz_submitted = False
        st.session_state.last_update = time.time()
        st.rerun()

    # Gestion du chronomètre dynamique
    if st.session_state.start_time and st.session_state.quiz is not None:
        # Mettre à jour le timer
        update_timer()
        
        elapsed = time.time() - st.session_state.start_time
        remaining = max(0, 1800 - int(elapsed))  # 30 minutes = 1800 secondes
        minutes, seconds = divmod(remaining, 60)
        
        # Afficher le timer avec couleur selon le temps restant
        if remaining > 600:  # Plus de 10 minutes
            timer_color = "green"
        elif remaining > 300:  # Plus de 5 minutes
            timer_color = "orange"
        else:  # Moins de 5 minutes
            timer_color = "red"
            
        st.markdown(f"""
            <div style='text-align: center; padding: 10px; background-color: #f0f0f0; border-radius: 5px;'>
                <h2 style='color: {timer_color}; margin: 0;'>⏳ Temps restant: {minutes:02d}:{seconds:02d}</h2>
            </div>
        """, unsafe_allow_html=True)

        if remaining == 0 and not st.session_state.quiz_submitted:
            st.error("⛔ Temps écoulé ! Le test est terminé.")
            st.session_state.quiz_submitted = True

        if not st.session_state.quiz_submitted:
            # Afficher les questions
            for i, row in st.session_state.quiz.iterrows():
                st.markdown(f"**Q{i+1}:** {row['Question']}")
                
                options = get_options(row)

                if options:
                    # Créer une clé unique pour chaque question
                    response_key = f"q{i}_{int(st.session_state.start_time)}"
                    
                    # Utiliser un radio button pour la sélection
                    response = st.radio(
                        f"Choisissez votre réponse pour Q{i+1}:",
                        options,
                        key=response_key,
                        index=None
                    )
                    
                    if response:
                        st.session_state.responses[i] = response
                    else:
                        st.session_state.responses[i] = None
                        
                    st.markdown("---")
                else:
                    st.warning(f"⚠️ Aucune option disponible pour Q{i+1}")
                    st.info(f"Bonne réponse attendue: {row['Bonne réponse']}")
                    st.markdown("---")

            # Bouton de soumission
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("✅ Soumettre le Quiz", use_container_width=True):
                    # Calculer le score
                    score = 0
                    detailed_results = []
                    
                    for i, row in st.session_state.quiz.iterrows():
                        correct_answer = str(row['Bonne réponse']).strip().lower()
                        user_answer = st.session_state.responses.get(i)
                        
                        if user_answer and str(user_answer).strip().lower() == correct_answer:
                            score += 1
                            detailed_results.append(f"Q{i+1}: ✓ Correct")
                        else:
                            detailed_results.append(f"Q{i+1}: ✗ Incorrect (Votre réponse: {user_answer or 'Non répondu'} | Bonne réponse: {row['Bonne réponse']})")
                    
                    st.session_state.score = score
                    st.session_state.quiz_submitted = True
                    
                    # Afficher les résultats détaillés
                    st.success(f"🎯 Votre note finale: {score}/20")
                    
                    with st.expander("📊 Détail des résultats"):
                        for result in detailed_results:
                            st.write(result)

                    # Générer le PDF
                    pdf_file = generate_pdf(name, score, st.session_state.responses, st.session_state.quiz)
                    
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        st.download_button(
                            "📥 Télécharger la feuille d'évaluation",
                            data=pdf_file,
                            file_name=f"Evaluation_{name}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                            use_container_width=True
                        )

        elif st.session_state.quiz_submitted and st.session_state.score is not None:
            st.success(f"📋 Quiz terminé ! Votre note: {st.session_state.score}/20")
            
            if st.button("🔄 Recommencer le test"):
                st.session_state.start_time = None
                st.session_state.quiz_submitted = False
                st.session_state.score = None
                st.rerun()

elif role == "Admin":
    st.header("🛠️ Espace Admin")
    
    # Aperçu des données
    st.subheader("📊 Aperçu des données")
    if not df.empty:
        st.dataframe(df)
        st.write(f"Nombre total de questions: {len(df)}")
    else:
        st.warning("Aucune question trouvée dans la base de données.")

    st.subheader("📌 Ajouter une nouvelle question")
    with st.form("add_question_form"):
        new_question = st.text_area("Question", placeholder="Entrez la question ici...")
        col1, col2 = st.columns(2)
        with col1:
            new_A = st.text_input("Option A", placeholder="Réponse A")
            new_B = st.text_input("Option B", placeholder="Réponse B")
        with col2:
            new_C = st.text_input("Option C", placeholder="Réponse C")
            new_D = st.text_input("Option D", placeholder="Réponse D")
        new_correct = st.text_input("Bonne réponse", placeholder="La réponse correcte (doit correspondre exactement à l'une des options)")

        if st.form_submit_button("➕ Ajouter la question"):
            if new_question and new_correct:
                new_row = {
                    "Question": new_question,
                    "A": new_A,
                    "B": new_B,
                    "C": new_C,
                    "D": new_D,
                    "Bonne réponse": new_correct
                }
                # Recharger les données actuelles
                current_df = pd.read_excel("NVG_TEST.xlsx")
                updated_df = pd.concat([current_df, pd.DataFrame([new_row])], ignore_index=True)
                updated_df.to_excel("NVG_TEST.xlsx", index=False)
                st.success("✅ Question ajoutée avec succès.")
                st.cache_data.clear()
                st.rerun()
            else:
                st.error("❌ Veuillez remplir au moins la question et la bonne réponse.")

    st.subheader("✏️ Modifier une question existante")
    if not df.empty:
        question_index = st.selectbox(
            "Sélectionnez la question à modifier",
            range(len(df)),
            format_func=lambda x: f"Q{x+1}: {df.iloc[x]['Question'][:50]}..."
        )
        
        if question_index < len(df):
            with st.form("edit_question_form"):
                st.write(f"**Question actuelle:** {df.iloc[question_index]['Question']}")
                
                updated_question = st.text_area("Nouvelle question", value=df.iloc[question_index]['Question'])
                
                col1, col2 = st.columns(2)
                with col1:
                    updated_A = st.text_input("Option A", value=df.iloc[question_index].get('A', ''))
                    updated_B = st.text_input("Option B", value=df.iloc[question_index].get('B', ''))
                with col2:
                    updated_C = st.text_input("Option C", value=df.iloc[question_index].get('C', ''))
                    updated_D = st.text_input("Option D", value=df.iloc[question_index].get('D', ''))
                
                updated_correct = st.text_input("Bonne réponse", value=df.iloc[question_index]['Bonne réponse'])

                if st.form_submit_button("💾 Sauvegarder les modifications"):
                    df.at[question_index, "Question"] = updated_question
                    df.at[question_index, "A"] = updated_A
                    df.at[question_index, "B"] = updated_B
                    df.at[question_index, "C"] = updated_C
                    df.at[question_index, "D"] = updated_D
                    df.at[question_index, "Bonne réponse"] = updated_correct
                    df.to_excel("NVG_TEST.xlsx", index=False)
                    st.success("✅ Question modifiée avec succès.")
                    st.cache_data.clear()
                    st.rerun()

# Pied de page
st.markdown("---")
st.markdown("<div style='text-align: center; color: #666;'>Quiz UAGN - Système d'évaluation NVG © 2024</div>", unsafe_allow_html=True)

